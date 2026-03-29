import type { ShowcaseApiResponse, ShowcaseResult } from "../../types/showcase";

export const DEFAULT_CACHE_TTL_SECONDS = 3600;
export const MAX_SHOWCASE_RESULTS = 100;
export const NOTION_VERSION = "2022-06-28";

interface NotionRichTextItem {
  plain_text?: string;
  text?: {
    content?: string;
  };
}

interface NotionPageProperty {
  type?: string;
  title?: NotionRichTextItem[];
  rich_text?: NotionRichTextItem[];
  url?: string | null;
  number?: number | null;
  select?: {
    name?: string;
  } | null;
}

export interface NotionPage {
  id: string;
  created_time: string;
  properties: Record<string, NotionPageProperty>;
}

interface FetchNotionResultsOptions {
  apiKey: string;
  databaseId: string;
  notionBaseUrl: string;
  cacheTtlSeconds?: number;
  fetchImpl?: typeof fetch;
}

export function buildNotionPageUrl(baseUrl: string, pageId: string): string | null {
  const normalizedBaseUrl = (baseUrl || "").trim().replace(/\/+$/, "");
  const normalizedPageId = (pageId || "").trim().replace(/-/g, "");

  if (!normalizedBaseUrl || !normalizedPageId) {
    return null;
  }

  return `${normalizedBaseUrl}/${normalizedPageId}`;
}

export function readRichText(items?: NotionRichTextItem[]): string {
  if (!items || items.length === 0) {
    return "";
  }

  return items
    .map((item) => item.plain_text ?? item.text?.content ?? "")
    .join("")
    .trim();
}

export function mapNotionPageToResult(page: NotionPage, notionBaseUrl: string): ShowcaseResult {
  const properties = page.properties || {};
  const title = readRichText(properties.Name?.title) || "Untitled result";
  const summary = readRichText(properties.Summary?.rich_text);
  const sourceUrl = properties.URL?.url?.trim() || null;
  const processingDuration = typeof properties["Processing Duration"]?.number === "number"
    ? properties["Processing Duration"].number ?? null
    : null;

  return {
    id: page.id,
    title,
    summary,
    source_url: sourceUrl,
    notion_url: buildNotionPageUrl(notionBaseUrl, page.id),
    created_at: page.created_time,
    processing_duration: processingDuration,
  };
}

export function buildResultsResponse(
  items: ShowcaseResult[],
  cacheTtlSeconds = DEFAULT_CACHE_TTL_SECONDS,
  generatedAt = new Date().toISOString(),
): ShowcaseApiResponse {
  return {
    items,
    generated_at: generatedAt,
    cache_ttl_seconds: cacheTtlSeconds,
  };
}

export async function fetchLatestCompletedResults(
  options: FetchNotionResultsOptions,
): Promise<ShowcaseApiResponse> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchImpl("https://api.notion.com/v1/databases/" + options.databaseId + "/query", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${options.apiKey}`,
      "Content-Type": "application/json",
      "Notion-Version": NOTION_VERSION,
    },
    body: JSON.stringify({
      filter: {
        property: "Status",
        select: {
          equals: "Completed",
        },
      },
      sorts: [
        {
          timestamp: "created_time",
          direction: "descending",
        },
      ],
      page_size: MAX_SHOWCASE_RESULTS,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to query Notion (${response.status})`);
  }

  const payload = await response.json() as { results?: NotionPage[] };
  const pages = Array.isArray(payload.results) ? payload.results : [];
  const items = pages.map((page) => mapNotionPageToResult(page, options.notionBaseUrl));

  return buildResultsResponse(items, options.cacheTtlSeconds ?? DEFAULT_CACHE_TTL_SECONDS);
}
