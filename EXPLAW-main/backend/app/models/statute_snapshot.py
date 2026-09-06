"""
Stage 1: the last successfully scraped text of each tracked statute
section, keyed by (statute_id, section). diff_engine compares each
new scrape against these rows to find what changed since the last
successful run - not just "yesterday" - so a missed run doesn't
create gaps or duplicate change records.
"""

from sqlalchemy import Column, DateTime, String

from app.db.session import Base


class StatuteSnapshot(Base):
    __tablename__ = "statute_snapshots"

    id = Column(String, primary_key=True)  # f"{statute_id}:{section}"
    statute_id = Column(String, nullable=False)
    section = Column(String, nullable=False)
    heading = Column(String)
    text = Column(String, nullable=False)
    fetched_at = Column(DateTime, nullable=False)
