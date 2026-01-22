from fastapi import APIRouter, HTTPException
from src.dependencies import AgenticRAGDep
from src.services.langfuse.tracer import RAGTracer
from src.services.ollama.prompts import RAGPromptBuilder
from src.schemas.api.ask import AgenticAskRequest, AgenticAskResponse, FeedbackRequest, FeedbackResponse

router = APIRouter(tags=["agentic-ask"])

@router.post("/ask-agentic", response_model=AgenticAskResponse)
async def ask_agentic(
    request: AgenticAskRequest,
    agentic_rag: AgenticRAGDep
) -> AgenticAskResponse:
    try:
        result = await agentic_rag.ask(
            query = request.query,
        )
        return AgenticAskResponse(
            query = result['query'],
            answer = result['answer'],
            sources = result.get('sources', []),
            chunks_used = request.top_k,
            search_mode = "hybrid" if request.use_hybrid else "bm25",
            reasoning_steps = result.get('reasoning_steps', []),
            retrieval_attempts = result.get('retrieval_attempts', 0),
            trace_id = result.get('trace_id')   
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")