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
