# Airflow Ingestion Pipeline

This directory contains the Apache Airflow orchestration logic for the automated paper ingestion pipeline.

## Pipeline Overview

The main workflow is defined in `dags/arxiv_paper_ingestion.py` and runs daily to keep the research paper database up to date.

### Workflow Steps:
1. **Setup**: Initializes the environment and required directories.
2. **Fetch**: Connects to the arXiv API to find new papers in specified categories (e.g., Computer Science - Artificial Intelligence).
3. **Download & Process**: Downloads the latest PDFs and uses the `pdf_parser` service to extract structured text.
4. **Index**: Chunks the extracted text, generates embeddings, and indexes the results into OpenSearch for hybrid search.
5. **Report**: Generates a summary report of the day's ingestion activity.
6. **Cleanup**: Removes temporary files to manage disk space.

## Directory Structure

- **`dags/`**: Contains the DAG definitions.
  - `arxiv_paper_ingestion.py`: The primary ingestion workflow.
  - `arxiv_ingestion/`: Modular logic for each step of the pipeline (fetching, indexing, reporting).
- **`plugins/`**: Custom hooks or operators (if any).
- **`Dockerfile`**: Custom Airflow image with all required project dependencies (including the `src` module).
- **`entrypoint.sh`**: Script to initialize the Airflow database and start services.

## Configuration

The pipeline relies on environment variables defined in the root `.env` file, as well as the global system settings in `src/config.py`.
