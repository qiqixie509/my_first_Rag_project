from src.config import get_settings
from src.services.langfuse.client import LangfuseTracer
from functools import lru_cache

@lru_cache(maxsize=1)
def make_langfuse_tracer() -> LangfuseTracer:
    settings = get_settings()
    return LangfuseTracer(settings)