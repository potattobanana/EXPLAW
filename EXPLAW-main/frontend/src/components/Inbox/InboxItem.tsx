import React from "react";
import { Link } from "react-router-dom";
import { Change } from "../../types";
import ChangeTypeBadge from "../common/ChangeTypeBadge";

const DATE_FORMAT: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" };

/** Point-form summaries read as "- a - b - c" when line-clamped as a
 * single paragraph, so the inbox preview joins bullet lines back into
 * flowing text instead. */
function toPreviewText(summary: string): string {
  return summary
    .split("\n")
    .map((line) => line.trim().replace(/^[-*]\s*/, ""))
    .filter(Boolean)
    .join(" ");
}

/**
 * Stage 2: one row in the inbox - change type, short summary, date,
 * unread indicator. Clicking navigates to /changes/:changeId.
 */
export default function InboxItem({ change }: { change: Change }) {
  return (
    <Link
      to={`/changes/${change.id}`}
      className={`inbox-item${change.isRead ? "" : " inbox-item--unread"}`}
    >
      <div className="inbox-item__row">
        <span style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
          <ChangeTypeBadge changeType={change.changeType} />
          {change.summaryUnverified && <span className="pill pill-warning">⚠ Unverified AI summary</span>}
        </span>
        <span className="inbox-item__date">
          {new Date(change.detectedAt).toLocaleDateString(undefined, DATE_FORMAT)}
        </span>
      </div>
      <p className="inbox-item__summary">{toPreviewText(change.summary)}</p>
    </Link>
  );
}
