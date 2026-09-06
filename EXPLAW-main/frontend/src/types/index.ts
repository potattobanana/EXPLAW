export type ChangeType =
  | "new_act"
  | "new_subsidiary_legislation"
  | "clause_amendment"
  | "clause_addition"
  | "clause_removal";

export interface Change {
  id: string;
  changeType: ChangeType;
  statuteId: string;
  section: string | null;
  summary: string;
  /** True when the AI's citation couldn't be verified against text it
   * actually retrieved - `summary` is still whatever it produced, just
   * needs a lawyer's eyes before being trusted. */
  summaryUnverified: boolean;
  effectiveDate: string | null;
  generalEffects: string | null;
  detectedAt: string;
  isRead: boolean;
}

export interface AffectedDocument {
  id: string;
  documentId: string;
  title: string;
  practiceArea: string;
  highlightedPortion: string | null;
  citation: string | null;
  suggestedText: string | null;
}
