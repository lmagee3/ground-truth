import type {
  ContextResponse,
  BriefingResponse,
  ComparisonResponse,
  HealthResponse,
  CountryResponse,
  GeoJSONCollection,
  QueryParseResponse,
  Depth,
  BriefingFormat,
} from '../types/api';

const API_BASE = (import.meta as unknown as { env: Record<string, string> }).env?.VITE_GT_API_URL ?? 'http://localhost:8000';

async function request<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => v && url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`GT API error ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

export async function fetchContext(
  query: string,
  depth: Depth = 'standard',
  provider?: string,
): Promise<ContextResponse> {
  return request<ContextResponse>(`/v1/context/${encodeURIComponent(query)}`, {
    depth,
    ...(provider ? { provider } : {}),
  });
}

export interface ProgressEvent {
  stage: string;
  message: string;
  percent: number;
}

export async function fetchContextStream(
  query: string,
  depth: Depth = 'standard',
  provider?: string,
  onProgress?: (event: ProgressEvent) => void,
): Promise<ContextResponse> {
  const url = new URL(`${API_BASE}/v1/context/${encodeURIComponent(query)}/stream`);
  url.searchParams.set('depth', depth);
  if (provider) {
    url.searchParams.set('provider', provider);
  }

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`GT API error ${res.status}: ${res.statusText}`);
  }

  const body = res.body;
  if (!body) {
    throw new Error('Stream response body unavailable');
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result: ContextResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';

    for (const frame of frames) {
      const lines = frame.split('\n');
      let eventType = 'message';
      const dataLines: string[] = [];

      for (const line of lines) {
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim();
        }
        if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trim());
        }
      }

      if (dataLines.length === 0) continue;
      const payload = JSON.parse(dataLines.join('\n'));

      if (eventType === 'progress' && onProgress) {
        onProgress(payload as ProgressEvent);
      } else if (eventType === 'result') {
        result = payload as ContextResponse;
      } else if (eventType === 'error') {
        throw new Error(String((payload as { detail?: string }).detail ?? 'Stream error'));
      }
    }
  }

  if (!result) {
    throw new Error('Stream ended without result');
  }
  return result;
}

export async function fetchBriefing(
  topic: string,
  format: BriefingFormat = 'full',
  provider?: string,
): Promise<BriefingResponse> {
  return request<BriefingResponse>(`/v1/briefing/${encodeURIComponent(topic)}`, {
    format,
    ...(provider ? { provider } : {}),
  });
}

export async function fetchComparison(
  eventA: string,
  eventB: string,
  provider?: string,
): Promise<ComparisonResponse> {
  return request<ComparisonResponse>(
    `/v1/compare/${encodeURIComponent(eventA)}/${encodeURIComponent(eventB)}`,
    provider ? { provider } : {},
  );
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/v1/health');
}

export async function fetchCountry(iso: string): Promise<CountryResponse> {
  return request<CountryResponse>(`/v1/country/${iso.toUpperCase()}`);
}

export async function fetchGeoJSON(iso: string, days = 30): Promise<GeoJSONCollection> {
  return request<GeoJSONCollection>(`/v1/events/${iso.toUpperCase()}.geojson`, {
    days: String(days),
  });
}

export async function fetchQueryParse(query: string): Promise<QueryParseResponse> {
  return request<QueryParseResponse>(`/v1/parse/${encodeURIComponent(query)}`);
}
