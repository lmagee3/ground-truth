import type { SourceInfo } from '../types/api';

interface SourceStatusProps {
  sources: Record<string, SourceInfo>;
  provider?: string;
}

const SOURCE_LABELS: Record<string, string> = {
  worldbank: 'World Bank',
  cia_factbook: 'CIA Factbook',
  gdelt: 'GDELT',
  acled: 'ACLED',
  sipri: 'SIPRI',
  fas: 'FAS Nuclear',
};

function StatusDot({ status }: { status: string | undefined }) {
  if (status === 'used') return <span className="w-2 h-2 rounded-full bg-gt-accent inline-block" />;
  if (status === 'error') return <span className="w-2 h-2 rounded-full bg-gt-danger inline-block animate-pulse" />;
  return <span className="w-2 h-2 rounded-full bg-gt-skipped inline-block" />;
}

export function SourceStatus({ sources, provider }: SourceStatusProps) {
  const usedCount = Object.values(sources).filter(s => s.status === 'used').length;
  const totalCount = Object.keys(sources).length;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono text-xs text-gt-muted uppercase tracking-widest">Sources</span>
        <span className={`font-mono text-xs ${usedCount === totalCount ? 'text-gt-accent' : 'text-gt-warn'}`}>
          {usedCount}/{totalCount}
        </span>
      </div>

      <div className="flex flex-col gap-1.5">
        {Object.entries(sources).map(([key, info]) => (
          <div key={key} className="flex items-start gap-2 group">
            <StatusDot status={info.status} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-mono ${info.status === 'used' ? 'text-gt-text' : 'text-gt-skipped'}`}>
                  {SOURCE_LABELS[key] ?? key}
                </span>
                {info.records !== undefined && info.records > 0 && (
                  <span className="text-xs text-gt-muted">{info.records.toLocaleString()}</span>
                )}
              </div>
              {info.status !== 'used' && info.reason && (
                <p className="text-xs text-gt-skipped leading-tight mt-0.5">{info.reason}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {provider && (
        <div className="mt-2 pt-2 border-t border-gt-border">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gt-accent/50 inline-block" />
            <span className="text-xs font-mono text-gt-muted">
              Provider: <span className="text-gt-accent">{provider}</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
