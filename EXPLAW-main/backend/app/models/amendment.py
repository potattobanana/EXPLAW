"""
Stage 4: records whether a lawyer agreed or rejected the suggested
amendment for a given affected document, and (if agreed) links to the
newly generated client document version.
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SAEnum
import enum

from app.db.session import Base


class Decision(str, enum.Enum):
    AGREED = "agreed"
    REJECTED = "rejected"


class AmendmentDecision(Base):
    __tablename__ = "amendment_decisions"

    id = Column(String, primary_key=True)
    affected_document_id = Column(String, ForeignKey("affected_documents.id"), nullable=False)
    decision = Column(SAEnum(Decision), nullable=False)
    decided_at = Column(DateTime, nullable=False)
    generated_document_id = Column(String, nullable=True)  # set only if AGREED
