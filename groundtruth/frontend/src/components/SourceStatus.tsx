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

const TAG_COLORS: Record<string, string> = {
  used: 'bg-[#00ff8820] text-gt-accent border-[#00ff8840]',
  skipped: 'bg-[#66666620] text-gt-skipped border-[#66666640]',
  error: 'bg-[#ff558820] text-gt-danger border-[#ff558840]',
};

function SourceTag({ status, label }: { status: string | undefined; label: string }) {
  const tone = TAG_COLORS[status ?? 'skipped'] ?? TAG_COLORS.skipped;
  return <span className={`px-2 py-0.5 rounded border text-xs uppercase tracking-[1px] ${tone}`}>{label}</span>;
}

export function SourceStatus({ sources, provider }: SourceStatusProps) {
  const usedCount = Object.values(sources).filter((source) => source.status === 'used').length;
  const totalCount = Object.keys(sources).length;

  return (
    <div>
      <div className="gt-section-title text-sm mb-3">
        <span className="text-base">◉</span> Source Contribution
      </div>

      <div className="text-xs text-gt-muted mb-3">
        {usedCount}/{totalCount} sources contributed
      </div>

      <div className="space-y-2">
        {Object.entries(sources).map(([key, info]) => (
          <div key={key} className="border border-gt-border rounded p-2.5 bg-gt-surface2/40">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm text-gt-text">{SOURCE_LABELS[key] ?? key}</span>
              <SourceTag status={info.status} label={info.status ?? 'skipped'} />
            </div>
            <div className="flex items-center justify-between mt-1 text-xs text-gt-muted">
              <span>{info.reason ?? 'contributed to synthesis'}</span>
              <span>{info.records ?? 0} records</span>
            </div>
          </div>
        ))}
      </div>

      {provider && (
        <div className="mt-3 text-xs text-gt-muted">
          Provider: <span className="text-gt-accent uppercase">{provider}</span>
        </div>
      )}
    </div>
  );
}
