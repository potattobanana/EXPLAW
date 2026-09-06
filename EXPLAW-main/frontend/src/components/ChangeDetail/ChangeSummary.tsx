import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import AffectedDocumentsList from "./AffectedDocumentsList";
import AppHeader from "../common/AppHeader";
import BulletList from "../common/BulletList";
import ChangeTypeBadge from "../common/ChangeTypeBadge";
import { getChangeDetail } from "../../api/client";
import { Change } from "../../types";

/**
 * Stage 2: opened when a user clicks an inbox item. Shows (1) summary
 * + effective date, (2) general effects/implications, (3) hands off
 * to AffectedDocumentsList for the filterable document list (or the
 * empty state if none are affected).
 */
export default function ChangeSummary() {
  const { changeId } = useParams<{ changeId: string }>();
  const [change, setChange] = useState<Change | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!changeId) return;
    setLoading(true);
    getChangeDetail(changeId)
      .then(setChange)
      .finally(() => setLoading(false));
  }, [changeId]);

  if (loading) {
    return (
      <>
        <AppHeader crumbs={[{ label: "Change" }]} />
        <div className="app-main loading-row">
          <span className="spinner" />
          Loading change...
        </div>
      </>
    );
  }

  if (!change) {
    return (
      <>
        <AppHeader crumbs={[{ label: "Change" }]} />
        <div className="app-main empty-state">Change not found.</div>
      </>
    );
  }

  return (
    <>
      <AppHeader crumbs={[{ label: change.statuteId }]} />
      <div className="app-main change-summary">
        <ChangeTypeBadge changeType={change.changeType} />
        <p className="change-summary__meta">
          <span>
            <strong>{change.statuteId}</strong>
            {change.section && <> s.{change.section}</>}
          </span>
          <span>
            Effective:{" "}
            {change.effectiveDate ? new Date(change.effectiveDate).toLocaleDateString() : "Not known"}
          </span>
        </p>

        <div className="card">
          {change.summaryUnverified && (
            <p style={{ margin: "0 0 var(--space-3)" }}>
              <span className="pill pill-warning">⚠ Unverified AI summary</span>{" "}
              <span style={{ color: "var(--color-muted)", fontSize: "0.85rem" }}>
                — its citation couldn't be confirmed against retrieved statute text. Please verify before relying on it.
              </span>
            </p>
          )}
          <BulletList text={change.summary} />
          {change.generalEffects && (
            <>
              <h3>Why it matters</h3>
              <BulletList text={change.generalEffects} className="change-summary__effects" />
            </>
          )}
        </div>

        <h2 className="change-summary__section-title">Affected documents</h2>
        {changeId && <AffectedDocumentsList changeId={changeId} />}
      </div>
    </>
  );
}
