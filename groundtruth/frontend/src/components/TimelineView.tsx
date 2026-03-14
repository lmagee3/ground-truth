import type { TimelineEvent } from '../types/api';

interface TimelineViewProps {
  events: TimelineEvent[];
}

const SOURCE_COLORS: Record<string, string> = {
  GDELT: 'text-[#00ccff]',
  ACLED: 'text-gt-warn',
  'World Bank': 'text-gt-accent',
  'CIA Factbook': 'text-gt-purple',
  SIPRI: 'text-gt-danger',
  FAS: 'text-[#ffaa00]',
};

export function TimelineView({ events }: TimelineViewProps) {
  if (!events || events.length === 0) {
    return <p className="gt-body-copy italic">No timeline events available.</p>;
  }

  const sorted = [...events].sort((a, b) => a.year - b.year);

  return (
    <div className="gt-timeline">
      {sorted.map((event, index) => (
        <div key={index} className="gt-timeline-item">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-gt-accent text-xs font-semibold">{event.year}</span>
            <span className={`text-xs ${SOURCE_COLORS[event.source] ?? 'text-gt-muted'}`}>
              [{event.source}]
            </span>
          </div>
          <p className="gt-body-copy">{event.event}</p>
        </div>
      ))}
    </div>
  );
}
