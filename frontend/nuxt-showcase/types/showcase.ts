export interface ShowcaseResult {
  id: string;
  title: string;
  summary: string;
  source_url: string | null;
  notion_url: string | null;
  created_at: string;
  processing_duration: number | null;
}

export interface ShowcaseApiResponse {
  items: ShowcaseResult[];
  generated_at: string;
  cache_ttl_seconds: number;
}
