import React, { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import SuggestedAmendment from "./SuggestedAmendment";
import AppHeader from "../common/AppHeader";
import { getDocumentReview, DocumentReview } from "../../api/client";

/**
 * Stage 3: opened doc with the affected portion shown Google-Docs-
 * suggestion-style - the existing clause struck through immediately
 * followed by the AI's proposed replacement - plus a citation back to
 * the source statute/paragraph. Hands off to SuggestedAmendment for
 * the accept/reject/regenerate/write-it-yourself controls; this
 * component owns `review` so regenerating or manually editing the
 * draft immediately updates the diff shown here too.
 */
export default function DocumentViewer() {
  const { changeId, documentId } = useParams<{ changeId: string; documentId: string }>();
  const [review, setReview] = useState<DocumentReview | null>(null);
  const [loading, setLoading] = useState(true);

  // Silent refetch (no page-level spinner) - used after an action like
  // regenerate/reject/agree so the diff above updates without flashing
  // the whole page back to a loading state. SuggestedAmendment tracks
  // its own busy/spinner state for the action itself.
  const refetch = useCallback(() => {
    if (!changeId || !documentId) return Promise.resolve();
    return getDocumentReview(documentId, changeId).then(setReview);
  }, [changeId, documentId]);

  useEffect(() => {
    setLoading(true);
    refetch().finally(() => setLoading(false));
  }, [refetch]);

  if (loading) {
    return (
      <>
        <AppHeader crumbs={changeId ? [{ label: "Change", to: `/changes/${changeId}` }, { label: "Document" }] : []} />
        <div className="app-main loading-row">
          <span className="spinner" />
          Generating the AI suggestion (this can take a moment)...
        </div>
      </>
    );
  }

  if (!review || !changeId || !documentId) {
    return (
      <>
        <AppHeader crumbs={[{ label: "Document" }]} />
        <div className="app-main empty-state">Document review not found.</div>
      </>
    );
  }

  const { currentText, highlightedPortion, suggestedText } = review;
  const highlightIndex = highlightedPortion ? currentText.indexOf(highlightedPortion) : -1;

  return (
    <>
      <AppHeader crumbs={[{ label: "Change", to: `/changes/${changeId}` }, { label: review.title }]} />
      <div className="app-main document-viewer">
        <h1>{review.title}</h1>
        <span className="pill pill-neutral">{review.practiceArea}</span>

        <div className="card" style={{ marginTop: "var(--space-4)" }}>
          <div className="document-viewer__text">
            {highlightIndex === -1 || !highlightedPortion ? (
              currentText
            ) : (
              <>
                {currentText.slice(0, highlightIndex)}
                <span className="diff-old">{highlightedPortion}</span>
                {suggestedText && (
                  <>
                    <span className="diff-arrow">&rarr;</span>
                    <span className="diff-new">{suggestedText}</span>
                  </>
                )}
                {currentText.slice(highlightIndex + highlightedPortion.length)}
              </>
            )}
          </div>

          {review.citation && <p className="document-viewer__citation">Source: {review.citation}</p>}
        </div>

        <SuggestedAmendment documentId={documentId} changeId={changeId} review={review} onChanged={refetch} />
      </div>
    </>
  );
}
