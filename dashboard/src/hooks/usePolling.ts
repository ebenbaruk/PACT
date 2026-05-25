import { useState, useEffect, useRef, useCallback } from "react";

export function usePolling<T>(
  fetcher: () => Promise<T>,
  interval: number,
  initialValue: T,
): { data: T; isLive: boolean; refresh: () => void } {
  const [data, setData] = useState<T>(initialValue);
  const [isLive, setIsLive] = useState(false);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const poll = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setIsLive(true);
    } catch {
      setIsLive(false);
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, interval);
    return () => clearInterval(id);
  }, [poll, interval]);

  // Lets callers force an immediate refetch (e.g. right after a demo step) so the
  // graph reacts instantly instead of waiting for the next poll tick.
  return { data, isLive, refresh: poll };
}
