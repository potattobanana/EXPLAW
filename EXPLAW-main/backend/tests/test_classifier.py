"""Tests for Stage 1: classifying a diff as new Act / subsidiary
legislation / clause amendment, addition, or removal."""

import pytest

from app.core.classifier import ChangeType, classify


def test_classifies_clause_amendment():
    diff = {"diff_type": "modified", "statute_id": "CoA1967", "section": "23"}
    assert classify(diff) == ChangeType.CLAUSE_AMENDMENT


def test_classifies_clause_addition():
    diff = {"diff_type": "added", "statute_id": "CoA1967", "section": "410A"}
    assert classify(diff) == ChangeType.CLAUSE_ADDITION


def test_classifies_clause_removal():
    diff = {"diff_type": "removed", "statute_id": "CoA1967", "section": "300"}
    assert classify(diff) == ChangeType.CLAUSE_REMOVAL


def test_classify_rejects_initial_snapshot():
    """NEW_ACT is decided in change_service (one Change per statute,
    not per section) - classify() should never be asked to handle the
    diff engine's "initial_snapshot" diff_type. See classifier.py's
    module docstring for why."""
    diff = {"diff_type": "initial_snapshot", "statute_id": "CoA1967", "section": "1"}
    with pytest.raises(ValueError):
        classify(diff)
