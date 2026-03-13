import type { BriefingReport } from '../types/api';
import { TimelineView } from './TimelineView';

interface BriefingPanelProps {
  report: BriefingReport;
  loading?: boolean;
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <h2 className="font-mono text-xs uppercase tracking-widest text-gt-accent border-b border-gt-border pb-1 mb-3">
        {label}
      </h2>
      {children}
    </div>
  );
}

function SkeletonBlock({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 bg-gt-surface2 rounded animate-pulse-slow"
          style={{ width: `${85 - i * 10}%` }}
        />
      ))}
    </div>
  );
}

export function BriefingPanel({ report, loading = false }: BriefingPanelProps) {
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 bg-gt-surface2 rounded animate-pulse-slow w-2/3" />
        <SkeletonBlock lines={3} />
        <SkeletonBlock lines={5} />
        <SkeletonBlock lines={4} />
      </div>
    );
  }

  return (
    <div>
      {/* Title + Summary */}
      <h1 className="font-mono text-xl font-bold text-gt-text mb-1 leading-tight">
        {report.title}
      </h1>
      {report.confidence_notes && (
        <p className="text-xs text-gt-warn font-mono mb-4 leading-relaxed">
          ⚠ {report.confidence_notes}
        </p>
      )}

      <Section label="Executive Summary">
        <p className="text-sm text-gt-text font-sans leading-relaxed">{report.summary}</p>
      </Section>

      <Section label="Background">
        <p className="text-sm text-gt-text font-sans leading-relaxed">{report.background}</p>
      </Section>

      {report.timeline?.length > 0 && (
        <Section label="Timeline">
          <TimelineView events={report.timeline} />
        </Section>
      )}

      {report.economic_context && (
        <Section label="Economic Context">
          <p className="text-sm text-gt-text font-sans leading-relaxed">{report.economic_context}</p>
        </Section>
      )}

      {report.military_context && (
        <Section label="Military Context">
          <p className="text-sm text-gt-text font-sans leading-relaxed">{report.military_context}</p>
        </Section>
      )}

      {report.perspectives?.length > 0 && (
        <Section label="Interpretive Frameworks">
          <div className="space-y-4">
            {report.perspectives.map((p, i) => (
              <div key={i} className="border-l-2 border-gt-accent/40 pl-3">
                <h3 className="font-mono text-xs text-gt-accent font-semibold mb-1 uppercase tracking-wide">
                  {p.framework}
                </h3>
                <p className="text-sm text-gt-text font-sans leading-relaxed mb-1">{p.argument}</p>
                {p.evidence && (
                  <p className="text-xs text-gt-muted font-mono">{p.evidence}</p>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      <Section label="Current Assessment">
        <p className="text-sm text-gt-text font-sans leading-relaxed">{report.current_assessment}</p>
      </Section>

      {report.sources_cited?.length > 0 && (
        <Section label="Sources Cited">
          <div className="flex flex-wrap gap-2">
            {report.sources_cited.map((s, i) => (
              <span
                key={i}
                className="px-2 py-0.5 border border-gt-border text-gt-muted font-mono text-xs rounded"
              >
                {s}
              </span>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}
