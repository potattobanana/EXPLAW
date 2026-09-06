import React from "react";

/** Small unread-count pill, e.g. for the inbox tab. */
export default function NotificationBadge({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <span
      style={{
        display: "inline-block",
        minWidth: "20px",
        padding: "0.1rem 0.4rem",
        borderRadius: "999px",
        fontSize: "0.75rem",
        fontWeight: 600,
        textAlign: "center",
        background: "var(--color-accent)",
        color: "white",
      }}
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}
