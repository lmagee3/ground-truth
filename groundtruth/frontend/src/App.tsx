import { useState } from 'react';

import { BriefingPanel } from './components/BriefingPanel';
import { CompareView } from './components/CompareView';
import { SearchBar } from './components/SearchBar';
import { SourceStatus } from './components/SourceStatus';
import { useContext as useGTContext } from './hooks/useContext';
import './styles/globals.css';
import type { Depth } from './types/api';

type ActiveTab = 'briefing' | 'compare';

const TABS: { id: ActiveTab; label: string }[] = [
  { id: 'briefing', label: 'INTEL BRIEFING' },
  { id: 'compare', label: 'COMPARE CASES' },
];

export function App() {
  const [tab, setTab] = useState<ActiveTab>('briefing');
  const { data, loading, error, query } = useGTContext();

  const handleSearch = (q: string, depth: Depth) => {
    query(q, depth);
  };

  return (
    <div className="min-h-screen bg-gt-bg text-gt-text font-mono">
      <header className="text-center py-10 px-5 border-b border-gt-border">
        <h1 className="text-4xl font-bold text-gt-accent tracking-[4px] uppercase mb-2">GROUND TRUTH</h1>
        <div className="text-gt-muted text-sm tracking-[2px] uppercase">
          Geopolitical Context Engine — By Chaos Monk
        </div>
        <div className="text-gt-warn text-base mt-3 italic">
          "The intelligence briefing behind the radar blip"
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-5 py-8">
        <div className="gt-card mb-8">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>

        <div className="flex gap-1 flex-wrap mb-8">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`
                bg-gt-surface2 border border-gt-border text-gt-muted
                px-5 py-2.5 font-mono text-xs tracking-[1px] rounded
                transition-all cursor-pointer
                ${
                  tab === t.id
                    ? 'bg-[#00ff8815] border-gt-accent text-gt-accent'
                    : 'hover:border-gt-accent hover:text-gt-accent'
                }
              `}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'briefing' ? (
          <div className="grid grid-cols-1 xl:grid-cols-[1fr_330px] gap-6">
            <section className="gt-card">
              {error && (
                <div className="gt-note-box mb-4 text-sm">
                  Error: {error}
                </div>
              )}

              {!data && !loading && !error && (
                <div className="text-center py-16">
                  <div className="text-gt-accent text-4xl mb-3">◉</div>
                  <p className="text-gt-muted text-sm uppercase tracking-[1px]">No briefing loaded</p>
                  <p className="gt-body-copy mt-2">
                    Enter a query to generate a multi-source geopolitical context briefing.
                  </p>
                </div>
              )}

              {(loading || data) && (
                <BriefingPanel
                  report={
                    data?.report ?? {
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
                    }
                  }
                  loading={loading}
                />
              )}
            </section>

            <aside className="space-y-5">
              <div className="gt-card">
                {data?.sources_available ? (
                  <SourceStatus sources={data.sources_available} />
                ) : (
                  <p className="gt-body-copy">Run a query to view source contribution status.</p>
                )}
              </div>

              {data && (
                <div className="gt-card">
                  <div className="gt-section-title text-sm">◉ Query Metadata</div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gt-muted">Topic</span>
                      <span className="text-gt-text">{data.query}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gt-muted">Depth</span>
                      <span className="text-gt-accent uppercase">{data.depth}</span>
                    </div>
                    {data.country?.name && (
                      <div className="flex justify-between">
                        <span className="text-gt-muted">Primary</span>
                        <span className="text-gt-text">{data.country.name}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </aside>
          </div>
        ) : (
          <div className="gt-card">
            <CompareView />
          </div>
        )}
      </main>

      <footer className="border-t border-gt-border py-4 px-5 text-center text-xs text-gt-muted tracking-[1px] uppercase">
        Ground Truth · Primary Sources Only · MIT
      </footer>
    </div>
  );
}
