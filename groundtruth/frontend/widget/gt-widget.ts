/**
 * Ground Truth Embeddable Widget
 *
 * Drop on any page:
 *   <div id="groundtruth-widget" data-query="ukraine" data-depth="brief"></div>
 *   <script src="https://gt.chaosmonk.dev/widget/gt-widget.js"></script>
 *
 * Attributes:
 *   data-query     Required. The geopolitical query.
 *   data-depth     Optional. "brief" | "standard" | "comprehensive". Default: "brief".
 *   data-api-url   Optional. Override API base URL.
 *   data-theme     Optional. "dark" | "light". Default: "dark".
 *   data-app-url   Optional. Override full briefing link base URL.
 */

interface GTReport {
  title?: string;
  summary?: string;
  current_assessment?: string;
  sources_cited?: string[];
  confidence_notes?: string;
}

interface GTContext {
  report?: GTReport;
  sources_available?: Record<string, { status: string; records?: number }>;
}

(function () {
  const WIDGET_VERSION = '0.1.0';

  const STYLES_DARK = `
    .gt-widget { font-family: Inter, system-ui, sans-serif; background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 16px; color: #e5e7eb; max-width: 600px; }
    .gt-widget--light { background: #f9fafb; border-color: #e5e7eb; color: #111827; }
    .gt-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
    .gt-badge { font-family: 'JetBrains Mono', monospace; font-size: 10px; background: #10b981; color: #0a0f1a; padding: 2px 6px; border-radius: 3px; font-weight: 600; letter-spacing: 0.05em; }
    .gt-title { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; margin: 0 0 8px; color: #e5e7eb; line-height: 1.4; }
    .gt-title--light { color: #111827; }
    .gt-summary { font-size: 13px; line-height: 1.6; color: #9ca3af; margin: 0 0 12px; }
    .gt-summary--light { color: #4b5563; }
    .gt-sources { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .gt-source { font-family: monospace; font-size: 10px; padding: 2px 6px; border: 1px solid #1f2937; border-radius: 3px; color: #6b7280; }
    .gt-source--used { border-color: #10b981; color: #10b981; }
    .gt-footer { display: flex; align-items: center; justify-content: space-between; padding-top: 10px; border-top: 1px solid #1f2937; }
    .gt-footer--light { border-top-color: #e5e7eb; }
    .gt-link { font-family: monospace; font-size: 10px; color: #10b981; text-decoration: none; }
    .gt-link:hover { text-decoration: underline; }
    .gt-spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid #1f2937; border-top-color: #10b981; border-radius: 50%; animation: gt-spin 0.8s linear infinite; }
    @keyframes gt-spin { to { transform: rotate(360deg); } }
    .gt-error { color: #ef4444; font-size: 12px; font-family: monospace; }
    .gt-confidence { font-size: 11px; color: #f59e0b; margin-bottom: 8px; }
  `;

  function injectStyles(): void {
    if (document.getElementById('gt-widget-styles')) return;
    const style = document.createElement('style');
    style.id = 'gt-widget-styles';
    style.textContent = STYLES_DARK;
    document.head.appendChild(style);
  }

  function renderWidget(el: HTMLElement, data: GTContext | null, error: string | null, theme: string): void {
    const isLight = theme === 'light';
    const apiUrl = el.dataset.apiUrl ?? 'http://localhost:8000';
    const appUrl = el.dataset.appUrl ?? 'https://gt.chaosmonk.dev';
    const query = el.dataset.query ?? '';

    if (error) {
      el.innerHTML = `<div class="gt-widget${isLight ? ' gt-widget--light' : ''}"><p class="gt-error">Ground Truth: ${error}</p></div>`;
      return;
    }

    if (!data) {
      el.innerHTML = `<div class="gt-widget${isLight ? ' gt-widget--light' : ''}">
        <div class="gt-header"><div class="gt-spinner"></div><span style="font-size:12px;color:#6b7280;font-family:monospace;">Loading briefing…</span></div>
      </div>`;
      return;
    }

    const report = data.report ?? {};
    const sources = data.sources_available ?? {};
    const usedSources = Object.entries(sources)
      .filter(([, v]) => v.status === 'used')
      .map(([k]) => k);
    const skippedSources = Object.entries(sources)
      .filter(([, v]) => v.status !== 'used')
      .map(([k]) => k);

    const sourceHtml = [
      ...usedSources.map(s => `<span class="gt-source gt-source--used">${s}</span>`),
      ...skippedSources.map(s => `<span class="gt-source">${s}</span>`),
    ].join('');

    el.innerHTML = `
      <div class="gt-widget${isLight ? ' gt-widget--light' : ''}">
        <div class="gt-header">
          <span class="gt-badge">GROUND TRUTH v${WIDGET_VERSION}</span>
        </div>
        <h3 class="gt-title${isLight ? ' gt-title--light' : ''}">${report.title ?? query}</h3>
        ${report.confidence_notes ? `<p class="gt-confidence">⚠ ${report.confidence_notes}</p>` : ''}
        <p class="gt-summary${isLight ? ' gt-summary--light' : ''}">${report.summary ?? 'No summary available.'}</p>
        ${sourceHtml ? `<div class="gt-sources">${sourceHtml}</div>` : ''}
        <div class="gt-footer${isLight ? ' gt-footer--light' : ''}">
          <span style="font-family:monospace;font-size:10px;color:#6b7280;">Sources: ${usedSources.length}/${Object.keys(sources).length} active</span>
          <a class="gt-link" href="${appUrl}/context/${encodeURIComponent(query)}" target="_blank" rel="noreferrer">Full briefing ↗</a>
        </div>
      </div>
    `;

    // Emit custom event for host page integration
    el.dispatchEvent(new CustomEvent('gt:briefing-loaded', { bubbles: true, detail: data }));
  }

  async function initWidget(el: HTMLElement): Promise<void> {
    const query = el.dataset.query;
    if (!query) {
      el.innerHTML = '<p style="color:#ef4444;font-family:monospace;font-size:12px;">gt-widget: data-query attribute required</p>';
      return;
    }

    const apiUrl = el.dataset.apiUrl ?? 'http://localhost:8000';
    const depth = el.dataset.depth ?? 'brief';
    const theme = el.dataset.theme ?? 'dark';

    renderWidget(el, null, null, theme); // loading state

    try {
      const res = await fetch(`${apiUrl}/v1/context/${encodeURIComponent(query)}?depth=${depth}`);
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json() as GTContext;
      renderWidget(el, data, null, theme);
    } catch (err) {
      renderWidget(el, null, err instanceof Error ? err.message : 'Unknown error', theme);
    }
  }

  function bootstrap(): void {
    injectStyles();
    document.querySelectorAll<HTMLElement>('[id^="groundtruth-widget"], .gt-widget-embed').forEach(el => {
      void initWidget(el);
    });

    // Expose API for host pages
    (window as unknown as Record<string, unknown>).GroundTruthWidget = { init: initWidget, version: WIDGET_VERSION };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
