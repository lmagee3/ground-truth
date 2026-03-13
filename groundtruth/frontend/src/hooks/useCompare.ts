import { useState, useCallback } from 'react';
import { fetchComparison } from '../api/client';
import type { ComparisonResponse } from '../types/api';

export interface UseCompareResult {
  data: ComparisonResponse | null;
  loading: boolean;
  error: string | null;
  compare: (eventA: string, eventB: string, provider?: string) => Promise<void>;
  reset: () => void;
}

export function useCompare(): UseCompareResult {
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const compare = useCallback(async (eventA: string, eventB: string, provider?: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchComparison(eventA, eventB, provider);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch comparison');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, compare, reset };
}
