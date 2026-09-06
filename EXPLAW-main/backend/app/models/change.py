"""
A single detected statute change - one row per Act/amendment/repeal
event picked up by the scraper.
"""

from sqlalchemy import Boolean, Column, String, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.core.classifier import ChangeType


class Change(Base):
    __tablename__ = "changes"

    id = Column(String, primary_key=True)
    change_type = Column(SAEnum(ChangeType), nullable=False)
    statute_id = Column(String, nullable=False)
    section = Column(String)  # which numbered provision changed, if applicable
    old_text = Column(String)  # from the diff engine's snapshot comparison; None for additions
    new_text = Column(String)  # None for removals
    summary = Column(String)
    # True when the AI's citation couldn't be verified against text it
    # actually retrieved (or its answer wasn't even parseable) - the
    # summary above is still whatever it produced, just shown to the
    # lawyer flagged as unverified rather than silently trusted.
    summary_unverified = Column(Boolean, default=False, nullable=False)
    effective_date = Column(DateTime)
    general_effects = Column(String)
    detected_at = Column(DateTime, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)  # unread badge in the inbox

    affected_documents = relationship("AffectedDocument", back_populates="change")
