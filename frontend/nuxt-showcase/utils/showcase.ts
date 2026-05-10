import type { ShowcaseResult } from "../types/showcase";

export function getLatestResultCreatedAt(items: ShowcaseResult[] = []): string {
  return items[0]?.created_at ?? "";
}

export function sortUnreadResultsFirst(
  items: ShowcaseResult[] = [],
  isRead: (id: string) => boolean,
): ShowcaseResult[] {
  const unreadItems = items.filter((item) => !isRead(item.id));
  const readItems = items.filter((item) => isRead(item.id));

  return [...unreadItems, ...readItems];
}
