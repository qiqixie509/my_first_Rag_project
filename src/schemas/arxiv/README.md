# ArXiv Schemas

This directory contains the Pydantic data models used for representing arXiv papers throughout the application's lifecycle.

## Models

### `ArxivPaper`
The primary schema used when fetching data directly from the arXiv API. It captures the essential metadata provided by the Atom feed.

### `PaperBase`
A shared base model that defines core arXiv metadata. These fields are common to both raw fetched data and papers stored in the database.

### `PaperCreate`
An expansion of `PaperBase` used during the data ingestion process. It adds optional fields for:
- Extracted raw text.
- Structured sections.
- Parser metadata (e.g., from Docling).
- Processing status flags.

### `PaperResponse`
The full schema used for API responses from our internal service. It inherits from `PaperBase` and adds:
- `id`: Unique UUID for the database record.
- Full extracted content (sections, text).
- Database timestamps (`created_at`, `updated_at`).
- Processing metadata.