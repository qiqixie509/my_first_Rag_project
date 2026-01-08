from services.arxiv.arxiv_client import ArxivClient
from config import get_settings

def make_arxiv_client() -> ArxivClient:
    settings = get_settings()
    client = ArxivClient(settings=settings.arxiv)
    return client
