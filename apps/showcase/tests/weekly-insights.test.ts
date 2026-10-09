import { describe, expect, it } from "vitest";

import { categoryShare, comparableWeeks, filterInsightWeeks, taipeiWeekStart } from "../utils/weekly-insights";
import type { WeeklyInsightSummary } from "../types/weekly-insights";

const week = (start: string, overrides: Partial<WeeklyInsightSummary> = {}): WeeklyInsightSummary => ({
  start, endExclusive: "2026-09-13", coverageStart: start, periodState: "closed", dataCompleteness: "complete",
  title: "週報", summary: "摘要", revision: 1, asOf: "2026-10-09T09:44:10Z",
  metrics: { rawCount: 2, sourceCount: 2, newSourceCount: 2, recurringSourceCount: 0 },
  categories: [{ id: "agent-engineering", count: 1 }], ...overrides,
});

describe("weekly insight calendar and comparisons", () => {
  it("starts each Taipei week on Sunday, including UTC boundary and year changes", () => {
    expect(taipeiWeekStart("2026-09-05T15:59:59Z")).toBe("2026-08-30");
    expect(taipeiWeekStart("2026-09-05T16:00:00Z")).toBe("2026-09-06");
    expect(taipeiWeekStart("2026-09-01T00:18:00Z")).toBe("2026-08-30");
    expect(taipeiWeekStart("2027-01-01T00:00:00Z")).toBe("2026-12-27");
  });

  it("rejects invalid timestamps instead of producing an invalid week", () => {
    expect(() => taipeiWeekStart("invalid")).toThrow();
  });

  it("compares only closed weeks with full coverage and complete data", () => {
    const items = [
      week("2026-08-30", { coverageStart: "2026-09-01" }),
      week("2026-09-06"), week("2026-09-13"),
      week("2026-09-20", { dataCompleteness: "partial" }),
      week("2026-10-04", { periodState: "open" }),
    ];
    expect(comparableWeeks(items).map((item) => item.start)).toEqual(["2026-09-06", "2026-09-13"]);
  });

  it("uses overlapping calendar weeks for date filters without truncating their statistics", () => {
    const items = [week("2026-08-30", { endExclusive: "2026-09-06" }), week("2026-09-06")];
    expect(filterInsightWeeks(items, "2026-09-05", "2026-09-05")).toHaveLength(1);
    expect(filterInsightWeeks(items, "2026-09-06", "2026-09-06").map((item) => item.start)).toEqual(["2026-09-06"]);
    expect(filterInsightWeeks(items, "2026-09-13", "2026-09-06")).toEqual([]);
  });

  it("shows no share for an empty week and preserves a zero category count", () => {
    expect(categoryShare(week("2026-09-06"), "agent-engineering")).toBe(50);
    expect(categoryShare(week("2026-09-06"), "career")).toBe(0);
    expect(categoryShare(week("2026-09-06", {
      metrics: { rawCount: 0, sourceCount: 0, newSourceCount: 0, recurringSourceCount: 0 },
    }), "career")).toBeNull();
  });
});
