import { useState, useCallback } from 'react';
import { fetchContext, fetchContextStream, type ProgressEvent } from '../api/client';
import type { ContextResponse, Depth } from '../types/api';

export interface UseContextResult {
  data: ContextResponse | null;
  loading: boolean;
  error: string | null;
  progress: ProgressEvent | null;
  query: (q: string, depth?: Depth, provider?: string) => Promise<void>;
  reset: () => void;
}

export function useContext(): UseContextResult {
  const [data, setData] = useState<ContextResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);

  const query = useCallback(async (q: string, depth: Depth = 'standard', provider?: string) => {
    setLoading(true);
    setError(null);
    setProgress(null);
    try {
      let result: ContextResponse;
      try {
        result = await fetchContextStream(q, depth, provider, (event) => {
          setProgress(event);
        });
      } catch {
        result = await fetchContext(q, depth, provider);
      }
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch context';
      setError(_humanizeContextError(message));
    } finally {
      setLoading(false);
      setProgress(null);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setProgress(null);
  }, []);

  return { data, loading, error, progress, query, reset };
}

function _humanizeContextError(raw: string): string {
  const message = raw.toLowerCase();
  if (message.includes('connecterror') || message.includes('connection refused')) {
    return 'Local AI (Ollama) is not running. Start it with: `ollama serve`';
  }
  if (message.includes('not found') && message.includes('model')) {
    const modelMatch = raw.match(/model ([^:]+):/i);
    const model = modelMatch?.[1] ?? 'your model';
    return `Model '${model}' not found. Pull it with: \`ollama pull ${model}\``;
  }
  if (message.includes('timeout') || message.includes('timed out')) {
    return 'Synthesis timed out after 5 minutes. Try Brief depth for faster results.';
  }
  return raw;
}
