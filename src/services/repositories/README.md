# Repositories Service

The Repositories Service provides the Data Access Layer (DAL) for the application, encapsulating the complexity of database interactions using SQLAlchemy.

## Features

- **Persistence Logic**: Abstracts the creation, retrieval, and updating of database models.
- **Upsert Support**: Intelligent "update or insert" logic to handle continuous paper ingestion without duplicates.
- **Type Safety**: Uses Pydantic schemas (like `PaperCreate`) for input validation before database commitment.

## Components

### `PaperRepository`
The primary repository class for managing research paper records. It provides standardized methods for common operations:
- `create()`: Adds a new paper to the database.
- `update()`: Modifies an existing paper record.
- `get_by_arxiv_id()`: Fast retrieval using the unique arXiv identifier.
- `upsert()`: A high-level method that either updates an existing paper or creates a new one based on the arXiv ID.


## Integration

Repositories are used throughout the system:
- **FastAPI Core**: For retrieving paper details to serve through the API.
- **Airflow Ingestion Pipeline**: For saving newly discovered papers from the arXiv API.
- **Indexing Service**: For loading paper content before processing it for OpenSearch.