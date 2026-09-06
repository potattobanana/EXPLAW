"""
Stage 1: classifies each raw diff as a new Act, new subsidiary
legislation, or a clause amendment/addition/removal.

NEW_ACT is handled separately in change_service, one Change per
newly-tracked statute rather than per-section: the diff engine's
"initial_snapshot" diff_type fires once per *section* the first time
we scrape a given Act, and collapsing all of those into a single
Change (instead of running each through classify() individually) is
what keeps day-one tracking of a 400-section Act from flooding the
inbox with 400 "new act" rows. There's no scraper for subsidiary
legislation (SL) yet - sso_scraper only pulls /Act/ pages - so
NEW_SUBSIDIARY_LEGISLATION is defined for when that's added but never
produced today.
"""

from enum import Enum


class ChangeType(str, Enum):
    NEW_ACT = "new_act"
    NEW_SUBSIDIARY_LEGISLATION = "new_subsidiary_legislation"
    CLAUSE_AMENDMENT = "clause_amendment"
    CLAUSE_ADDITION = "clause_addition"
    CLAUSE_REMOVAL = "clause_removal"


_DIFF_TYPE_TO_CHANGE_TYPE = {
    "added": ChangeType.CLAUSE_ADDITION,
    "removed": ChangeType.CLAUSE_REMOVAL,
    "modified": ChangeType.CLAUSE_AMENDMENT,
}


def classify(diff: dict) -> ChangeType:
    """Classifies one section-level diff from diff_engine. Only
    handles "added"/"removed"/"modified" - "initial_snapshot" diffs
    are aggregated into a single NEW_ACT Change per statute upstream
    in change_service and should never reach this function."""
    diff_type = diff.get("diff_type")
    try:
        return _DIFF_TYPE_TO_CHANGE_TYPE[diff_type]
    except KeyError:
        raise ValueError(f"classify() can't handle diff_type {diff_type!r}") from None
