import { createHash } from "node:crypto";
import registry from "../../.generated/weekly-insights";
import type { InsightListResponse, InsightSeries, WeeklyInsight } from "../../types/weekly-insights";

const snapshot = registry as unknown as { series: InsightSeries; weeks: WeeklyInsight[] };
export const insightETag = `"${createHash("sha256").update(JSON.stringify(snapshot)).digest("hex").slice(0, 24)}"`;

export function insightList(): InsightListResponse {
  return {
    series: snapshot.series,
    weeks: snapshot.weeks.map(({ content: _content, sources: _sources, qualityNote: _quality, ...summary }) => summary),
  };
}

export function insightDetail(start: string) {
  const index = snapshot.weeks.findIndex((week) => week.start === start);
  if (index < 0) return null;
  return {
    series: snapshot.series,
    week: snapshot.weeks[index],
    previous: snapshot.weeks[index - 1]?.start ?? null,
    next: snapshot.weeks[index + 1]?.start ?? null,
  };
}
