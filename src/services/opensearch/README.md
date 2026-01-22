# OpenSearch Service

The OpenSearch Service is the heart of the system's retrieval capabilities. It manages the underlying cluster connection, index configurations, and the execution of complex search queries.

## Features

- **Index Management**: Automated creation and configuration of hybrid indexes with specific mappings for both technical text and high-dimensional vectors.
- **Query Building**: A dedicated `QueryBuilder` that constructs sophisticated OpenSearch DSL queries for keyword search, k-NN vector search, and hybrid combinations.
- **Search Pipelines**: Implementation of server-side search pipelines, including the RRF (Reciprocal Rank Fusion) pipeline for merging disparate search results.
- **Bulk Operations**: Efficient bulk indexing of paper chunks to handle large datasets.
- **Hybrid Search**: Native support for switching between BM25 (keyword) and hybrid (keyword + vector) search modes.

## Relationship with Indexing

The OpenSearch service and the **Indexing Service** work in tandem to enable search functionality:

- **OpenSearch Service (The Store & Searcher)**: It defines the *structure* (mappings) and provides the *mechanics* for searching. It is passive until called upon to store or retrieve data.
- **Indexing Service (The Producer)**: It is the active pipeline that *processes* raw research papers. It takes a paper, chunks it, embeds those chunks, and then uses the `OpenSearchClient` as a tool to save those results into the designated index.

In short: **Indexing** prepares the data; **OpenSearch** hosts and queries it.

## Components

### `OpenSearchClient`
The primary interface for all interactions with the OpenSearch cluster. It handles connection pooling, index setup, and search execution.

### `index_config_hybrid.py` (The Infrastructure Blueprint)
This file defines the technical foundation of our search capabilities. It contains:
- **Index Mappings**: Uses `strict` dynamic mapping to ensure data integrity.
- **HNSW/k-NN Configuration**: Configures the `hnsw` algorithm for vector search using the `faiss` engine and `cosinesimil` space type. It optimizes for recall with `ef_construction` set to 512.
- **Custom Analyzers**: Defines a `text_analyzer` that uses `standard` tokenization combined with `lowercase`, `stop`, and `snowball` filters for better keyword matching.
- **RRF Pipeline**: Defines the `hybrid-rrf-pipeline` with a `rank_constant` of 60, implementing the standard Reciprocal Rank Fusion formula.

### `QueryBuilder` (The Query Engine)
The `QueryBuilder` is a dynamic class that abstracts OpenSearch's verbose JSON Query DSL into a simple, object-oriented interface.
- **Multi-Match Strategies**: Implements `best_fields` matching with `fuzziness: "AUTO"` to handle typos and varied terminology.
- **Field Boosting**: Automatically applies weights (e.g., `chunk_text^3`) to prioritize matches in critical fields.
- **Context-Aware Mapping**: Dynamically adjusts which fields are searched and highlighted based on whether it's a "paper" search or a granular "chunk" search.
- **Highlighting**: Custom-configures HTML `<mark>` tags for providing users with visual context for why a result was returned.

## Configuration

Settings are pulled from `src/config.py`:
- `opensearch_host`: The URL of the OpenSearch cluster.
- `index_name`: The base name for the paper indices.
- `chunk_index_suffix`: Suffix used for the granular chunk index.
