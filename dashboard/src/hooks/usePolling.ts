import { useState, useEffect, useRef, useCallback } from "react";

export function usePolling<T>(
  fetcher: () => Promise<T>,
  interval: number,
  initialValue: T,
): { data: T; isLive: boolean } {
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

  return { data, isLive };
}
