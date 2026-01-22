from src.config import Settings
import httpx
import logging
import json
from typing import Optional, Any, Dict, List
from src.exceptions import OllamaException, OllamaConnectionException, OllamaTimeoutError
from src.services.ollama.prompts import RAGPromptBuilder, ResponseParser
from src.services.langfuse.client import LangfuseTracer


logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_host
        self.timeout = httpx.Timeout(float(settings.ollama_timeout))
        self.prompt_builder = RAGPromptBuilder()
        self.response_parser = ResponseParser()


    def get_langchain_model(
        self,
        model: str = "llama3.2",
        temperature: float = 0.0,
        **kwargs: Any
    ):
        """Get a LangChain-compatible Ollama model instance."""
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model,
                base_url=self.base_url,
                temperature=temperature,
                **kwargs
            )
        except ImportError:
            logger.error("langchain-ollama package not found. Please install it.")
            raise OllamaException("langchain-ollama package not found")


    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                data = {"model": model, "prompt": prompt, "stream": stream, **kwargs}
                logger.info(f"Sending request to Ollama: model={model}, stream={stream}, extra_params={kwargs}")
                response = await client.post(f"{self.base_url}/api/generate", json=data)

                if response.status_code == 200:
                    result = response.json()

                    usage_metadata = {}
                    if "prompt_eval_count" in result:
                        usage_metadata["prompt_tokens"] = result.get("prompt_eval_count", 0)
                    if "eval_count" in result:
                        usage_metadata["completion_tokens"] = result.get("eval_count", 0)

                    if usage_metadata:
                        usage_metadata["total_tokens"] = (
                            usage_metadata.get("prompt_tokens", 0) + 
                            usage_metadata.get("completion_tokens", 0)
                        )

                    if "total_duration" in result:
                        usage_metadata["latency_ms"] = round(result["total_duration"] / 1_000_000, 2)
                        usage_metadata["total_duration"] = result.get("total_duration", 0)
                    
                    if "prompt_eval_duration" in result:
                        usage_metadata["prompt_eval_duration_ms"] = round(result["prompt_eval_duration"] / 1_000_000, 2)
                    
                    if "eval_duration" in result:
                        usage_metadata["eval_duration_ms"] = round(result["eval_duration"] / 1_000_000, 2)

                    result["usage_metadata"] = usage_metadata

                    logger.debug(f"Usage metadata: {usage_metadata}")
                    return result
                else:
                    raise OllamaException(f"Failed to generate response from Ollama: {response.status_code}")

        except httpx.ConnectError as e:
            raise OllamaConnectionException(f"Cannot connect to Ollama service: {e}")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(f"Ollama service timeout: {e}")
        except OllamaException:
            raise
        except Exception as e:
            raise OllamaException(f"Unexpected error from Ollama: {e}")


    async def generate_rag_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        model: str = "llama3.2",
        use_structured_output: bool = False
    ) -> Dict[str, Any]:
        try:
            if use_structured_output:
                prompt_data = self.prompt_builder.create_structured_prompt(query, chunks)
                
                response = await self.generate(
                    model=model,
                    prompt = prompt_data["prompt"],
                    temperature = 0.7,
                    top_p = 0.9,
                    format = prompt_data["format"]
                )
            else:
                prmopt = self.prompt_builder.create_rag_prompt(query, chunks)
                response = await self.generate(
                    model=model,
                    prompt = prmopt,
                    temperature = 0.7,
                    top_p = 0.9
                )
            if response and "response" in response:
                answer_text = response['response']
                logger.debug(f"Raw LLM response: {answer_text[:500]}")
                if use_structured_output:
                    parsed_response = self.response_parser.parse_structured_response(answer_text)
                    logger.debug(f"Parsed response: {parsed_response}")
                    return parsed_response
                else:
                    sources = []
                    seen_urls=set()
                    for chunk in chunks:
                        arxiv_id = chunk.get("arxiv_id")
                        if arxiv_id:
                            arxiv_id_clean = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
                            pdf_url = f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf"
                            if pdf_url not in seen_urls:
                                sources.append(pdf_url)
                                seen_urls.add(pdf_url)
                    citations = list(set(chunk.get("arxiv_id") for chunk in chunks if chunk.get("arxiv_id")))

                    return {
                        "answer": answer_text,
                        "sources": sources,
                        "confidence": "medium",
                        "citations": citations
                    }
            else:
                raise OllamaException("No response generated from Ollama")

        except Exception as e:
            raise OllamaException(f"Unexpected error from Ollama: {e}")


    async def generate_stream(
        self,
        model: str,
        prompt: str,
        **kwargs: Dict[str, Any]
    ):
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                data = {"model": model, "prompt": prompt, "stream": True, **kwargs}
                
                async with client.stream("POST", f"{self.base_url}/api/generate", json=data) as response:
                    if response.status_code != 200:
                        raise OllamaException(f"Ollama API error: {response.status_code}")
                        
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            json_response = json.loads(line)
                            yield json_response
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse stream line: {line}")
                            continue

        except httpx.ConnectError as e:
            raise OllamaConnectionException(f"Cannot connect to Ollama service: {e}")
        except Exception as e:
            raise OllamaException(f"Streaming error: {e}")


    async def generate_rag_answer_stream(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        model: str = "llama3.2"
    ):
        try:
            prompt = self.prompt_builder.create_rag_prompt(query, chunks)
            
            async for chunk in self.generate_stream(
                model=model,
                prompt=prompt,
                temperature=0.7,
                top_p=0.9
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Error generating streaming RAG answer: {e}")
            raise OllamaException(f"Unexpected error from Ollama: {e}")