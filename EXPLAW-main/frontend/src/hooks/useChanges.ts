import { useCallback, useEffect, useState } from "react";
import { listChanges } from "../api/client";
import { Change } from "../types";

/** Stage 2: loads and holds the inbox list. */
export function useChanges() {
  const [changes, setChanges] = useState<Change[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    setLoading(true);
    listChanges()
      .then(setChanges)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { changes, loading, refresh };
}
