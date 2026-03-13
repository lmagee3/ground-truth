import { useState, useCallback } from 'react';
import { fetchContext } from '../api/client';
import type { ContextResponse, Depth } from '../types/api';

export interface UseContextResult {
  data: ContextResponse | null;
  loading: boolean;
  error: string | null;
  query: (q: string, depth?: Depth, provider?: string) => Promise<void>;
  reset: () => void;
}

export function useContext(): UseContextResult {
  const [data, setData] = useState<ContextResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useCallback(async (q: string, depth: Depth = 'standard', provider?: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchContext(q, depth, provider);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch context');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, query, reset };
}
