import type { ShowcaseResult } from "../types/showcase";

export function getLatestResultCreatedAt(items: ShowcaseResult[] = []): string {
  return items[0]?.created_at ?? "";
}
