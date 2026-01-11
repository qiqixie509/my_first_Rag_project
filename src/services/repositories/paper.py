from sqlalchemy.orm import Session
from src.models.paper import Paper
from src.schemas.arxiv.paper import PaperCreate
from datetime import datetime
from sqlalchemy import select


class PaperRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, paper: PaperCreate) -> Paper:
        db_paper = Paper(**paper.model_dump())
        self.session.add(db_paper)
        self.session.commit()
        self.session.refresh(db_paper)
        return db_paper

    def update(self, db_paper: Paper, paper_data: PaperCreate) -> Paper:
        """Update an existing paper in the database with new data."""
        for key, value in paper_data.model_dump(exclude_unset=True).items():
            setattr(db_paper, key, value)
        
        self.session.commit()
        self.session.refresh(db_paper)
        return db_paper

    def get_by_arxiv_id(self, arxiv_id: str) -> Paper | None:
        stmt = select(Paper).where(Paper.arxiv_id == arxiv_id)
        return self.session.scalar(stmt)

    def upsert(self, paper: PaperCreate) -> Paper:
        existing_paper = self.get_by_arxiv_id(paper.arxiv_id)
        if existing_paper:
            return self.update(existing_paper, paper)
        else:
            return self.create(paper)

    