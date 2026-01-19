from langfuse import Langfuse
from src.config import Settings
import logging
from typing import Optional
from typing import Any, Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class LangfuseTracer:

    def __init__(self, settings: Settings):
        self.settings = settings.langfuse
        self.client: Optional[Langfuse] = None
        if self.settings.enabled and self.settings.public_key and self.settings.secret_key:
            try:
                self.client = Langfuse(
                    public_key=self.settings.public_key,
                    secret_key=self.settings.secret_key,
                    host=self.settings.host,
                    flush_at=self.settings.flush_at,
                    flush_interval=self.settings.flush_interval,
                    debug=self.settings.debug
                )
                logger.info(f"Langfuse v3 tracing initialized (host: {self.settings.host})")
            except Exception as e:
                logger.error(f"Failed to initialize Langfuse v3 tracing: {e}")
                self.client = None
        else:
            logger.warning("Langfuse v3 tracing is disabled")


    @contextmanager
    def trace_rag_request(self, query: str, user_id: str, session_id: str, metadata: Optional[Dict] = None):
        if not self.client:
            yield None
            return

        trace = self.client.trace(
            name="rag_request",
            user_id=user_id,
            session_id=session_id,
            input={"query": query},
            metadata=metadata
        )
        try:
            yield trace
        except Exception as e:
            trace.update(level="ERROR", status_message=str(e))
            raise e
        finally:
            # Trace ending is handled by individual spans or implicitly, 
            # but we can ensure flushing happens in RAGTracer.
            pass

    def create_span(self, trace, name: str, input_data: Optional[Dict] = None):
        if not trace:
            return None
        return trace.span(name=name, input=input_data)

    def end_generation(self, span, answer: str, model: str):
        if not span:
            return
        
        self.update_span(
            span=span,
            output={"answer": answer},
            metadata={"model": model},
            status_message="success"
        )


    def update_span(
        self, 
        span, 
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: Optional[str] = None,
        status_message: Optional[str] = None
    ):
        if not span:
            return
        try:
            update_data = {}
            if output is not None:
                update_data["output"] = output
            if metadata:
                update_data["metadata"] = metadata
            if level:
                update_data["level"] = level
            if status_message:
                update_data["status_message"] = status_message

            if update_data:
                span.update(**update_data)
            span.end()
        except Exception as e:
            logger.error(f"Error updating span: {e}")


    def flush(self):
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.warning(f"Failed to flush Langfuse client: {e}")