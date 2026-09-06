import React, { useState } from "react";
import InboxItem from "./InboxItem";
import NotificationBadge from "../common/NotificationBadge";
import AppHeader from "../common/AppHeader";
import { useChanges } from "../../hooks/useChanges";
import { triggerManualCheck } from "../../api/client";

type CheckResult = { newChanges: number } | { error: string };

/**
 * Stage 2: email-inbox-style sidebar. Lists past + new changes,
 * newest/unread highlighted. Also hosts the manual "check now" button
 * (Stage 1).
 */
export default function InboxList() {
  const { changes, loading, refresh } = useChanges();
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<CheckResult | null>(null);
  const unreadCount = changes.filter((c) => !c.isRead).length;

  async function handleCheckNow() {
    setChecking(true);
    setResult(null);
    try {
      const { new_changes } = await triggerManualCheck();
      setResult({ newChanges: new_changes });
      refresh();
    } catch (err) {
      setResult({ error: err instanceof Error ? err.message : "Something went wrong." });
    } finally {
      setChecking(false);
    }
  }

  return (
    <>
      <AppHeader />
      <div className="app-main inbox">
        <div className="inbox__header">
          <h1>
            Inbox <NotificationBadge count={unreadCount} />
          </h1>
          <button className="btn-primary" onClick={handleCheckNow} disabled={checking}>
            {checking ? "xplaw-ing..." : "Check now"}
          </button>
        </div>

        {checking && (
          <div className="loading-row" style={{ marginBottom: "var(--space-4)" }}>
            <span className="spinner" />
            xplaw-ing...
          </div>
        )}

        {!checking && result && "newChanges" in result && (
          <div className="empty-state" style={{ marginBottom: "var(--space-4)", padding: "var(--space-3) var(--space-4)" }}>
            ✓ Check complete -{" "}
            {result.newChanges === 0 ? "no new changes found." : `${result.newChanges} new change(s) added.`}
          </div>
        )}

        {!checking && result && "error" in result && (
          <div className="empty-state" style={{ marginBottom: "var(--space-4)", color: "var(--color-danger)" }}>
            Check failed: {result.error}
          </div>
        )}

        {loading ? (
          <div className="loading-row">
            <span className="spinner" />
            Loading changes...
          </div>
        ) : changes.length === 0 ? (
          <div className="empty-state">
            <p>No statute changes detected yet.</p>
            <p>Click "Check now" to run a scan against the tracked Acts.</p>
          </div>
        ) : (
          <div className="inbox__list">
            {changes.map((change) => (
              <InboxItem key={change.id} change={change} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
