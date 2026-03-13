import { useState } from 'react';
import { useCompare } from '../hooks/useCompare';
import type { SourceInfo } from '../types/api';
import { SourceStatus } from './SourceStatus';

interface CompareViewProps {
  defaultProvider?: string;
}

export function CompareView({ defaultProvider }: CompareViewProps) {
  const [eventA, setEventA] = useState('');
  const [eventB, setEventB] = useState('');
  const { data, loading, error, compare, reset } = useCompare();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (eventA.trim() && eventB.trim()) {
      compare(eventA.trim(), eventB.trim(), defaultProvider);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          id="gt-compare-a"
          type="text"
          value={eventA}
          onChange={e => setEventA(e.target.value)}
          placeholder="Event A (e.g. ukraine war)"
          disabled={loading}
          className="flex-1 bg-gt-surface2 border border-gt-border rounded px-3 py-2 text-gt-text text-sm font-sans focus:outline-none focus:border-gt-accent disabled:opacity-50"
        />
        <span className="self-center font-mono text-gt-muted text-sm">vs</span>
        <input
          id="gt-compare-b"
          type="text"
          value={eventB}
          onChange={e => setEventB(e.target.value)}
          placeholder="Event B (e.g. korea war)"
          disabled={loading}
          className="flex-1 bg-gt-surface2 border border-gt-border rounded px-3 py-2 text-gt-text text-sm font-sans focus:outline-none focus:border-gt-accent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!eventA.trim() || !eventB.trim() || loading}
          id="gt-compare-btn"
          className="px-4 py-2 bg-gt-accent text-gt-bg font-mono text-xs font-semibold rounded hover:bg-gt-accent-dim transition-colors disabled:opacity-40 flex items-center gap-2"
        >
          {loading ? (
            <><span className="inline-block w-3 h-3 border-2 border-gt-bg border-t-transparent rounded-full animate-spin" />COMPARING</>
          ) : 'COMPARE'}
        </button>
        {data && (
          <button type="button" onClick={reset} className="px-3 py-2 border border-gt-border text-gt-muted font-mono text-xs rounded hover:border-gt-accent/50 transition-colors">
            CLEAR
          </button>
        )}
      </form>

      {error && (
        <p className="text-gt-danger font-mono text-xs">Error: {error}</p>
      )}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Parallels */}
          <div className="bg-gt-surface rounded border border-gt-border p-4">
            <h3 className="font-mono text-xs uppercase tracking-widest text-gt-accent mb-3">Parallels</h3>
            <ul className="space-y-2">
              {(data.comparison.parallels ?? []).map((p, i) => (
                <li key={i} className="text-sm text-gt-text font-sans leading-relaxed flex gap-2">
                  <span className="text-gt-accent flex-shrink-0">▸</span>
                  {p}
                </li>
              ))}
            </ul>
          </div>

          {/* Assessment */}
          <div className="bg-gt-surface rounded border border-gt-accent/30 p-4">
            <h3 className="font-mono text-xs uppercase tracking-widest text-gt-accent mb-3">Assessment</h3>
            <p className="text-sm text-gt-text font-sans leading-relaxed">
              {data.comparison.assessment}
            </p>
          </div>

          {/* Differences */}
          <div className="bg-gt-surface rounded border border-gt-border p-4">
            <h3 className="font-mono text-xs uppercase tracking-widest text-gt-accent mb-3">Differences</h3>
            <ul className="space-y-2">
              {(data.comparison.differences ?? []).map((d, i) => (
                <li key={i} className="text-sm text-gt-text font-sans leading-relaxed flex gap-2">
                  <span className="text-gt-warn flex-shrink-0">▸</span>
                  {d}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {data?.sources_available && (
        <div className="mt-2 p-3 bg-gt-surface rounded border border-gt-border">
          <SourceStatus sources={data.sources_available as Record<string, SourceInfo>} />
        </div>
      )}
    </div>
  );
}
