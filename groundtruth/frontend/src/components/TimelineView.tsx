import type { TimelineEvent } from '../types/api';

interface TimelineViewProps {
  events: TimelineEvent[];
}

const SOURCE_COLORS: Record<string, string> = {
  GDELT: 'text-blue-400',
  ACLED: 'text-orange-400',
  'World Bank': 'text-gt-accent',
  'CIA Factbook': 'text-purple-400',
  SIPRI: 'text-red-400',
  FAS: 'text-yellow-400',
};

export function TimelineView({ events }: TimelineViewProps) {
  if (!events || events.length === 0) {
    return (
      <p className="text-gt-muted text-sm font-sans italic">No timeline events available.</p>
    );
  }

  const sorted = [...events].sort((a, b) => a.year - b.year);

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-[5px] top-2 bottom-2 w-px bg-gt-border" />

      <div className="flex flex-col gap-4">
        {sorted.map((ev, i) => (
          <div key={i} className="flex gap-4 pl-6 relative">
            {/* Dot */}
            <div className="absolute left-0 top-1.5 w-3 h-3 rounded-full border-2 border-gt-accent bg-gt-bg" />

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-mono text-xs text-gt-accent font-semibold">{ev.year}</span>
                <span className={`font-mono text-xs ${SOURCE_COLORS[ev.source] ?? 'text-gt-muted'}`}>
                  [{ev.source}]
                </span>
              </div>
              <p className="text-sm text-gt-text font-sans leading-relaxed">{ev.event}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
