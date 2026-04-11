import type { ShowcaseApiResponse, ShowcaseDetailResult, ShowcaseResult } from "../../types/showcase";

export const DEFAULT_CACHE_TTL_SECONDS = 3600;
export const MAX_SHOWCASE_RESULTS = 100;
export const NOTION_VERSION = "2022-06-28";
const STATUS_PROPERTY_CANDIDATES = ["Status", "status", "狀態", "状态", "State", "state"];
const TITLE_PROPERTY_CANDIDATES = ["Title", "title", "Name", "name", "標題", "标题"];
const SUMMARY_PROPERTY_CANDIDATES = ["Summary", "summary", "Prompt", "prompt", "Description", "description", "摘要"];
const URL_PROPERTY_CANDIDATES = ["URL", "Url", "url", "Link", "link"];
const DATE_PROPERTY_CANDIDATES = ["Date", "date", "Published At", "published_at", "Published", "發布日期", "发布日期"];
const CREATED_TIME_PROPERTY_CANDIDATES = ["Created time", "created time", "Created Time", "建立時間", "建立日期"];

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
  checkbox?: boolean | null;
  date?: {
    start?: string | null;
  } | null;
  select?: {
    name?: string;
  } | null;
}

export interface NotionPage {
  id: string;
  created_time: string;
  properties: Record<string, NotionPageProperty>;
}

interface NotionBlockRichTextContainer {
  rich_text?: NotionRichTextItem[];
}

export interface NotionBlock {
  id: string;
  type: string;
  paragraph?: NotionBlockRichTextContainer;
  heading_1?: NotionBlockRichTextContainer;
  heading_2?: NotionBlockRichTextContainer;
  heading_3?: NotionBlockRichTextContainer;
  bulleted_list_item?: NotionBlockRichTextContainer;
  numbered_list_item?: NotionBlockRichTextContainer;
  to_do?: NotionBlockRichTextContainer;
  quote?: NotionBlockRichTextContainer;
  callout?: NotionBlockRichTextContainer;
  toggle?: NotionBlockRichTextContainer;
  code?: NotionBlockRichTextContainer;
}

interface NotionDatabaseProperty {
  id?: string;
  name?: string;
  type?: string;
}

export interface NotionDatabaseSchema {
  title?: NotionRichTextItem[];
  properties: Record<string, NotionDatabaseProperty>;
}

interface FetchNotionResultsOptions {
  apiKey: string;
  databaseId: string;
  cacheTtlSeconds?: number;
  visibilityPropertyName?: string;
  statusPropertyName?: string;
  completedStatusValue?: string;
  fetchImpl?: typeof fetch;
}

interface FetchShowcaseDetailOptions {
  apiKey: string;
  databaseId: string;
  pageId: string;
  statusPropertyName?: string;
  completedStatusValue?: string;
  fetchImpl?: typeof fetch;
}

interface PropertyDescriptor {
  name: string;
  type: string;
}

export interface ResolvedNotionQueryConfig {
  filter:
    | {
        kind: "none";
      }
    | {
        kind: "checkbox";
        propertyName: string;
        equals: boolean;
      }
    | {
        kind: "status";
        propertyName: string;
        propertyType: "status" | "select";
        completedValue: string;
      };
  availableProperties: Array<{ name: string; type: string }>;
}

export interface ResolvedNotionFieldMapping {
  titlePropertyName: string | null;
  summaryPropertyName: string | null;
  urlPropertyName: string | null;
  createdTimePropertyName: string | null;
  datePropertyName: string | null;
  processingDurationPropertyName: string | null;
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

function findPropertyByCandidates<T extends { type?: string }>(
  properties: Record<string, T>,
  candidates: string[],
  allowedTypes?: string[],
): [string, T] | undefined {
  const entries = Object.entries(properties);

  for (const candidate of candidates) {
    const exact = entries.find(([propertyName, property]) =>
      propertyName === candidate && (!allowedTypes || allowedTypes.includes(property.type || "")));
    if (exact) {
      return exact;
    }
    const caseInsensitive = entries.find(([propertyName, property]) =>
      propertyName.toLowerCase() === candidate.toLowerCase() &&
      (!allowedTypes || allowedTypes.includes(property.type || "")));
    if (caseInsensitive) {
      return caseInsensitive;
    }
  }

  return undefined;
}

export function resolveFieldMapping(schema: NotionDatabaseSchema): ResolvedNotionFieldMapping {
  const properties = schema.properties || {};

  const titleProperty = findPropertyByCandidates(properties, TITLE_PROPERTY_CANDIDATES, ["title"])
    ?? Object.entries(properties).find(([, property]) => property.type === "title");
  const summaryProperty = findPropertyByCandidates(properties, SUMMARY_PROPERTY_CANDIDATES, ["rich_text"]);
  const urlProperty = findPropertyByCandidates(properties, URL_PROPERTY_CANDIDATES, ["url"]);
  const createdTimeProperty = findPropertyByCandidates(properties, CREATED_TIME_PROPERTY_CANDIDATES, ["created_time"])
    ?? Object.entries(properties).find(([, property]) => property.type === "created_time");
  const dateProperty = findPropertyByCandidates(properties, DATE_PROPERTY_CANDIDATES, ["date"]);
  const processingDurationProperty = findPropertyByCandidates(properties, ["Processing Duration", "processing duration"], ["number"]);

  return {
    titlePropertyName: titleProperty?.[0] ?? null,
    summaryPropertyName: summaryProperty?.[0] ?? null,
    urlPropertyName: urlProperty?.[0] ?? null,
    createdTimePropertyName: createdTimeProperty?.[0] ?? null,
    datePropertyName: dateProperty?.[0] ?? null,
    processingDurationPropertyName: processingDurationProperty?.[0] ?? null,
  };
}

export function mapNotionPageToResult(
  page: NotionPage,
  fieldMapping?: ResolvedNotionFieldMapping,
): ShowcaseResult {
  const properties = page.properties || {};
  const mapping = fieldMapping ?? {
    titlePropertyName: "Name",
    summaryPropertyName: "Summary",
    urlPropertyName: "URL",
    createdTimePropertyName: null,
    datePropertyName: null,
    processingDurationPropertyName: "Processing Duration",
  };
  const title = mapping.titlePropertyName
    ? readRichText(properties[mapping.titlePropertyName]?.title)
    : "";
  const summary = mapping.summaryPropertyName
    ? readRichText(properties[mapping.summaryPropertyName]?.rich_text)
    : "";
  const sourceUrl = mapping.urlPropertyName
    ? properties[mapping.urlPropertyName]?.url?.trim() || null
    : null;
  const processingDuration = mapping.processingDurationPropertyName &&
    typeof properties[mapping.processingDurationPropertyName]?.number === "number"
    ? properties[mapping.processingDurationPropertyName]?.number ?? null
    : null;
  const createdAt = mapping.createdTimePropertyName
    ? page.created_time
    : mapping.datePropertyName
    ? properties[mapping.datePropertyName]?.date?.start || page.created_time
    : page.created_time;

  return {
    id: page.id,
    title: title || "Untitled result",
    summary,
    source_url: sourceUrl,
    created_at: createdAt,
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

function getBlockRichText(block: NotionBlock): string {
  const blockContent = block[block.type as keyof NotionBlock] as NotionBlockRichTextContainer | undefined;
  return readRichText(blockContent?.rich_text);
}

export function renderNotionBlocks(blocks: NotionBlock[]): string {
  return blocks
    .map((block) => getBlockRichText(block))
    .filter((content) => content.length > 0)
    .join("\n\n")
    .trim();
}

function buildNotionHeaders(apiKey: string): Record<string, string> {
  return {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
  };
}

export async function fetchDatabaseSchema(
  apiKey: string,
  databaseId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<NotionDatabaseSchema> {
  const response = await fetchImpl(`https://api.notion.com/v1/databases/${databaseId}`, {
    method: "GET",
    headers: buildNotionHeaders(apiKey),
  });

  if (!response.ok) {
    const errorText = await response.text();
    const compactErrorText = errorText.replace(/\s+/g, " ").trim();
    const detail = compactErrorText ? `: ${compactErrorText.slice(0, 300)}` : "";
    throw new Error(`Failed to read Notion database schema (${response.status})${detail}`);
  }

  return await response.json() as NotionDatabaseSchema;
}

export async function fetchPage(
  apiKey: string,
  pageId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<NotionPage> {
  const response = await fetchImpl(`https://api.notion.com/v1/pages/${pageId}`, {
    method: "GET",
    headers: buildNotionHeaders(apiKey),
  });

  if (!response.ok) {
    const errorText = await response.text();
    const compactErrorText = errorText.replace(/\s+/g, " ").trim();
    const detail = compactErrorText ? `: ${compactErrorText.slice(0, 300)}` : "";
    throw new Error(`Failed to read Notion page (${response.status})${detail}`);
  }

  return await response.json() as NotionPage;
}

export async function fetchPageBlocks(
  apiKey: string,
  pageId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<NotionBlock[]> {
  const blocks: NotionBlock[] = [];
  let cursor: string | undefined;

  while (true) {
    const query = new URLSearchParams({ page_size: "100" });
    if (cursor) {
      query.set("start_cursor", cursor);
    }

    const response = await fetchImpl(`https://api.notion.com/v1/blocks/${pageId}/children?${query.toString()}`, {
      method: "GET",
      headers: buildNotionHeaders(apiKey),
    });

    if (!response.ok) {
      const errorText = await response.text();
      const compactErrorText = errorText.replace(/\s+/g, " ").trim();
      const detail = compactErrorText ? `: ${compactErrorText.slice(0, 300)}` : "";
      throw new Error(`Failed to read Notion page blocks (${response.status})${detail}`);
    }

    const payload = await response.json() as {
      results?: NotionBlock[];
      has_more?: boolean;
      next_cursor?: string | null;
    };
    blocks.push(...(Array.isArray(payload.results) ? payload.results : []));

    if (!payload.has_more || !payload.next_cursor) {
      break;
    }
    cursor = payload.next_cursor;
  }

  return blocks;
}

export function resolveStatusConfig(
  schema: NotionDatabaseSchema,
  preferredPropertyName?: string,
  completedStatusValue = "Completed",
): ResolvedNotionQueryConfig {
  const availableProperties = Object.entries(schema.properties || {}).map(([name, property]) => ({
    name,
    type: property.type || "unknown",
  }));
  const properties = schema.properties || {};
  const findByName = (name: string, allowedTypes?: string[]) =>
    findPropertyByCandidates(properties, [name], allowedTypes);

  let statusMatch: [string, NotionDatabaseProperty] | undefined;
  if (preferredPropertyName) {
    statusMatch = findByName(preferredPropertyName);
    if (!statusMatch) {
      throw new Error(
        `Configured status property "${preferredPropertyName}" was not found. Available properties: ${availableProperties.map((item) => `${item.name}(${item.type})`).join(", ")}`,
      );
    }
  } else {
    for (const candidate of STATUS_PROPERTY_CANDIDATES) {
      statusMatch = findByName(candidate, ["status", "select"]);
      if (statusMatch) {
        break;
      }
    }
    if (!statusMatch) {
      statusMatch = Object.entries(properties).find(([, property]) => property.type === "status" || property.type === "select");
    }
  }

  if (!statusMatch) {
    return {
      filter: {
        kind: "none",
      },
      availableProperties,
    };
  }

  const [propertyName, property] = statusMatch;
  if (property.type !== "status" && property.type !== "select") {
    throw new Error(`Property "${propertyName}" must be a status/select field, got "${property.type || "unknown"}".`);
  }

  return {
    filter: {
      kind: "status",
      propertyName,
      propertyType: property.type,
      completedValue: completedStatusValue,
    },
    availableProperties,
  };
}

export async function fetchLatestCompletedResults(
  options: FetchNotionResultsOptions,
): Promise<ShowcaseApiResponse> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const schema = await fetchDatabaseSchema(options.apiKey, options.databaseId, fetchImpl);
  const queryConfig = resolveStatusConfig(
    schema,
    options.statusPropertyName,
    options.completedStatusValue || "Completed",
  );
  const fieldMapping = resolveFieldMapping(schema);
  const queryFilter = queryConfig.filter.kind === "status"
    ? {
        property: queryConfig.filter.propertyName,
        [queryConfig.filter.propertyType]: {
          equals: queryConfig.filter.completedValue,
        },
      }
    : null;
  const response = await fetchImpl("https://api.notion.com/v1/databases/" + options.databaseId + "/query", {
    method: "POST",
    headers: buildNotionHeaders(options.apiKey),
    body: JSON.stringify({
      ...(queryFilter ? { filter: queryFilter } : {}),
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
    const errorText = await response.text();
    const compactErrorText = errorText.replace(/\s+/g, " ").trim();
    const detail = compactErrorText ? `: ${compactErrorText.slice(0, 300)}` : "";
    throw new Error(`Failed to query Notion (${response.status})${detail}`);
  }

  const payload = await response.json() as { results?: NotionPage[] };
  const pages = Array.isArray(payload.results) ? payload.results : [];
  const items = pages.map((page) => mapNotionPageToResult(page, fieldMapping));

  return buildResultsResponse(items, options.cacheTtlSeconds ?? DEFAULT_CACHE_TTL_SECONDS);
}

export async function fetchShowcaseDetail(
  options: FetchShowcaseDetailOptions,
): Promise<ShowcaseDetailResult> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const schema = await fetchDatabaseSchema(options.apiKey, options.databaseId, fetchImpl);
  const fieldMapping = resolveFieldMapping(schema);
  const page = await fetchPage(options.apiKey, options.pageId, fetchImpl);
  const blocks = await fetchPageBlocks(options.apiKey, options.pageId, fetchImpl);
  const baseResult = mapNotionPageToResult(page, fieldMapping);
  const content = renderNotionBlocks(blocks) || baseResult.summary;

  return {
    ...baseResult,
    content,
  };
}
