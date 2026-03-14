import type { ReactNode } from 'react';

import type { BriefingReport } from '../types/api';
import { TimelineView } from './TimelineView';

interface BriefingPanelProps {
  report: BriefingReport;
  loading?: boolean;
}

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="gt-card mb-4">
      <h3 className="gt-section-title">
        <span className="text-base">◉</span> {title}
      </h3>
      <div className="gt-body-copy">{children}</div>
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
        <SkeletonBlock lines={4} />
        <SkeletonBlock lines={6} />
        <SkeletonBlock lines={5} />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl text-gt-text mb-2 tracking-[1px] uppercase">{report.title}</h1>
      {report.confidence_notes && (
        <div className="gt-note-box mb-4 text-sm">⚠ {report.confidence_notes}</div>
      )}

      <SectionCard title="Executive Summary">{report.summary}</SectionCard>
      <SectionCard title="Background">{report.background}</SectionCard>

      {report.timeline?.length > 0 && (
        <SectionCard title="Timeline">
          <TimelineView events={report.timeline} />
        </SectionCard>
      )}

      {report.economic_context && (
        <SectionCard title="Economic Context">{report.economic_context}</SectionCard>
      )}

      {report.military_context && (
        <SectionCard title="Military Context">{report.military_context}</SectionCard>
      )}

      {report.perspectives?.length > 0 && (
        <SectionCard title="Interpretive Frameworks">
          <div className="space-y-3">
            {report.perspectives.map((perspective, index) => (
              <div key={index} className="border-l-2 border-gt-accent/50 pl-3">
                <div className="text-gt-accent text-xs uppercase tracking-[1px] mb-1">
                  {perspective.framework}
                </div>
                <div className="gt-body-copy mb-1">{perspective.argument}</div>
                {perspective.evidence && (
                  <div className="text-xs text-gt-blue">{perspective.evidence}</div>
                )}
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      <SectionCard title="Current Assessment">{report.current_assessment}</SectionCard>

      {report.sources_cited?.length > 0 && (
        <SectionCard title="Sources Cited">
          <div className="flex flex-wrap gap-2">
            {report.sources_cited.map((source, index) => (
              <span
                key={index}
                className="px-2 py-1 border border-gt-border rounded text-xs text-gt-muted"
              >
                {source}
              </span>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
