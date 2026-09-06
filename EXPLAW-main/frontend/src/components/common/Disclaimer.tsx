import React from "react";

/**
 * Always shown alongside any AI-suggested amendment. Do not remove
 * or make this dismissible - lawyers must be reminded to make
 * amendments themselves.
 */
export default function Disclaimer() {
  return (
    <p role="note" style={{ margin: 0 }}>
      This is an AI-generated suggestion. Please review and make any
      amendments yourself before relying on it.
    </p>
  );
}
