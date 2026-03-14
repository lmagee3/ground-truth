interface ProgressBarProps {
  stage: string;
  message: string;
  percent: number;
}

export function ProgressBar({ stage, message, percent }: ProgressBarProps) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gt-muted mb-1">
        <span className="uppercase tracking-[1px]">{message}</span>
        <span className="text-gt-accent">{percent}%</span>
      </div>
      <div className="w-full h-2 bg-gt-surface2 rounded overflow-hidden">
        <div
          className="h-full bg-gt-accent transition-all duration-500 ease-out rounded"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="mt-1 text-[10px] text-gt-muted uppercase tracking-[1px]">
        {stage.replace(/_/g, ' ')}
      </div>
    </div>
  );
}
