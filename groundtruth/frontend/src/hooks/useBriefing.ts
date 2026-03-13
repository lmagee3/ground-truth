import { useState, useCallback } from 'react';
import { fetchBriefing } from '../api/client';
import type { BriefingResponse, BriefingFormat } from '../types/api';

export interface UseBriefingResult {
  data: BriefingResponse | null;
  loading: boolean;
  error: string | null;
  query: (topic: string, format?: BriefingFormat, provider?: string) => Promise<void>;
  reset: () => void;
}

export function useBriefing(): UseBriefingResult {
  const [data, setData] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useCallback(async (topic: string, format: BriefingFormat = 'full', provider?: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchBriefing(topic, format, provider);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch briefing');
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
