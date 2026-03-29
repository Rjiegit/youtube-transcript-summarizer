import { describe, expect, it, vi } from "vitest";

import { sampleNotionPages } from "../test-data/notion";
import {
  MAX_SHOWCASE_RESULTS,
  buildNotionPageUrl,
  fetchLatestCompletedResults,
  mapNotionPageToResult,
} from "../server/utils/notion";

describe("showcase Notion mapping", () => {
  it("builds a Notion page URL from base url and page id", () => {
    expect(buildNotionPageUrl("https://www.notion.so/workspace", "abcd-1234")).toBe(
      "https://www.notion.so/workspace/abcd1234",
    );
  });

  it("maps a Notion page to the public showcase shape", () => {
    const result = mapNotionPageToResult(sampleNotionPages[0], "https://www.notion.so/workspace");

    expect(result).toMatchObject({
      id: "result-2-page-id",
      title: "Second result",
      summary: "A concise summary of the second result.",
      source_url: "https://www.youtube.com/watch?v=second",
      notion_url: "https://www.notion.so/workspace/result2pageid",
      processing_duration: 12.4,
    });
  });

  it("queries Notion for the latest 100 completed items", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: sampleNotionPages }),
    });

    const response = await fetchLatestCompletedResults({
      apiKey: "secret",
      databaseId: "database-id",
      notionBaseUrl: "https://www.notion.so/workspace",
      cacheTtlSeconds: 3600,
      fetchImpl,
    });

    expect(fetchImpl).toHaveBeenCalledTimes(1);
    const [, request] = fetchImpl.mock.calls[0];
    expect(JSON.parse(String(request.body))).toMatchObject({
      page_size: MAX_SHOWCASE_RESULTS,
      filter: {
        property: "Status",
        select: { equals: "Completed" },
      },
      sorts: [
        {
          timestamp: "created_time",
          direction: "descending",
        },
      ],
    });
    expect(response.items).toHaveLength(2);
    expect(response.cache_ttl_seconds).toBe(3600);
  });
});
