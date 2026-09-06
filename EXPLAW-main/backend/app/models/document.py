"""
A firm document (contract template, policy, etc.) and the join
between a document and a change that affects it.
"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    practice_area = Column(String, nullable=False)  # used for Stage 2 filter
    current_text = Column(String, nullable=False)


class AffectedDocument(Base):
    """Links a Change to a Document it affects, plus the AI's
    suggested amendment for that specific pairing."""

    __tablename__ = "affected_documents"

    id = Column(String, primary_key=True)
    change_id = Column(String, ForeignKey("changes.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    highlighted_portion = Column(String)
    citation = Column(String)
    suggested_text = Column(String)
    # JSON-serialized ReAct agent message history for this pairing (see
    # react_agent.py) - lets "try again with AI" continue the same
    # conversation instead of starting from a blank slate each time.
    # Cleared when a lawyer manually overwrites the draft, since a
    # resumed conversation that doesn't know about that edit would be
    # actively misleading rather than just unhelpful.
    conversation_history = Column(String)

    change = relationship("Change", back_populates="affected_documents")
    document = relationship("Document")
