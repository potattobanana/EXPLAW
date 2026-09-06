import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useDocuments } from "../../hooks/useDocuments";

/**
 * Stage 2: list of documents affected by this change, filterable by
 * practice area. If the list is empty, renders the "no documents
 * affected" empty state instead of an empty table.
 *
 * The practice area options are derived from the affected documents
 * themselves rather than a hardcoded taxonomy - the firm's actual
 * taxonomy is still an open decision (see docs/workflow.md), and a
 * guessed hardcoded list would either hide real options or offer ones
 * with nothing behind them. Filtering happens client-side against the
 * one unfiltered fetch, since the whole set is already in hand.
 */
export default function AffectedDocumentsList({
  changeId,
}: {
  changeId: string;
}) {
  const { documents, loading } = useDocuments(changeId);
  const [practiceArea, setPracticeArea] = useState("All");

  const practiceAreas = useMemo(
    () => Array.from(new Set(documents.map((doc) => doc.practiceArea))).sort(),
    [documents]
  );
  const filtered =
    practiceArea === "All" ? documents : documents.filter((doc) => doc.practiceArea === practiceArea);

  if (loading) {
    return (
      <div className="loading-row">
        <span className="spinner" />
        Loading affected documents...
      </div>
    );
  }

  return (
    <div>
      {practiceAreas.length > 1 && (
        <select value={practiceArea} onChange={(e) => setPracticeArea(e.target.value)} style={{ marginBottom: "var(--space-3)" }}>
          <option value="All">All practice areas</option>
          {practiceAreas.map((area) => (
            <option key={area} value={area}>
              {area}
            </option>
          ))}
        </select>
      )}

      {filtered.length === 0 ? (
        <div className="empty-state">No documents affected by this change.</div>
      ) : (
        <ul className="doc-list">
          {filtered.map((doc) => (
            <li key={doc.id} className="doc-list__item">
              <Link className="doc-list__title" to={`/changes/${changeId}/documents/${doc.documentId}`}>
                {doc.title}
              </Link>
              <span className="pill pill-neutral">{doc.practiceArea}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
