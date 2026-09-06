"""
Points the app at a throwaway sqlite file for the whole test session
(set before anything imports app.config/app.db.session, since those
read DATABASE_URL once at import time) and hands each test a fresh,
already-migrated session via the `db` fixture.
"""

import os
import tempfile

_tmp_db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"

import pytest  # noqa: E402

import app.models  # noqa: E402, F401 - registers every model on Base.metadata
from app.db.session import Base, SessionLocal, engine  # noqa: E402

Base.metadata.create_all(engine)


@pytest.fixture()
def db():
    """A fresh session per test. All tables live in one shared sqlite
    file for the whole test session (see module docstring), so every
    test clears its own data on the way out rather than assuming an
    empty database going in."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()
