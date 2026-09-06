/**
 * Thin wrapper around fetch for the backend API. Add auth headers
 * here once the firm's login flow is decided.
 */

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

/** Throws with the backend's error detail on a non-2xx response,
 * instead of letting callers treat a valid-JSON error body as success. */
async function parseOrThrow(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return body;
}

export async function triggerManualCheck(): Promise<{ new_changes: number; change_ids: string[] }> {
  // Stage 1: "check now" button. Scrapes the tracked Acts live, so
  // this routinely takes 30s-2min - genuine network + PDF-parsing
  // work, not a hang. Callers should show a clear "this may take a
  // while" state rather than a bare button-label change.
  const response = await fetch(`${BASE_URL}/changes/check`, { method: "POST" });
  return parseOrThrow(response);
}

export async function listChanges() {
  // Stage 2: inbox sidebar
  return fetch(`${BASE_URL}/changes/`).then((r) => r.json());
}

export async function getChangeDetail(changeId: string) {
  // Stage 2: change detail view
  return fetch(`${BASE_URL}/changes/${changeId}`).then((r) => r.json());
}

export async function listAffectedDocuments(
  changeId: string,
  practiceArea?: string
) {
  // Stage 2: affected documents, filterable by practice area
  const params = new URLSearchParams({ change_id: changeId });
  if (practiceArea) params.set("practice_area", practiceArea);
  return fetch(`${BASE_URL}/documents/?${params}`).then((r) => r.json());
}

export interface DocumentReview {
  id: string;
  documentId: string;
  title: string;
  practiceArea: string;
  currentText: string;
  highlightedPortion: string | null;
  citation: string | null;
  suggestedText: string | null;
  agreed: boolean;
  generatedDocumentId: string | null;
  rejectionCount: number;
}

export async function getDocumentReview(documentId: string, changeId: string): Promise<DocumentReview> {
  // Stage 3: document with highlights, citation, suggested amendment
  const params = new URLSearchParams({ change_id: changeId });
  const response = await fetch(`${BASE_URL}/documents/${documentId}?${params}`);
  return parseOrThrow(response);
}

export async function regenerateSuggestion(
  documentId: string,
  changeId: string,
  guidance?: string
): Promise<DocumentReview> {
  // Stage 3 review loop: ask the AI to try again, optionally steered
  // by the lawyer's own instruction for this attempt
  const response = await fetch(`${BASE_URL}/documents/${documentId}/regenerate?change_id=${changeId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ guidance: guidance || null }),
  });
  return parseOrThrow(response);
}

export async function setManualSuggestion(
  documentId: string,
  changeId: string,
  highlightedPortion: string,
  suggestedText: string
): Promise<DocumentReview> {
  // Stage 3 review loop: write the replacement clause yourself
  const response = await fetch(`${BASE_URL}/documents/${documentId}/suggestion?change_id=${changeId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ highlightedPortion, suggestedText }),
  });
  return parseOrThrow(response);
}

export async function listAllDocuments(): Promise<
  { id: string; title: string; practiceArea: string; currentText: string }[]
> {
  // Document management page: every onboarded firm document
  const response = await fetch(`${BASE_URL}/documents/all`);
  return parseOrThrow(response);
}

export async function createDocument(
  title: string,
  practiceArea: string,
  currentText: string
): Promise<{ id: string; title: string; practiceArea: string }> {
  // Onboards a new firm document template
  const response = await fetch(`${BASE_URL}/documents/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, practiceArea, currentText }),
  });
  return parseOrThrow(response);
}

export async function agreeToAmendment(documentId: string, changeId: string) {
  // Stage 4: agree -> generates new document for client
  const response = await fetch(`${BASE_URL}/amendments/${documentId}/agree?change_id=${changeId}`, {
    method: "POST",
  });
  return parseOrThrow(response);
}

export async function rejectAmendment(documentId: string, changeId: string) {
  // Stage 4: reject -> no change, logged
  const response = await fetch(`${BASE_URL}/amendments/${documentId}/reject?change_id=${changeId}`, {
    method: "POST",
  });
  return parseOrThrow(response);
}
