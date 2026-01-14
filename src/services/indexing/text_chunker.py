import logging
import re
from typing import Optional, Dict, List, Union, Any
from src.schemas.common import ChunkMetadata, TextChunk

logger = logging.getLogger(__name__)

class TextChunker:
    """Service for chunking text into overlapping segments.

    Supports both traditional word-based chunking and section-aware chunking.
    Default: 600 words per chunk with 100 word overlap.
    """
    def __init__(self, chunk_size: int = 600, overlap_size: int = 100, min_chunk_size: int = 100):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size

        if overlap_size >= chunk_size:
            raise ValueError("Overlap size must be less than chunk size")
        logger.info(
            f"Text chunker initialized: chunk_size={chunk_size}, overlap_size={overlap_size}, min_chunk_size={min_chunk_size}"
        )

    def _parse_sections(self, sections: Any) -> Dict[str, str]:
        """Normalize section input into a dictionary of {title: content}."""
        if isinstance(sections, dict):
            return {str(k): str(v) for k, v in sections.items()}
        elif isinstance(sections, list):
            # Handle list of dicts with 'title' and 'content' keys
            parsed = {}
            for i, item in enumerate(sections):
                if isinstance(item, dict):
                    title = item.get("title", f"Section {i+1}")
                    content = item.get("content", "")
                    parsed[title] = content
                else:
                    parsed[f"Section {i+1}"] = str(item)
            return parsed
        elif isinstance(sections, str):
            return {"Content": sections}
        return {}

    def _create_chunk(
        self,
        text: str,
        index: int,
        arxiv_id: str,
        paper_id: Optional[str],
        section_title: Optional[str] = None,
        start_char: int = 0,
        end_char: int = 0,
        overlap_prev: int = 0,
        overlap_next: int = 0
    ) -> TextChunk:
        """Helper to create a TextChunk object."""
        words = text.split()
        return TextChunk(
            text=text,
            metadata=ChunkMetadata(
                chunk_index=index,
                start_char=start_char,
                end_char=end_char,
                word_count=len(words),
                overlap_with_previous=overlap_prev,
                overlap_with_next=overlap_next,
                section_title=section_title
            ),
            arxiv_id=arxiv_id,
            paper_id=paper_id
        )

    def chunk_text(
        self,
        text: str,
        arxiv_id: str,
        paper_id: Optional[str] = None,
        section_title: Optional[str] = None
    ) -> List[TextChunk]:
        """Traditional word-based sliding window chunking."""
        if not text or not text.strip():
            return []

        # Simple whitespace splitting for now
        words = re.findall(r"\S+", text)
        if len(words) < self.min_chunk_size:
            return [self._create_chunk(text, 0, arxiv_id, paper_id, section_title, 0, len(text))]

        chunks = []
        chunk_idx = 0
        i = 0
        while i < len(words):
            chunk_words = words[i:i + self.chunk_size]
            if len(chunk_words) < self.min_chunk_size and chunks:
                break
                
            chunk_text = " ".join(chunk_words)
            
            # Rough character estimations
            start_char = len(" ".join(words[:i])) if i > 0 else 0
            end_char = start_char + len(chunk_text)
            
            overlap_prev = self.overlap_size if i > 0 else 0
            overlap_next = self.overlap_size if i + self.chunk_size < len(words) else 0

            chunks.append(self._create_chunk(
                chunk_text, chunk_idx, arxiv_id, paper_id, 
                section_title, start_char, end_char, 
                overlap_prev, overlap_next
            ))
            
            i += (self.chunk_size - self.overlap_size)
            chunk_idx += 1
            
            if i + self.chunk_size > len(words) and i < len(words):
                # Ensure we don't skip the last bit if it's too small for a full chunk
                # but large enough to be included in the previous one's overlap
                if len(words) - i < self.min_chunk_size:
                    break

        return chunks

    def chunk_paper(
        self,
        title: str,
        abstract: str,
        full_text: str,
        arxiv_id: str,
        paper_id: Optional[str] = None,
        sections: Optional[Any] = None
    ) -> List[TextChunk]:
        """High-level entry point that chooses between section-based or flat chunking."""
        if not sections:
            return self.chunk_text(f"{title}\n\n{abstract}\n\n{full_text}", arxiv_id, paper_id)

        parsed_sections = self._parse_sections(sections)
        if not parsed_sections:
            return self.chunk_text(f"{title}\n\n{abstract}\n\n{full_text}", arxiv_id, paper_id)

        all_chunks = []
        header = f"Title: {title}\nAbstract: {abstract}\n\n"
        
        # We include the header in every chunk for context (optional design choice)
        chunk_idx = 0
        
        # Process sections
        for s_title, s_content in parsed_sections.items():
            section_full_text = f"Section: {s_title}\n{s_content}"
            # Prefix with header for context
            text_to_chunk = f"{header}{section_full_text}"
            
            section_chunks = self.chunk_text(text_to_chunk, arxiv_id, paper_id, s_title)
            
            # Adjust chunk indices
            for chunk in section_chunks:
                chunk.metadata.chunk_index = chunk_idx
                chunk_idx += 1
                all_chunks.append(chunk)

        return all_chunks