import { useEffect, useState } from "react";
import { listAffectedDocuments } from "../api/client";
import { AffectedDocument } from "../types";

/** Stage 2: loads every document affected by a change. Practice-area
 * filtering is done client-side in AffectedDocumentsList (see that
 * component for why) rather than by refetching per filter change. */
export function useDocuments(changeId: string) {
  const [documents, setDocuments] = useState<AffectedDocument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listAffectedDocuments(changeId).then((data) => {
      if (!cancelled) {
        setDocuments(data);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [changeId]);

  return { documents, loading };
}
