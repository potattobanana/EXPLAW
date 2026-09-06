import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Disclaimer from "../common/Disclaimer";
import {
  agreeToAmendment,
  rejectAmendment,
  regenerateSuggestion,
  setManualSuggestion,
  DocumentReview,
} from "../../api/client";

type Busy = null | "agree" | "reject" | "regenerate" | "manual";

/**
 * Stage 3/4: accept/reject/iterate controls for the AI-suggested
 * amendment shown inline (Google-Docs-suggestion style) in
 * DocumentViewer above this component.
 *
 * Rejecting is NOT terminal - only agreeing is, since it's the one
 * action with an irreversible side effect (a new document gets
 * generated). After a reject, the lawyer can ask the AI to try again
 * (optionally steering it with their own instruction) or write the
 * replacement clause themselves, then decide again - this loops for
 * as long as needed rather than dead-ending after one rejection.
 */
export default function SuggestedAmendment({
  documentId,
  changeId,
  review,
  onChanged,
}: {
  documentId: string;
  changeId: string;
  review: DocumentReview;
  onChanged: () => Promise<void> | void;
}) {
  const [busy, setBusy] = useState<Busy>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [prompting, setPrompting] = useState(false);
  const [draftHighlight, setDraftHighlight] = useState("");
  const [draftText, setDraftText] = useState("");
  const [guidance, setGuidance] = useState("");
  const navigate = useNavigate();

  const canApply = Boolean(review.highlightedPortion);

  async function run(which: Busy, action: () => Promise<unknown>) {
    setBusy(which);
    setError(null);
    try {
      await action();
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(null);
    }
  }

  function startEditing() {
    setDraftHighlight(canApply ? review.highlightedPortion ?? "" : "");
    setDraftText(canApply ? review.suggestedText ?? "" : "");
    setEditing(true);
  }

  async function handleSaveManual() {
    await run("manual", async () => {
      await setManualSuggestion(documentId, changeId, draftHighlight.trim(), draftText.trim());
      setEditing(false);
    });
  }

  async function handleRegenerate() {
    await run("regenerate", async () => {
      await regenerateSuggestion(documentId, changeId, guidance.trim() || undefined);
      setPrompting(false);
      setGuidance("");
    });
  }

  if (review.agreed) {
    return (
      <div className="card">
        <p className="suggested-amendment__status suggested-amendment__status--agreed">
          ✓ Amendment agreed - a new document version was generated.
        </p>
        <button onClick={() => navigate(`/changes/${changeId}`)}>Back to change</button>
      </div>
    );
  }

  if (prompting) {
    return (
      <div className="card">
        <h2>Try again with AI</h2>
        <p style={{ color: "var(--color-muted)", marginTop: 0 }}>
          Tell it what to change about its last attempt, or leave this blank to just ask for a
          different approach.
        </p>
        <textarea
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          rows={3}
          placeholder='e.g. "Focus on the indemnity clause instead" or "make it shorter"'
          autoFocus
          style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-border-strong)", font: "inherit", resize: "vertical" }}
        />
        {error && <p style={{ color: "var(--color-danger)" }}>Couldn't submit: {error}</p>}
        <div className="suggested-amendment__actions">
          <button className="btn-primary" onClick={handleRegenerate} disabled={busy === "regenerate"}>
            {busy === "regenerate" ? "Asking AI..." : "Regenerate"}
          </button>
          <button onClick={() => setPrompting(false)} disabled={busy === "regenerate"}>
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (editing) {
    return (
      <div className="card">
        <h2>Write the amendment yourself</h2>
        <div style={{ marginBottom: "var(--space-3)" }}>
          <label htmlFor="draft-highlight" style={{ display: "block", marginBottom: "var(--space-1)", fontWeight: 500 }}>
            Existing text to replace
          </label>
          <textarea
            id="draft-highlight"
            value={draftHighlight}
            onChange={(e) => setDraftHighlight(e.target.value)}
            rows={3}
            placeholder="Paste the exact clause text from the document that needs to change..."
            style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-border-strong)", font: "inherit", resize: "vertical" }}
          />
        </div>
        <div style={{ marginBottom: "var(--space-3)" }}>
          <label htmlFor="draft-text" style={{ display: "block", marginBottom: "var(--space-1)", fontWeight: 500 }}>
            Replacement text
          </label>
          <textarea
            id="draft-text"
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            rows={5}
            placeholder="Your proposed wording..."
            style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-border-strong)", font: "inherit", resize: "vertical" }}
          />
        </div>
        {error && <p style={{ color: "var(--color-danger)" }}>Couldn't save: {error}</p>}
        <div className="suggested-amendment__actions">
          <button
            className="btn-primary"
            onClick={handleSaveManual}
            disabled={busy === "manual" || !draftHighlight.trim() || !draftText.trim()}
          >
            {busy === "manual" ? "Saving..." : "Save draft"}
          </button>
          <button onClick={() => setEditing(false)} disabled={busy === "manual"}>
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (!review.suggestedText) {
    return (
      <div className="card">
        <p>No AI suggestion is available for this document yet.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Review this suggestion</h2>
      {canApply ? (
        <p style={{ color: "var(--color-muted)", margin: 0 }}>
          The proposed change is shown struck-through and inserted above.
        </p>
      ) : (
        <p style={{ color: "var(--color-accent)" }}>⚠ {review.suggestedText}</p>
      )}

      {review.rejectionCount > 0 && (
        <p style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
          Revised after {review.rejectionCount} rejection{review.rejectionCount === 1 ? "" : "s"}.
        </p>
      )}

      <div className="suggested-amendment__disclaimer">
        <span aria-hidden="true">⚠️</span>
        <Disclaimer />
      </div>

      {error && <p style={{ color: "var(--color-danger)" }}>Couldn't submit: {error}</p>}

      <div className="suggested-amendment__actions">
        {canApply && (
          <button className="btn-primary" onClick={() => run("agree", () => agreeToAmendment(documentId, changeId))} disabled={busy !== null}>
            {busy === "agree" ? "Submitting..." : "Agree"}
          </button>
        )}
        <button className="btn-danger" onClick={() => run("reject", () => rejectAmendment(documentId, changeId))} disabled={busy !== null}>
          {busy === "reject" ? "Submitting..." : "Reject"}
        </button>
        <button onClick={() => setPrompting(true)} disabled={busy !== null}>
          Try again with AI
        </button>
        <button onClick={startEditing} disabled={busy !== null}>
          Write it yourself
        </button>
      </div>
    </div>
  );
}
