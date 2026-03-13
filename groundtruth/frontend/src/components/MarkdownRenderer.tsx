import ReactMarkdown from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`prose-gt ${className}`}>
      <ReactMarkdown
        components={{
          h1: ({ children }) => (
            <h1 className="font-mono text-lg font-bold text-gt-accent mb-3 mt-4 tracking-tight">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="font-mono text-base font-semibold text-gt-text mb-2 mt-4 uppercase tracking-wider">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="font-mono text-sm font-semibold text-gt-accent/80 mb-1 mt-3">{children}</h3>
          ),
          p: ({ children }) => (
            <p className="text-sm text-gt-text font-sans leading-relaxed mb-3">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="list-none space-y-1 mb-3 pl-2">{children}</ul>
          ),
          li: ({ children }) => (
            <li className="text-sm text-gt-text font-sans flex gap-2 before:content-['▸'] before:text-gt-accent before:flex-shrink-0">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-gt-accent">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-gt-muted">{children}</em>
          ),
          code: ({ children }) => (
            <code className="font-mono text-xs bg-gt-surface2 text-gt-accent px-1 py-0.5 rounded">{children}</code>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-gt-accent pl-3 my-2 text-gt-muted italic">{children}</blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
