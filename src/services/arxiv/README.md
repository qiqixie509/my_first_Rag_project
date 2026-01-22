# ArXiv Service

The ArXiv Service provides a client for interacting with the arXiv API to fetch research paper metadata and download full-text PDFs.

## Features

- **Metadata Fetching**: Search and retrieve paper details (title, authors, abstract, categories) based on specific categories (e.g., `cs.LG`, `cs.AI`) and date ranges.
- **XML Parsing**: Parsing of arXiv's Atom Feed format into structured `ArxivPaper` objects.
- **PDF Downloader**: Async downloading of paper PDFs with configurable retry logic and exponential backoff.
- **Rate Limiting**: Built-in adherence to arXiv's rate-limiting policies to prevent IP blocks.
- **PDF Caching**: Local caching mechanism to avoid redundant downloads of the same paper.

## Components

### `ArxivClient`
The core service class that manages API requests and PDF downloads. It uses `httpx` for asynchronous HTTP requests and `xml.etree.ElementTree` for parsing.
- **Request Timestamp Tracking**: The client keep track of exactly when it last communicated with the arXiv API, to ensure we don't violate arXiv's rate limiting policies. In initialization, the `last_request_time` is set to `None` and every time the `fetch papers` function is called, it records the current time and update the `last_request_time`.
- **Intelligent Delays**: with the `last_request_time`, the code calculates exactly how much time is remaining since the last request, and avoid a dumb sleep like `sleep(3)` every time.
- **Caching**: To save bandwith and avoid being blocked for too many requests, the client uses a local cache to store downloaded PDFs, to avoid redundant downloads of the same paper.


### `make_arxiv_client`
A factory function in `factory.py` that simplifies the initialization of the client using the application's global settings.


## Configuration

The service is configured via `ArxivSettings` in `src/config.py`, which includes:
- `base_url`: The arXiv API endpoint.
- `pdf_cache_dir`: Directory for storing downloaded PDFs.
- `rate_limit_delay`: Delay between consecutive API requests.
- `max_results`: Default number of papers to fetch.
- `search_category`: Default subject category (e.g., `cs.CL`).
