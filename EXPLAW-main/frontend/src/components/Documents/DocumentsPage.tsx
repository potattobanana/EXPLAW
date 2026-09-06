import React, { useCallback, useEffect, useState } from "react";
import AppHeader from "../common/AppHeader";
import { listAllDocuments, createDocument } from "../../api/client";

interface DocumentSummary {
  id: string;
  title: string;
  practiceArea: string;
  currentText: string;
}

/**
 * Firm document onboarding. This is currently the only way to add a
 * document to the system - there's no sync from a firm's actual
 * document management system yet. A real deployment would likely
 * want that integration in addition to (or instead of) this manual
 * form, but this is the minimal path until that exists.
 */
export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [practiceArea, setPracticeArea] = useState("");
  const [currentText, setCurrentText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    listAllDocuments()
      .then(setDocuments)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createDocument(title.trim(), practiceArea.trim(), currentText.trim());
      setTitle("");
      setPracticeArea("");
      setCurrentText("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  const canSubmit = title.trim() && practiceArea.trim() && currentText.trim() && !submitting;

  return (
    <>
      <AppHeader />
      <div className="app-main">
        <h1>Firm documents</h1>
        <p style={{ color: "var(--color-muted)" }}>
          Templates the system checks against detected statute changes. Mention the relevant
          Act by name (e.g. "Companies Act 1967") so changes to it get matched to this document.
        </p>

        <div className="card">
          <h2>Add a document</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "var(--space-3)" }}>
              <label htmlFor="doc-title" style={{ display: "block", marginBottom: "var(--space-1)", fontWeight: 500 }}>
                Title
              </label>
              <input
                id="doc-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Standard NDA Template"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-border-strong)", font: "inherit" }}
              />
            </div>

            <div style={{ marginBottom: "var(--space-3)" }}>
              <label htmlFor="doc-area" style={{ display: "block", marginBottom: "var(--space-1)", fontWeight: 500 }}>
                Practice area
              </label>
              <input
                id="doc-area"
                type="text"
                value={practiceArea}
                onChange={(e) => setPracticeArea(e.target.value)}
                placeholder="e.g. Corporate"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-border-strong)", font: "inherit" }}
              />
            </div>

            <div style={{ marginBottom: "var(--space-3)" }}>
              <label htmlFor="doc-text" style={{ display: "block", marginBottom: "var(--space-1)", fontWeight: 500 }}>
                Document text
              </label>
              <textarea
                id="doc-text"
                value={currentText}
                onChange={(e) => setCurrentText(e.target.value)}
                placeholder="Paste the full text of the template..."
                rows={8}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-border-strong)", font: "inherit", resize: "vertical" }}
              />
            </div>

            {error && <p style={{ color: "var(--color-danger)" }}>Couldn't save: {error}</p>}

            <button className="btn-primary" type="submit" disabled={!canSubmit}>
              {submitting ? "Saving..." : "Add document"}
            </button>
          </form>
        </div>

        <h2 className="change-summary__section-title">Onboarded documents</h2>
        <p style={{ color: "var(--color-muted)", marginTop: 0 }}>Click a document to see its full text.</p>
        {loading ? (
          <div className="loading-row">
            <span className="spinner" />
            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">No documents onboarded yet.</div>
        ) : (
          <ul className="doc-list">
            {documents.map((doc) => {
              const isExpanded = expandedId === doc.id;
              return (
                <li key={doc.id} className="doc-list__item" style={{ display: "block" }}>
                  <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? null : doc.id)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      width: "100%",
                      border: "none",
                      background: "none",
                      padding: 0,
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <span className="doc-list__title">{doc.title}</span>
                    <span className="pill pill-neutral">{doc.practiceArea}</span>
                  </button>
                  {isExpanded && (
                    <p style={{ marginTop: "var(--space-3)", marginBottom: 0, whiteSpace: "pre-wrap", color: "var(--color-text)" }}>
                      {doc.currentText}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </>
  );
}
