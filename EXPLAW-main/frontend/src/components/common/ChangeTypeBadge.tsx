import React from "react";
import { ChangeType } from "../../types";

const LABELS: Record<ChangeType, string> = {
  new_act: "New Act",
  new_subsidiary_legislation: "New Subsidiary Legislation",
  clause_amendment: "Clause Amendment",
  clause_addition: "Clause Addition",
  clause_removal: "Clause Removal",
};

export default function ChangeTypeBadge({ changeType }: { changeType: ChangeType }) {
  return <span className={`pill pill-${changeType}`}>{LABELS[changeType] ?? changeType}</span>;
}
