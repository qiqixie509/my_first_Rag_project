import logging
from typing import Dict, List, Union
import time

from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from ..context import Context
from ..state import AgentState
from .utils import get_latest_query

logger = logging.getLogger(__name__)

async def ainvoke_retrieve_step(
    state: AgentState,
    runtime: Runtime[Context]
) -> Dict[str, Union[int, str, list]]:
    logger.info("NODE: retrieve")
    start_time = time.time()

    messages = state["messages"]
    question = get_latest_query(messages)
    current_attempts = state.get("retrieval_attempts", 0)

    max_attempts = runtime.context.max_retrieval_attempts

    updates = {}
    if state.get("original_query") is None:
        updates["original_query"] = question
        logger.debug(f"Stored original query: {question[:100]}...")

    span = None
    if runtime.context.langfuse_enabled and runtime.context.trace:
        try:
            span = runtime.context.langfuse_tracer.create_span(
                trace=runtime.context.trace,
                name="document_retrieval_initation",
                input_data={
                    "query": question,
                    "attempt": current_attempts + 1,
                    "max_attempts": max_attempts,
                },
                metadata={
                    "node": "retrieve",
                    "model": runtime.context.model_name,
                },
            )
            logger.debug(f"Created Langfuse span for retrieval attempt {current_attempts + 1}")
        except Exception as e:
            logger.warning(f"Error creating Langfuse span: {str(e)}")


    if current_attempts >= max_attempts:
        logger.warning(f"Max retrieval attempts ({max_attempts}) reached")
        fallback_msg = (
            f"I apologize, but I couldn't find relevant research papers after {max_attempts} attempts.\n"
            "This may be because:\n"
            "1. No papers in the database contain relevant information\n"
            "2. The query terms don't match the indexed content\n\n"
            "Please try rephrasing your question with more specific technical terms."
        )

        if span:
            execution_time = (time.time() - start_time) * 1000
            runtime.context.langfuse_tracer.end_span(
                span,
                output={"status": "max_attempts_reached", "fallback": True},
                metadata={"execution_time_ms": execution_time},
            )
        
        return {**updates, "messages": [AIMessage(content=fallback_msg)]}
    
    new_attempt_count = current_attempts + 1
    updates["retrieval_attempts"] = new_attempt_count
    logger.info(f"Retrieval attempt {new_attempt_count}/{max_attempts}")

    updates["messages"] = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": f"retrieve_{new_attempt_count}",
                    "name": "retrieve_paper",
                    "args": {"query": question}
                }
            ]
        )
    ]

    logger.debug(f"Retrieval attempt {new_attempt_count}/{max_attempts}")

    # Update span with successful tool call creation
    if span:
        execution_time = (time.time() - start_time) * 1000
        runtime.context.langfuse_tracer.update_span(
            span,
            output={
                "status": "tool_call_created",
                "query": question,
                "attempt": new_attempt_count
            },
            metadata={"execution_time_ms": execution_time},
        )
    return updates