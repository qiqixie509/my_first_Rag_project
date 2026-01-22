# Ollama Service

[Ollama](https://ollama.com/) is an open-source framework designed for running large language models (LLMs) locally on your machine. It simplifies the process of downloading, managing, and serving models like Llama 3, Mistral, and others through a local API.

In this project, we use the **`llama3.2:latest`** model (specifically the 3B parameter version) for its excellent balance of performance and efficiency when running on consumer hardware.

The Ollama Service provides the interface for local LLM inference, primarily used for generating answers based on retrieved research papers.

## Features

- **Text Generation**: Provides asynchronous methods for standard text generation and RAG-specific answer generation.
- **Streaming Support**: Supports real-time streaming of model responses for a more interactive user experience.
- **Structured Output**: Can generate and parse JSON-formatted responses using Pydantic schemas for precise data extraction.
- **Prompt Management**: Includes a dedicated `RAGPromptBuilder` to construct consistent system and user prompts with cited context.
- **LangChain Integration**: Built-in support for generating LangChain-compatible model instances (`ChatOllama`) for use in complex agentic workflows.

## Components

### `OllamaClient`
The main service class that handles communication with the local Ollama server. It leverages `httpx` for async API calls and manages model configuration.

### `RAGPromptBuilder`
A utility class that constructs prompts specifically for the RAG pipeline. It handles:
- **System Prompts**: Loads specialized system instructions.
- **Context Injection**: Formats retrieved paper snippets with proper arXiv citations.
- **Structured Schema**: Prepares the format instructions for JSON mode.

### `ResponseParser`
Ensures that structured (JSON) responses from the model are valid and correctly formatted against the expected schemas.

### `make_ollama_client`
A factory function in `factory.py` that simplifies client initialization with application-wide settings and implements caching to maintain a single client instance.


## Configuration

Settings are controlled via `src/config.py`:
- `ollama_host`: The base URL of the local Ollama server (prefix `http://`).
- `ollama_model`: The default model name to use (e.g., `llama3.2`).
- `ollama_timeout`: Request timeout in seconds.
