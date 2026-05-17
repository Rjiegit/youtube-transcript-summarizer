import type { ShowcaseResult } from "../types/showcase";

type ReadMap = Record<string, { readAt: string }>;

export function getLatestResultCreatedAt(items: ShowcaseResult[] = []): string {
  return items[0]?.created_at ?? "";
}

export function getReadStats(
  items: ShowcaseResult[] = [],
  readMap: ReadMap = {},
) {
  const totalCount = items.length;
  const unreadCount = items.filter((item) => !readMap[item.id]).length;

  return {
    totalCount,
    unreadCount,
  };
}

export function sortUnreadResultsFirst(
  items: ShowcaseResult[] = [],
  isRead: (id: string) => boolean,
): ShowcaseResult[] {
  const unreadItems = items.filter((item) => !isRead(item.id));
  const readItems = items.filter((item) => isRead(item.id));

  return [...unreadItems, ...readItems];
}
