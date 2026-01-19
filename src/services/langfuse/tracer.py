import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from .client import LangfuseTracer


class RAGTracer:
    def __init__(self, tracer: LangfuseTracer):
        self.tracer = tracer


    @contextmanager
    def trace_request(self, user_id: str, query: str):
        trace = None
        try:
            with self.tracer.trace_rag_request(
                query=query, user_id=user_id, session_id=f"session_{user_id}", metadata={"simplified_tracing": True}
            ) as trace:
                yield trace
        finally:
            if trace:
                self.tracer.flush()

    @contextmanager
    def trace_embedding(self, trace, query: str):
        start_time = time.time()
        span = self.tracer.create_span(
            trace=trace, name='query_embedding', input_data={"query": query, "query_length": len(query)}
        )
        try:
            yield span
        finally:
            duration = time.time() - start_time
            if span:
                self.tracer.update_span(span=span, output={"embedding_duration_ms": round(duration*1000, 2), "success": True})

    @contextmanager
    def trace_search(self, trace, query: str, top_k: int):
        span = self.tracer.create_span(
            trace=trace,
            name="search_retrieval",
            input_data={"query": query, "top_k": top_k}
        )
        try:
            yield span
        finally:
            if span:
                span.end()
        

    @contextmanager
    def trace_prompt_construction(self, trace, chunks: List[Dict]):
        span = self.tracer.create_span(
            trace=trace,
            name="prompt_construction",
            input_data={"chunks_count": len(chunks)}
        )
        try:
            yield span
        finally:
            if span:
                span.end()

    @contextmanager
    def trace_generation(self, trace, model: str, prompt: str):
        span = self.tracer.create_span(
            trace=trace, name='llm_generation', input_data={"model": model, "prompt_length": len(prompt), "prompt": prompt}
        )
        try:
            yield span
        finally:
            if span:
                span.end()


    def end_request(self, trace, answer: str, duration: float):
        """End main request trace."""
        if not trace:
            return

        try:
            trace.update(
                output={"answer": answer, "total_duration_seconds": round(duration, 3), "response_length": len(answer)}
            )
        except Exception:
            # Silently fail - don't break the request for tracing issues
            pass


    @contextmanager
    def end_search(self, span, chunks: List[Dict], arxiv_ids: List[str], total: int):
        if not span:
            return
        self.tracer.update_span(
            span=span,
            output={
                'chunks_returned': len(chunks),
                'arxiv_ids': arxiv_ids,
                'total_hits': total,
                'success': True
            }
        )



    @contextmanager
    def end_prompt(self, span, prompt: str):
        if not span:
            return
        self.tracer.update_span(span=span, output={"final_prompt": prompt, "prompt_length": len(prompt)})

    @contextmanager
    def end_generation(self, span, answer: str, model: str):
        self.tracer.end_generation(span, answer, model)