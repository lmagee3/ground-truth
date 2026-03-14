// Ground Truth API — TypeScript type definitions
// Mirrors the FastAPI response schemas exactly.

export type Depth = 'brief' | 'standard' | 'comprehensive';
export type BriefingFormat = 'full' | 'summary' | 'executive';
export type SourceStatusValue = 'used' | 'skipped' | 'error';

export interface SourceInfo {
  status: SourceStatusValue;
  records?: number;
  reason?: string | null;
  configured?: boolean;
  loaded?: boolean;
  freshness?: string | null;
}

export interface TimelineEvent {
  year: number;
  event: string;
  source: string;
}

export interface Perspective {
  framework: string;
  argument: string;
  evidence: string;
}

export interface BriefingReport {
  title: string;
  summary: string;
  background: string;
  timeline: TimelineEvent[];
  economic_context: string;
  military_context: string;
  perspectives: Perspective[];
  current_assessment: string;
  sources_cited: string[];
  confidence_notes: string;
  generated_at?: string;
  sources_available?: Record<string, SourceInfo>;
}

export interface ContextResponse {
  query: string;
  depth: Depth;
  region: string | null;
  country: { iso_code: string; name: string } | null;
  report: BriefingReport;
  sources: string[];
  sources_available: Record<string, SourceInfo>;
}

export interface BriefingResponse {
  topic: string;
  format: BriefingFormat;
  report: BriefingReport;
  markdown: string;
  sources_available: Record<string, SourceInfo>;
}

export interface ComparisonResponse {
  event_a: string;
  event_b: string;
  comparison: {
    parallels: string[];
    differences: string[];
    assessment: string;
  };
  sources_available: Record<string, SourceInfo>;
}

export interface HealthSource {
  loaded: boolean;
  freshness?: string;
  configured?: boolean;
}

export interface HealthResponse {
  status: string;
  sources: Record<string, HealthSource>;
  synthesis: { provider: string };
  database: { enabled: boolean };
  checked_at: string;
}

export interface CountryResponse {
  country: { iso_code: string; name: string; region?: string };
  factbook: Record<string, unknown>;
  worldbank: Record<string, unknown[]>;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: { type: 'Point'; coordinates: [number, number] };
  properties: {
    event_type: string;
    date: string;
    description: string;
    source: string;
    actors: string[];
    source_url: string;
  };
}

export interface GeoJSONCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
  metadata: { iso_code: string; days: number; total: number };
}

export interface QueryParseResponse {
  query_type: 'country' | 'bilateral' | 'regional' | 'topical';
  countries: string[];
  region: 'middle-east' | 'europe' | 'asia' | 'africa' | 'americas' | null;
  topic: string;
  time_period: {
    start_year: number;
    end_year: number;
  };
  key_entities: string[];
  suggested_depth: Depth;
}
