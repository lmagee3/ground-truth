import { useState } from 'react';
import type { Depth } from '../types/api';

interface SearchBarProps {
  onSearch: (query: string, depth: Depth) => void;
  loading: boolean;
}

const DEPTHS: { value: Depth; label: string; desc: string }[] = [
  { value: 'brief', label: 'Brief', desc: '~30s' },
  { value: 'standard', label: 'Standard', desc: '~60s' },
  { value: 'comprehensive', label: 'Comprehensive', desc: '~90s' },
];

const EXAMPLES = [
  'South China Sea tensions',
  'Ukraine war background',
  'Iran nuclear program',
  'NATO expansion history',
  'Gaza conflict context',
];

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [depth, setDepth] = useState<Depth>('standard');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) onSearch(query.trim(), depth);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div className="flex gap-2">
          <input
            id="gt-search"
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Enter country, conflict, or geopolitical topic..."
            disabled={loading}
            className="
              flex-1 bg-gt-surface2 border border-gt-border rounded
              px-4 py-3 text-gt-text placeholder-gt-muted font-sans text-sm
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
              px-6 py-3 bg-gt-accent text-gt-bg font-mono font-semibold text-sm rounded
              hover:bg-gt-accent-dim transition-colors
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

        {/* Depth selector */}
        <div className="flex items-center gap-2">
          <span className="text-gt-muted font-mono text-xs uppercase tracking-widest">Depth:</span>
          <div className="flex gap-1">
            {DEPTHS.map(d => (
              <button
                key={d.value}
                type="button"
                onClick={() => setDepth(d.value)}
                className={`
                  px-3 py-1 rounded font-mono text-xs transition-colors
                  ${depth === d.value
                    ? 'bg-gt-accent text-gt-bg'
                    : 'bg-gt-surface2 text-gt-muted border border-gt-border hover:border-gt-accent/50'
                  }
                `}
              >
                {d.label} <span className="opacity-60">{d.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Example queries */}
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-gt-muted font-mono text-xs uppercase tracking-widest">Examples:</span>
          {EXAMPLES.map(ex => (
            <button
              key={ex}
              type="button"
              onClick={() => setQuery(ex)}
              className="text-xs text-gt-muted hover:text-gt-accent font-sans transition-colors underline underline-offset-2 decoration-gt-border hover:decoration-gt-accent"
            >
              {ex}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
