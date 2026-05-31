import type { ShowcaseResult } from "../types/showcase";

type ReadMap = Record<string, { readAt: string }>;

export interface ShowcaseDisplayResult extends ShowcaseResult {
  readKey: string;
  readCandidateIds: string[];
}

const TRACKING_QUERY_PARAMS = new Set([
  "fbclid",
  "gclid",
  "mc_cid",
  "mc_eid",
  "utm_campaign",
  "utm_content",
  "utm_medium",
  "utm_source",
  "utm_term",
]);

export function getLatestResultCreatedAt(items: ShowcaseResult[] = []): string {
  return items[0]?.created_at ?? "";
}

function normalizeSourceUrl(sourceUrl: string): string {
  try {
    const url = new URL(sourceUrl);
    url.protocol = "https:";
    url.hash = "";
    url.pathname = url.pathname.replace(/\/+$/, "") || "/";

    const params = Array.from(url.searchParams.entries())
      .filter(([key]) => !TRACKING_QUERY_PARAMS.has(key.toLowerCase()))
      .sort(([leftKey, leftValue], [rightKey, rightValue]) =>
        leftKey === rightKey ? leftValue.localeCompare(rightValue) : leftKey.localeCompare(rightKey));

    url.search = "";
    for (const [key, value] of params) {
      url.searchParams.append(key, value);
    }

    return url.toString().replace(/\/(?=\?)/, "").replace(/\/$/, "");
  } catch {
    return sourceUrl.trim().toLowerCase();
  }
}

export function getResultReadKey(item: ShowcaseResult): string {
  const sourceUrl = item.source_url?.trim();

  if (!sourceUrl) {
    return item.id;
  }

  return `url:${normalizeSourceUrl(sourceUrl)}`;
}

export function dedupeShowcaseResults(items: ShowcaseResult[] = []): ShowcaseDisplayResult[] {
  const groupedItems = new Map<string, ShowcaseDisplayResult>();

  for (const item of items) {
    const readKey = getResultReadKey(item);
    const existingItem = groupedItems.get(readKey);

    if (existingItem) {
      existingItem.readCandidateIds.push(item.id);
      continue;
    }

    groupedItems.set(readKey, {
      ...item,
      readKey,
      readCandidateIds: [item.id],
    });
  }

  return Array.from(groupedItems.values());
}

export function isResultRead(
  item: ShowcaseDisplayResult,
  readMap: ReadMap = {},
): boolean {
  return Boolean(readMap[item.readKey] || item.readCandidateIds.some((id) => readMap[id]));
}

export function getResultReadKeys(item: ShowcaseDisplayResult): string[] {
  return Array.from(new Set([
    item.readKey,
    item.id,
    ...item.readCandidateIds,
  ].map((id) => id.trim()).filter(Boolean)));
}

export function getReadStats(
  items: ShowcaseDisplayResult[] = [],
  readMap: ReadMap = {},
) {
  const totalCount = items.length;
  const unreadCount = items.filter((item) => !isResultRead(item, readMap)).length;

  return {
    totalCount,
    unreadCount,
  };
}

export function sortUnreadResultsFirst(
  items: ShowcaseDisplayResult[] = [],
  isRead: (item: ShowcaseDisplayResult) => boolean,
): ShowcaseDisplayResult[] {
  const unreadItems = items.filter((item) => !isRead(item));
  const readItems = items.filter((item) => isRead(item));

  return [...unreadItems, ...readItems];
}
