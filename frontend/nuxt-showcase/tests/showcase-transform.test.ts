import { describe, expect, it, vi } from "vitest";

import { sampleNotionPages } from "../test-data/notion";
import {
  MAX_SHOWCASE_RESULTS,
  buildNotionPageUrl,
  fetchLatestCompletedResults,
  mapNotionPageToResult,
  resolveFieldMapping,
  resolveStatusConfig,
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
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          properties: {
            Public: { type: "checkbox" },
            Title: { type: "title" },
            Prompt: { type: "rich_text" },
            URL: { type: "url" },
            "Created time": { type: "created_time" },
            Date: { type: "date" },
          },
        }),
      })
      .mockResolvedValueOnce({
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

    expect(fetchImpl).toHaveBeenCalledTimes(2);
    const [, request] = fetchImpl.mock.calls[1];
    expect(JSON.parse(String(request.body))).toMatchObject({
      page_size: MAX_SHOWCASE_RESULTS,
      filter: {
        property: "Public",
        checkbox: { equals: true },
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

  it("surfaces compact Notion API error details when the query fails", async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          properties: {
            Public: { type: "checkbox" },
            Title: { type: "title" },
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => '{"object":"error","message":"Could not find database with ID: demo"}',
      });

    await expect(
      fetchLatestCompletedResults({
        apiKey: "secret",
        databaseId: "database-id",
        notionBaseUrl: "https://www.notion.so/workspace",
        fetchImpl,
      }),
    ).rejects.toThrow('Failed to query Notion (404): {"object":"error","message":"Could not find database with ID: demo"}');
  });

  it("resolves a status-like property from database schema", () => {
    const statusConfig = resolveStatusConfig({
      properties: {
        Public: { type: "checkbox" },
        標題: { type: "title" },
      },
    });

    expect(statusConfig.filter.kind).toBe("checkbox");
    if (statusConfig.filter.kind === "checkbox") {
      expect(statusConfig.filter.propertyName).toBe("Public");
      expect(statusConfig.filter.equals).toBe(true);
    }
  });

  it("prefers the configured property name when provided", () => {
    const statusConfig = resolveStatusConfig(
      {
        properties: {
          PublishState: { type: "select" },
          狀態: { type: "status" },
        },
      },
      "PublishState",
      "Done",
    );

    expect(statusConfig.filter.kind).toBe("status");
    if (statusConfig.filter.kind === "status") {
      expect(statusConfig.filter.propertyName).toBe("PublishState");
      expect(statusConfig.filter.propertyType).toBe("select");
      expect(statusConfig.filter.completedValue).toBe("Done");
    }
  });

  it("resolves field mapping for public content databases", () => {
    const fieldMapping = resolveFieldMapping({
      properties: {
        Title: { type: "title" },
        Prompt: { type: "rich_text" },
        URL: { type: "url" },
        "Created time": { type: "created_time" },
        Date: { type: "date" },
      },
    });

    expect(fieldMapping).toMatchObject({
      titlePropertyName: "Title",
      summaryPropertyName: "Prompt",
      urlPropertyName: "URL",
      createdTimePropertyName: "Created time",
      datePropertyName: "Date",
    });
  });
});
