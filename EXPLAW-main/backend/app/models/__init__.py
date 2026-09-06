"""
Importing this package registers every model on Base.metadata, which
db.session.Base.metadata.create_all() and Alembic autogenerate both
rely on - a model that's never imported never gets a table.
"""

from app.models.amendment import AmendmentDecision
from app.models.change import Change
from app.models.document import AffectedDocument, Document
from app.models.statute_snapshot import StatuteSnapshot

__all__ = [
    "AmendmentDecision",
    "Change",
    "AffectedDocument",
    "Document",
    "StatuteSnapshot",
]
