from sqlalchemy.orm import Session
from models.paper import Paper
from schemas.arxiv.paper import PaperCreate
from datetime import datetime


class PaperRepository:
    def __init__(self, session:Session):
        self.session = session

    def create(self, paper: PaperCreate)
        db_paper = Paper(**paper.model_dump())
        self.session.add(db_paper)
        self.session.commit()
        self.session.refresh(db_paper)
        return db_paper
    