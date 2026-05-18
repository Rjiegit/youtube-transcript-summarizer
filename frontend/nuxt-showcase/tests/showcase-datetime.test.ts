import { describe, expect, it } from "vitest";

import { formatTaipeiDate, formatTaipeiDateTime } from "../utils/datetime";
import {
  dedupeShowcaseResults,
  getLatestResultCreatedAt,
  getReadStats,
  getResultReadKey,
  isResultRead,
  sortUnreadResultsFirst,
} from "../utils/showcase";
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

function createResultWithUrl(id: string, sourceUrl: string): ShowcaseResult {
  return {
    ...createResult(id),
    source_url: sourceUrl,
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

    const displayItems = dedupeShowcaseResults(items);

    expect(sortUnreadResultsFirst(displayItems, (item) => item.id.startsWith("read")).map((item) => item.id)).toEqual([
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

  it("uses normalized source URLs as article-level read keys", () => {
    expect(getResultReadKey(createResultWithUrl(
      "result-1",
      "HTTP://Example.com/Article/?b=2&a=1&utm_source=newsletter#section",
    ))).toBe("url:https://example.com/Article?a=1&b=2");
    expect(getResultReadKey(createResult("result-2"))).toBe("result-2");
  });

  it("deduplicates repeated source URLs while preserving the newest representative", () => {
    const items = [
      createResultWithUrl("result-1", "https://example.com/article/?b=2&a=1"),
      createResultWithUrl("result-2", "https://example.com/article?a=1&b=2#comments"),
      createResultWithUrl("result-3", "https://example.com/other"),
    ];

    const dedupedItems = dedupeShowcaseResults(items);

    expect(dedupedItems.map((item) => item.id)).toEqual(["result-1", "result-3"]);
    expect(dedupedItems[0].readKey).toBe("url:https://example.com/article?a=1&b=2");
    expect(dedupedItems[0].readCandidateIds).toEqual(["result-1", "result-2"]);
  });

  it("treats a duplicated article as read when its article key or legacy page ID is read", () => {
    const [dedupedItem] = dedupeShowcaseResults([
      createResultWithUrl("result-1", "https://example.com/article"),
      createResultWithUrl("result-2", "https://example.com/article/"),
    ]);

    expect(isResultRead(dedupedItem, {
      "result-2": { readAt: "2026-04-11T00:00:00.000Z" },
    })).toBe(true);
    expect(isResultRead(dedupedItem, {
      [dedupedItem.readKey]: { readAt: "2026-04-11T00:00:00.000Z" },
    })).toBe(true);
  });

  it("counts unread items from the current result list only", () => {
    expect(getReadStats(dedupeShowcaseResults([
      createResultWithUrl("result-1", "https://example.com/article"),
      createResultWithUrl("result-2", "https://example.com/article/"),
      createResult("result-3"),
    ]), {
      "result-2": { readAt: "2026-04-11T00:00:00.000Z" },
      "stale-result": { readAt: "2026-04-10T00:00:00.000Z" },
    })).toEqual({
      totalCount: 2,
      unreadCount: 1,
    });
  });

  it("treats an empty result list as zero read stats", () => {
    expect(getReadStats([], {
      "stale-result": { readAt: "2026-04-10T00:00:00.000Z" },
    })).toEqual({
      totalCount: 0,
      unreadCount: 0,
    });
  });
});
