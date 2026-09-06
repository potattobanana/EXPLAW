import React from "react";

/** Renders AI-generated point-form text (lines starting with "- ") as
 * an actual bulleted list. Falls back to a single paragraph for text
 * that isn't in that format (e.g. older summaries generated before
 * the prompt asked for bullets), so nothing breaks either way. */
export default function BulletList({ text, className }: { text: string; className?: string }) {
  const points = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^[-*]\s*/, ""));

  const isBulleted = /^[-*]\s/.test(text.trim()) || points.length > 1;

  if (!isBulleted) {
    return <p className={className}>{text}</p>;
  }

  return (
    <ul className={className ? `${className} bullet-list` : "bullet-list"}>
      {points.map((point, i) => (
        <li key={i}>{point}</li>
      ))}
    </ul>
  );
}
