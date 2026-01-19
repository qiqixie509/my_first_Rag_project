# my_first_Rag_project
This is a paper search assistant that enables you to find specific papers of interest by asking questions on your local device.  This project is inspired by JAMWITHAI. 

## Data Ingestion




- Arxiv: It is responsible for fetching the latest research papers automatically daily.
- PDF Parsing: It is responsible for parsing the PDFs of the research papers using docling.
- Metadata Storage: Store authors, titles, abstracts, and categories of the research papers. The metadata is stored in PostgreSQL.
- Search Engine: Use OpenSearch to index the parsed data, and apply hybrid search (BM25 + semantic vectors) to retrieve the relevant papers.
- Chunking Engine: 
- Rag pipeline: Query expansion + retriveval + prompt templating
- Local LLM: Answer questions using Ollama or API
- Observability: 
- FastAPI backend: 
 

## Environment
- Python 3.12
- Docker
- Docker Compose
- uv

## Dependencies
- PostgreSQL
- OpenSearch
- Ollama
- Airflow   

## Arxiv Ingestion


## Data Ingestion
Data source: arxiv
Docling PDF processing
Data storage: PostgreSQL
Opensearch indexing
Embedding using Jani


## Data Ingestion Pipeline
Fetch PDFs using Arxiv API -> Parse PDFs using Docling -> Store the parsed data in PostgreSQL -> Index the parsed data in OpenSearch -> Embedding the parsed data using Jani -> Daily report including the data from PostgreSQL and OpenSearch

## FastAPI Design
The FastAPI backend is designed to provide a RESTful API for the RAG system. The API is designed to be used by other applications to query the RAG system and get answers to questions. We used a central hub for dependency injection (DI), separated how objects are created from where they are used, making the code more clean and testable. API routes like ask_question just ask for an OpenSearchDep. We reuse that single connection across thousands of requests, rather than creating a new expensive connection for every single user query.
- /ask: Ask a question
- /stream: Stream the answer




