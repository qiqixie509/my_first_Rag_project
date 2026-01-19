from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError
import json
import logging
from src.schemas.ollama import RAGResponse
from typing import Optional, List, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)

class RAGPromptBuilder:

    def __init__(self):
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        prompt_file = self.prompts_dir / "system_prompt.txt"
        if not prompt_file.exists():
            return (
                "You are an AI assistant specialized in answering questions about "
                "acdemic papers from arXiv. Base your answer STRICTLY on the provided "
                "paper excerpts."
            )
        return prompt_file.read_text().strip()


    def create_rag_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        prompt = f"{self.system_prompt}\n\n"
        prompt += "### Context from Papers:\n\n"
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get("chunk_text", chunk.get("content", ""))
            arxiv_id = chunk.get("arxiv_id")
            prompt += f"[Document {i+1}. arXiv: {arxiv_id}]\n"
            prompt += f"{chunk_text}\n\n"

        prompt += f"### Question:\n{query}\n\n"
        prompt += (
            "### Answer:\nProvide a natural, conversational response (not JSON) and cite sources using [arXiv:id] format.\n\n"
        )
        return prompt


    def create_structured_prompt(self, query: str, chunks: List[Dict]) -> Dict[str, Any]:
        prompt_text = self.create_rag_prompt(query, chunks)
        return {
            "prompt": prompt_text,
            "format": RAGResponse.model_json_schema()
        }


class ResponseParser:
    @staticmethod
    def parse_structured_response(response: str) -> Optional[Dict[str, Any]]:
        try:
            parsed_json = json.loads(response)
            validated_response = RAGResponse(**parsed_json)
            return validated_response.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse structured response: {e}")
            return None
   