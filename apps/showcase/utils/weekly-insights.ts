import type { WeeklyInsightSummary } from "../types/weekly-insights";

export function taipeiWeekStart(timestamp: string): string {
  const date = new Date(timestamp);
  if (!Number.isFinite(date.getTime())) throw new Error("Invalid timestamp");
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Taipei", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(date);
  const part = (type: string) => Number(parts.find((item) => item.type === type)?.value);
  const localDate = new Date(Date.UTC(part("year"), part("month") - 1, part("day")));
  localDate.setUTCDate(localDate.getUTCDate() - localDate.getUTCDay());
  return localDate.toISOString().slice(0, 10);
}

export function weekEndDate(endExclusive: string): string {
  const date = new Date(`${endExclusive}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() - 1);
  return date.toISOString().slice(0, 10);
}

export function formatWeekRange(week: WeeklyInsightSummary): string {
  const format = (date: string) => `${Number(date.slice(5, 7))}/${Number(date.slice(8, 10))}`;
  return `${format(week.start)}–${format(weekEndDate(week.endExclusive))}`;
}

export function insightWeekStatus(week: WeeklyInsightSummary): string {
  if (week.dataCompleteness !== "complete") return "資料未完整";
  if (week.periodState === "open") return "本週進行中";
  if (week.coverageStart !== week.start) return "首週部分資料";
  return "完整週";
}

export function comparableWeeks<T extends WeeklyInsightSummary>(weeks: T[]): T[] {
  return weeks.filter((week) => week.periodState === "closed" && week.dataCompleteness === "complete" &&
    week.coverageStart === week.start).sort((a, b) => a.start.localeCompare(b.start));
}

export function categoryShare(week: WeeklyInsightSummary, categoryId: string): number | null {
  if (!week.metrics.sourceCount) return null;
  return 100 * (week.categories.find((category) => category.id === categoryId)?.count ?? 0) / week.metrics.sourceCount;
}

export function filterInsightWeeks<T extends WeeklyInsightSummary>(weeks: T[], from = "", to = ""): T[] {
  if (from && to && from > to) return [];
  return weeks.filter((week) => (!from || week.endExclusive > from) && (!to || week.start <= to));
}

export function filterInsightWeeksByRange<T extends WeeklyInsightSummary>(weeks: T[], fromWeek = "", toWeek = ""): T[] {
  if (fromWeek && toWeek && fromWeek > toWeek) return [];
  return weeks.filter((week) => (!fromWeek || week.start >= fromWeek) && (!toWeek || week.start <= toWeek));
}
