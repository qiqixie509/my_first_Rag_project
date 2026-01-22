# Embedding Service

The Embedding Service is responsible for converting human language (text) into high-dimensional numerical vectors (embeddings). We use the **Jina AI (jina-embeddings-v3)** model to handle this transformation.

## Why do we need Embeddings?

Computers cannot "read" text the way humans do. To perform complex operations like finding similar documents, we must convert words into a language of numbers (vectors) where "distance" represents semantic similarity.

### 1. Value for OpenSearch (Hybrid Search)
Traditional search engines (BM25) look for exact word matches. If a user searches for "deep learning" but a paper uses the term "neural networks," keyword search might miss it.
- **Semantic Understanding**: Embeddings allow OpenSearch to understand that "deep learning" and "neural networks" are conceptually related.
- **Hybrid Performance**: By combining keyword scores with vector similarity scores (via the RRF pipeline), we get the precision of keyword search and the "intelligence" of semantic search.

### 2. Value for Ollama (RAG Context)
Local LLMs like Ollama have a limited "context window"—they can only read a certain amount of text at once. We cannot feed 10,000 research papers into the model.
- **Precision Retrieval**: Embeddings act as a filter. They help us find the exact 3 or 4 most relevant chunks of text from our entire database.
- **Context Relevance**: This ensures that Ollama only receives the most pertinent information, improving answer accuracy and reducing hallucinations.

## Components

### `JinaEmbeddingClient`
A client that interfaces with the Jina AI API. It handles:
- **Query Embedding**: Optimized for short, search-style strings (`task="retrieval.query"`).
- **Passage Embedding**: Optimized for longer document chunks (`task="retrieval.passage"`).
- **Batching**: Efficiently processes multiple text chunks in a single API call to minimize latency.

### `make_embeddings_client`
A factory function in `factory.py` that initializes the client using the `jina_api_key` from the application's global configuration.