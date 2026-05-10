import { describe, expect, it } from "vitest";

import { formatTaipeiDate, formatTaipeiDateTime } from "../utils/datetime";
import { getLatestResultCreatedAt, sortUnreadResultsFirst } from "../utils/showcase";
import type { ShowcaseResult } from "../types/showcase";

function createResult(id: string): ShowcaseResult {
  return {
    id,
    title: id,
    summary: `${id} summary`,
    source_url: null,
    created_at: "2026-04-11T10:53:00.000Z",
    processing_duration: null,
  };
}

describe("showcase datetime formatting", () => {
  it("formats updated timestamps in Asia/Taipei", () => {
    expect(formatTaipeiDateTime("2026-04-11T10:53:00.000Z")).toBe("2026年4月11日 下午06:53");
  });

  it("formats card dates in Asia/Taipei", () => {
    expect(formatTaipeiDate("2026-04-11T10:53:00.000Z")).toBe("2026年4月11日");
  });

  it("returns an empty string for missing values", () => {
    expect(formatTaipeiDateTime("")).toBe("");
    expect(formatTaipeiDate(null)).toBe("");
  });

  it("uses the latest result created time for the home page stat", () => {
    expect(getLatestResultCreatedAt([
      {
        id: "latest",
        title: "Latest",
        summary: "Latest summary",
        source_url: null,
        created_at: "2026-04-11T10:53:00.000Z",
        processing_duration: null,
      },
      {
        id: "older",
        title: "Older",
        summary: "Older summary",
        source_url: null,
        created_at: "2026-04-10T10:53:00.000Z",
        processing_duration: null,
      },
    ])).toBe("2026-04-11T10:53:00.000Z");
    expect(getLatestResultCreatedAt([])).toBe("");
  });

  it("sorts unread results before read results while preserving group order", () => {
    const items = [
      createResult("read-1"),
      createResult("unread-1"),
      createResult("read-2"),
      createResult("unread-2"),
    ];

    expect(sortUnreadResultsFirst(items, (id) => id.startsWith("read")).map((item) => item.id)).toEqual([
      "unread-1",
      "unread-2",
      "read-1",
      "read-2",
    ]);
    expect(items.map((item) => item.id)).toEqual([
      "read-1",
      "unread-1",
      "read-2",
      "unread-2",
    ]);
  });

  it("returns an empty result list when sorting an empty list", () => {
    expect(sortUnreadResultsFirst([], () => false)).toEqual([]);
  });
});
