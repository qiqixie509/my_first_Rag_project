from src.services.agents.config import GraphConfig
from src.services.opensearch.client import OpenSearchClient
from src.services.ollama.client import OllamaClient
from src.services.embedding.jina_client import JinaEmbeddingClient
from src.services.langfuse.client import LangfuseTracer
import logging
import time
from .state import AgentState
from typing import Optional
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from .tools import create_retriever_tool
from .nodes import (
    ainvoke_guardrail_step,
    ainvoke_out_of_scope_step,
    ainvoke_retrieve_step,
    ainvoke_grade_documents_step,
    ainvoke_rewrite_query_step,
    ainvoke_generate_answer_step,
    continue_after_guardrail,
)
from .state import AgentState
from typing import Optional, List, Dict, Any
from .context import Context



logger = logging.getLogger(__name__)

class AgenticRAGService:
    def __init__(
        self,
        opensearch_client: OpenSearchClient,
        ollama_client: OllamaClient,
        embeddings_client: JinaEmbeddingClient,
        langfuse_tracer: Optional[LangfuseTracer] = None,
        graph_config: Optional[GraphConfig] = None,
    ):
        self.opensearch_client = opensearch_client
        self.ollama_client = ollama_client
        self.embeddings_client = embeddings_client
        self.langfuse_tracer = langfuse_tracer
        self.graph_config = graph_config or GraphConfig()

        logger.info("Initializing AgenticRAGService with configuration:")
        logger.info(f"  Model: {self.graph_config.model}")
        logger.info(f"  Top-k: {self.graph_config.top_k}")
        logger.info(f"  Hybrid search: {self.graph_config.use_hybrid}")
        logger.info(f"  Max retrieval attempts: {self.graph_config.max_retrieval_attempts}")
        logger.info(f"  Guardrail threshold: {self.graph_config.guardrail_threshold}")

        # Build graph once (no runnables needed!)
        self.graph = self._build_graph()
        logger.info("✓ AgenticRAGService initialized successfully")


    def _build_graph(self):
        logger.info("Building LangGraph workflow with context_schema")
        workflow = StateGraph(AgentState, context_schema=Context)
        retrieval_tool = create_retriever_tool(
            opensearch_client=self.opensearch_client,
            embeddings_client=self.embeddings_client,
            top_k=self.graph_config.top_k,
            use_hybrid=self.graph_config.use_hybrid,
        )
        tools = [retrieval_tool]

        logger.info("Adding nodes to workflow graph")
        workflow.add_node("guardrail", ainvoke_guardrail_step)
        workflow.add_node("out_of_scope", ainvoke_out_of_scope_step)
        workflow.add_node("retrieve", ainvoke_retrieve_step)
        workflow.add_node("tool_retrieve", ToolNode(tools))
        workflow.add_node("grade_documents", ainvoke_grade_documents_step)
        workflow.add_node("rewrite_query", ainvoke_rewrite_query_step)
        workflow.add_node("generate_answer", ainvoke_generate_answer_step)

        logger.info("Configuring graph edges and routing logic")

        workflow.add_edge(START, "guardrail")

        workflow.add_conditional_edges(
            "guardrail",
            continue_after_guardrail,
            {
                "continue": "retrieve",
                "out_of_scope": "out_of_scope"
            },
        )

        workflow.add_edge("out_of_scope", END)

        workflow.add_conditional_edges(
            "retrieve",
            tools_condition,
            {
                "tools": "tool_retrieve",
                END: END
            }
        )

        workflow.add_edge("tool_retrieve", "grade_documents")

        workflow.add_conditional_edges(
            "grade_documents",
            lambda state: state.get("routing_decision", "generate_answer"),
            {
                "generate_answer": "generate_answer",
                "rewrite_query": "rewrite_query"
            },
        )

        workflow.add_edge("rewrite_query", "retrieve")

        workflow.add_edge("generate_answer", END)

        logger.info("Compiling LangGraph workflow")
        compiled_graph = workflow.compile()
        logger.info("✓ Graph compilation successful")

        return compiled_graph


    def _extract_answer(self, result: dict) -> str:
        messages = result.get("messages", [])
        if not messages:
            return "No answer generated"
        final_message = messages[-1]
        return final_message["content"] if "content" in final_message else str(final_message)


    def _extract_sources(self, result: dict) -> list:
        sources = []
        relevant_sources = result.get("relevant_sources", [])

        for source in relevant_sources:
            if hasattr(source, 'to_dict'):
                sources.append(source.to_dict())
            elif isinstance(source, dict):
                sources.append(source)
            else:
                sources.append(str(source))
        
        # If we didn't find specific relevant_sources, fall back to the generic sources field
        if not sources:
            sources_from_state = result.get("sources")
            return sources_from_state if isinstance(sources_from_state, list) else []
        return sources


    def _extract_reasoning_steps(self, result: dict) -> list:
        steps = []
        retrieval_attempts = result.get("retrieval_attempts", 0)
        guardrail_result = result.get("guardrail_result")
        grading_results = result.get("grading_results", [])

        if guardrail_result:
            score = getattr(guardrail_result, 'score', 'N/A')
            steps.append(f"Validated query scope (score: {score}/100)")

        if retrieval_attempts > 0:
            steps.append(f"Retrieved documents ({retrieval_attempts} attempts)")

        if grading_results:
            relevant_count = sum(1 for g in grading_results if g.is_relevant)
            steps.append(f"Graded documents ({relevant_count} relevant)")

        if result.get("rewritten_query"):
            steps.append("Rewritten query for better results")

        steps.append("Generated answer from context")

        return steps


    async def _run_workflow(
        self,
        query: str,
        model_to_use: str,
        user_id: str,
        trace: Optional = None,
    ) -> dict:
        try:
            start_time = time.time()
            logger.info("Invoking LangGraph workflow")

            state_input = {
                "messages": [HumanMessage(content=query)],
                "retrieval_attempts": 0,
                "guardrail_result": None,
                "routing_decision": None,
                "sources": None,
                "relevant_sources": [],
                "relevant_tool_artefacts": None,
                "grading_results": [],
                "metadata": {},
                "original_query": None,
                "rewritten_query": None,
            }

            runtime_context = Context(
                ollama_client=self.ollama_client,
                opensearch_client=self.opensearch_client,
                embeddings_client=self.embeddings_client,
                langfuse_tracer=self.langfuse_tracer,
                trace=trace,
                langfuse_enabled=self.langfuse_tracer is not None and self.langfuse_tracer.client is not None,
                model_name=model_to_use,
                temperature=self.graph_config.temperature,
                top_k=self.graph_config.top_k,
                max_retrieval_attempts=self.graph_config.max_retrieval_attempts,
                guardrail_threshold=self.graph_config.guardrail_threshold,
            )
            config = {
                "thread_id": f"use_{user_id}_session_{int(time.time())}"
            }

            if self.langfuse_tracer and trace:
                try:
                    callback_handler = CallbackHandler()
                    config['callbacks'] = [callback_handler]
                    logger.info("✓ Langfuse callback handler added to runtime context")
                except Exception as e:
                    logger.warning(f"Error adding Langfuse callback handler: {str(e)}")

            result = await self.graph.ainvoke(
                state_input,
                config=config,
                context=runtime_context,
            )

            execution_time=time.time()-start_time
            logger.info(f"Graph execution completed in {execution_time:.2f} seconds")

            answer = self._extract_answer(result)
            sources = self._extract_sources(result)
            retrieval_attempts = result.get("retrieval_attempts", 0)
            reasoning_steps = self._extract_reasoning_steps(result)

            if trace:
                trace.update(
                    output={
                        "answer": answer,
                        "sources_count": len(sources),
                        "retrieval_attempts": retrieval_attempts,
                        "reasoning_steps": reasoning_steps,
                        "execution_time": execution_time,
                    }
                )
                trace.end()
                self.langfuse_tracer.flush()

            logger.info("=" * 80)
            logger.info("Agentic RAG Request Completed")
            logger.info(f"Answer: {answer}")
            logger.info(f"Sources: {sources}")
            logger.info(f"Retrieval Attempts: {retrieval_attempts}")
            logger.info(f"Reasoning Steps: {reasoning_steps}")
            logger.info(f"Execution Time: {execution_time:.2f} seconds")
            logger.info("=" * 80)

            guardrail_result = result.get("guardrail_result")
            return {
                "query": query,
                "answer": answer,
                "sources": sources,
                "retrieval_attempts": retrieval_attempts,
                "reasoning_steps": reasoning_steps,
                "execution_time": execution_time,
                "guardrail_score": guardrail_result.score if guardrail_result else None,
            }
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            logger.exception("Full traceback:")

            # Update trace with error (cleanup handled by context manager)
            if trace:
                trace.update(output={"error": str(e)}, level="ERROR")
                trace.end()
                self.langfuse_tracer.flush()

            raise


    async def ask(
        self,
        query: str,
        user_id: str = "api_user",
        model: Optional[str] = None,
    ) -> dict:
        model_to_use = model or self.graph_config.model

        logger.info("=" * 80)
        logger.info("Starting Agentic RAG Request")
        logger.info(f"Query: {query}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Model: {model_to_use}")
        logger.info("=" * 80)

        if not query or len(query.strip()) == 0:
            logger.error("Empty query received")
            raise ValueError("Query cannot be empty")

        trace = None
        if self.langfuse_tracer and self.langfuse_tracer.client:
            logger.info("Creating Langfuse trace (v3 SDK)")
            metadata = {
                "env": self.graph_config.settings.environment,
                "service": "agentic_rag",
                "top_k": self.graph_config.top_k,
                "use_hybrid": self.graph_config.use_hybrid,
                "model": model_to_use,
            }
            trace = self.langfuse_tracer.client.start_as_current_span(
                name="agentic_rag_request",
            )

        async def _execute_with_trace():
            if trace is not None:
                with trace as trace_obj:
                    trace_obj.update(
                        input={'query': query},
                        metadata=metadata,
                        user_id=user_id,
                        session_id=f"session_{user_id}"
                    )
                    logger.debug(f"Trace created: {trace_obj}")
                    return await self._run_workflow(query, model_to_use, user_id, trace_obj)
            else:
                return await self._run_workflow(query, model_to_use, user_id)
        
        try:
            return await _execute_with_trace()
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            logger.exception("Full traceback:")
            raise
        
    