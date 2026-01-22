# PDF Parser Service

The PDF Parser Service is responsible for extracting structured content and raw text from PDF research papers. It is built on top of [Docling](https://github.com/DS4SD/docling), a powerful document parsing tool by IBM.

## Features

- **Structural Extraction**: Automatically identifies headers, titles, and sections to organize the paper content.
- **OCR Support**: Optional Optical Character Recognition for processing scanned or non-searchable PDFs.
- **Robust Validation**:
  - Prevents processing of non-PDF or corrupted files.
  - Enforces configurable limits on page count and file size to optimize resource usage.
- **Export Options**: Provides both structured section-based data and full raw text.
- **Table Structure**: Capable of recovering structural information for tables within the documents.

## Components

### `PDFParserService`
A high-level service wrapper that provides a clean `parse_pdf` interface for the rest of the application. It handles high-level error catching and service-level logic.

### `DoclingParser`
The core engine that wraps the `docling` library. It includes:
- **PDF Validation**: Uses `pypdfium2` for fast page counting and preliminary file checks.
- **Element Mapping**: Converts `Docling` internal document elements into the application's unified `PdfContent` schema.

### `make_pdf_parser_service`
A factory function in `factory.py` that initializes the service with global settings and implements an LRU cache to maintain a single instance of the parser models.


## Configuration

The parser behavior is controlled via settings in `src/config.py`:
- `max_pages`: Maximum number of pages to process.
- `max_file_size_mb`: Maximum allowed file size.
- `do_ocr`: Enable/disable OCR processing.
- `do_table_structure`: Enable/disable advanced table parsing.
