from db.base import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

class Paper(Base):
    __tablename__ = "papers"

    # Core arXiv metadata
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    arxiv_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    authors = Column(JSON, nullable=False)
    categories = Column(JSON, nullable=False)
    published_date = Column(DateTime, nullable=False)
    pdf_url = Column(String, nullable=False)

    # Parsed PDF content 
    raw_text = Column(Text, nullable=True)
    sections = Column(JSON, nullable=True)
    references = Column(JSON, nullable=True)

    # PDF processing metadata
    parser_used = Column(String, nullable=True)
    parser_metadata = Column(JSON, nullable=True)
    pdf_processed = Column(Boolean, default=False, nullable=False)
    pdf_processing_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=lambda: datetime.now(timezone.utc))