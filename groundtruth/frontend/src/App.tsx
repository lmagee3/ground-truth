import { useState } from 'react';
import type { Depth } from './types/api';
import { useContext as useGTContext } from './hooks/useContext';
import { SearchBar } from './components/SearchBar';
import { BriefingPanel } from './components/BriefingPanel';
import { SourceStatus } from './components/SourceStatus';
import { CompareView } from './components/CompareView';
import './styles/globals.css';

type ActiveTab = 'briefing' | 'compare';

export function App() {
  const [tab, setTab] = useState<ActiveTab>('briefing');
  const { data, loading, error, query } = useGTContext();

  const handleSearch = (q: string, depth: Depth) => {
    query(q, depth);
  };

  return (
    <div className="min-h-screen bg-gt-bg flex flex-col">
      {/* Header */}
      <header className="border-b border-gt-border bg-gt-surface/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-mono text-lg font-bold text-gt-accent tracking-tight">GROUND TRUTH</span>
            <span className="hidden sm:inline text-gt-border">|</span>
            <span className="hidden sm:inline font-sans text-xs text-gt-muted">
              Geopolitical Context Engine
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-gt-muted">
              Primary sources only — no spin
            </span>
            <a
              href="https://github.com/lmagee3/ground-truth"
              target="_blank"
              rel="noreferrer"
              className="font-mono text-xs text-gt-muted hover:text-gt-accent transition-colors"
            >
              [GitHub]
            </a>
          </div>
        </div>
      </header>

      {/* Search */}
      <div className="border-b border-gt-border bg-gt-surface/40 px-4 py-4">
        <div className="max-w-7xl mx-auto">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>
      </div>

      {/* Tab nav */}
      <div className="border-b border-gt-border">
        <div className="max-w-7xl mx-auto px-4 flex gap-1 pt-2">
          {(['briefing', 'compare'] as ActiveTab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`
                px-4 py-2 font-mono text-xs uppercase tracking-widest transition-colors
                border-b-2 -mb-px
                ${tab === t
                  ? 'border-gt-accent text-gt-accent'
                  : 'border-transparent text-gt-muted hover:text-gt-text'
                }
              `}
            >
              {t === 'briefing' ? '01 / BRIEFING' : '02 / COMPARE'}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {tab === 'briefing' ? (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
            {/* Briefing pane */}
            <div className="bg-gt-surface rounded border border-gt-border p-6 min-h-[400px]">
              {error && (
                <div className="p-3 bg-gt-danger/10 border border-gt-danger/30 rounded mb-4">
                  <p className="text-gt-danger font-mono text-xs">Error: {error}</p>
                </div>
              )}

              {!data && !loading && !error && (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <div className="font-mono text-4xl text-gt-border mb-4">⊕</div>
                  <p className="font-mono text-sm text-gt-muted mb-2">No briefing loaded</p>
                  <p className="text-xs text-gt-muted/60 font-sans max-w-sm">
                    Enter a country, conflict, or geopolitical topic above to generate an intelligence briefing from authoritative primary sources.
                  </p>
                </div>
              )}

              {(loading || data) && (
                <BriefingPanel
                  report={data?.report ?? {
                    title: 'Synthesizing briefing...',
                    summary: '',
                    background: '',
                    timeline: [],
                    economic_context: '',
                    military_context: '',
                    perspectives: [],
                    current_assessment: '',
                    sources_cited: [],
                    confidence_notes: '',
                  }}
                  loading={loading}
                />
              )}
            </div>

            {/* Sidebar */}
            <div className="flex flex-col gap-4">
              {/* Source status */}
              <div className="bg-gt-surface rounded border border-gt-border p-4">
                {data?.sources_available ? (
                  <SourceStatus
                    sources={data.sources_available}
                    provider={data.report?.sources_available
                      ? undefined
                      : 'ollama'}
                  />
                ) : (
                  <div>
                    <span className="font-mono text-xs text-gt-muted uppercase tracking-widest">Sources</span>
                    <p className="text-xs text-gt-muted/60 mt-2 font-sans">Run a briefing to see source contribution.</p>
                  </div>
                )}
              </div>

              {/* Depth / metadata */}
              {data && (
                <div className="bg-gt-surface rounded border border-gt-border p-4">
                  <span className="font-mono text-xs text-gt-muted uppercase tracking-widest">Query</span>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between">
                      <span className="font-mono text-xs text-gt-muted">Topic</span>
                      <span className="font-mono text-xs text-gt-text">{data.query}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-mono text-xs text-gt-muted">Depth</span>
                      <span className="font-mono text-xs text-gt-accent">{data.depth}</span>
                    </div>
                    {data.country?.name && (
                      <div className="flex justify-between">
                        <span className="font-mono text-xs text-gt-muted">Country</span>
                        <span className="font-mono text-xs text-gt-text">{data.country.name}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Mission statement */}
              <div className="bg-gt-surface/50 rounded border border-gt-border/50 p-4">
                <p className="text-xs text-gt-muted/70 font-sans leading-relaxed">
                  Ground Truth generates intelligence briefings from authoritative primary sources only.
                  No editorial spin. No Wikipedia. Multiple interpretive frameworks.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gt-surface rounded border border-gt-border p-6">
            <CompareView />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gt-border py-4 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span className="font-mono text-xs text-gt-muted">
            Ground Truth — Chaos Monk / MAGE Software
          </span>
          <span className="font-mono text-xs text-gt-muted">
            MIT Licensed · Primary Sources Only
          </span>
        </div>
      </footer>
    </div>
  );
}
