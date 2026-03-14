import { useEffect, useState } from 'react';

import { fetchQueryParse } from '../api/client';
import type { Depth, QueryParseResponse } from '../types/api';

interface SearchBarProps {
  onSearch: (query: string, depth: Depth) => void;
  loading: boolean;
}

const DEPTHS: { value: Depth; label: string; desc: string }[] = [
  { value: 'brief', label: 'Brief', desc: '~30s' },
  { value: 'standard', label: 'Standard', desc: '~60s' },
  { value: 'comprehensive', label: 'Comprehensive', desc: '~90s · Cloud AI' },
];

const EXAMPLES = [
  'South China Sea tensions',
  'Ukraine war background',
  'US-Iran tensions background',
  'NATO expansion history',
  'Gaza conflict context',
];

function formatParsePreview(parsed: QueryParseResponse): string {
  const countries = parsed.countries.length ? parsed.countries.join(' + ') : 'none';
  const span = `${parsed.time_period.start_year}-${parsed.time_period.end_year}`;
  return `${parsed.query_type} | ${countries} | ${span} | ${parsed.suggested_depth}`;
}

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [depth, setDepth] = useState<Depth>('standard');
  const [parsed, setParsed] = useState<QueryParseResponse | null>(null);

  useEffect(() => {
    if (!query.trim()) {
      setParsed(null);
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        const result = await fetchQueryParse(query.trim());
        setParsed(result);
      } catch {
        setParsed(null);
      }
    }, 300);

    return () => window.clearTimeout(timer);
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query.trim(), depth);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div className="flex gap-2">
          <input
            id="gt-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter country, conflict, or geopolitical topic..."
            disabled={loading}
            className="
              flex-1 bg-gt-surface2 border border-gt-border rounded
              px-4 py-3 text-gt-text placeholder-gt-muted font-mono text-sm
              focus:outline-none focus:border-gt-accent focus:ring-1 focus:ring-gt-accent/30
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors
            "
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            id="gt-search-btn"
            className="
              px-6 py-3 bg-gt-accent text-gt-bg font-mono font-semibold text-xs rounded tracking-[1px] uppercase
              hover:bg-[#00dd77] transition-colors
              disabled:opacity-40 disabled:cursor-not-allowed
              flex items-center gap-2
            "
          >
            {loading ? (
              <>
                <span className="inline-block w-3 h-3 border-2 border-gt-bg border-t-transparent rounded-full animate-spin" />
                <span>ANALYZING</span>
              </>
            ) : (
              'RUN BRIEFING'
            )}
          </button>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-gt-muted font-mono text-xs uppercase tracking-[1px]">Depth:</span>
          <div className="flex gap-1 flex-wrap">
            {DEPTHS.map((d) => (
              <button
                key={d.value}
                type="button"
                onClick={() => setDepth(d.value)}
                className={`
                  px-3 py-1 rounded font-mono text-xs transition-colors uppercase tracking-[1px]
                  ${
                    depth === d.value
                      ? 'bg-gt-accent text-gt-bg'
                      : 'bg-gt-surface2 text-gt-muted border border-gt-border hover:border-gt-accent/50'
                  }
                `}
              >
                {d.label} <span className="opacity-60 normal-case">{d.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {depth === 'comprehensive' && (
          <div className="text-[10px] text-gt-warn">
            Best results with Claude API. Set SYNTHESIS_PROVIDER=anthropic in .env
          </div>
        )}

        {parsed && query.trim() && (
          <div className="bg-[#00ff8808] border border-[#00ff8830] rounded px-3 py-2 text-xs">
            <div className="text-gt-accent mb-1">🔍 {query}</div>
            <div className="text-gt-muted">Detected: {formatParsePreview(parsed)}</div>
          </div>
        )}

        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-gt-muted font-mono text-xs uppercase tracking-[1px]">Examples:</span>
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setQuery(example)}
              className="text-xs text-gt-muted hover:text-gt-accent transition-colors underline underline-offset-2 decoration-gt-border hover:decoration-gt-accent"
            >
              {example}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
