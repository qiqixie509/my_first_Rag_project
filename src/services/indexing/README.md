# Indexing and Hybrid Search Service

The Indexing Service is responsible for processing parsed research papers into searchable chunks and creating a robust hybrid search index.

## Features

- **Semantic Chunking**: Breaks down full-text papers into manageable, context-aware chunks using the `TextChunker`.
- **Hybrid Indexing**: Combines traditional keyword-based (BM25) indexing with modern vector-based (Embedding) indexing.
- **Batch Processing**: Supports efficient indexing of multiple papers in batches with automatic progress tracking.
- **RRF (Reciprocal Rank Fusion)**: A state-of-the-art ranking algorithm used to combine results from multiple search methods.

## Hybrid Search & RRF Pipeline

Our system employs a **Native Hybrid Search** strategy to provide the most relevant results:

1.  **BM25 Search**: Captures keyword matches and technical terminology.
2.  **Vector Search**: Captures semantic meaning and conceptual relevance using Jina AI embeddings.
3.  **RRF Fusion**: The results from both searches are merged using a **Reciprocal Rank Fusion (RRF)** pipeline. 
    - The RRF algorithm scores documents based on their rank in each individual search result list.
    - Documents that appear near the top of *any* list (or high enough in *multiple* lists) are prioritized.
    - This approach provides a more balanced and accurate ranking than simple score-based merging.

### Implementation Details

- **OpenSearch Integration**: We use a custom OpenSearch `search_pipeline` configured with a `phase_results_processor` of type `rerank`.
- **Automatic Setup**: The `OpenSearchClient` automatically sets up the required index mappings and RRF pipelines during initialization.

## Components

### `HybridIndexingService`
The primary entry point for indexing papers. It orchestrates the chunking, embedding, and bulk-indexing process.

### `TextChunker`
A specialized utility that splits documents while maintaining metadata (section titles, page IDs, etc.) to provide better context for the LLM.

### `HybridIndexerFactory`
Initializes the service with the necessary client dependencies (Embedding, OpenSearch, etc.).

