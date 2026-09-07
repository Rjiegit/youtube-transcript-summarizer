import { describe, expect, it, vi } from "vitest";

import { sampleNotionPages } from "../test-data/notion";
import { sampleNotionBlocks } from "../test-data/notion";
import {
  fetchPageBlocks,
  fetchShowcaseDetail,
  fetchLatestCompletedResults,
  mapNotionPageToResult,
  renderNotionBlocks,
  resolveFieldMapping,
  resolveStatusConfig,
} from "../server/utils/notion";

describe("showcase Notion mapping", () => {
  it("maps a Notion page to the public showcase shape", () => {
    const result = mapNotionPageToResult(sampleNotionPages[0]);

    expect(result).toMatchObject({
      id: "result-2-page-id",
      title: "Second result",
      summary: "A concise summary of the second result.",
      source_url: "https://www.youtube.com/watch?v=second",
      processing_duration: 12.4,
    });
  });

  it("queries Notion for the latest 50 completed items", async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          properties: {
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
      cacheTtlSeconds: 3600,
      fetchImpl,
    });

    expect(fetchImpl).toHaveBeenCalledTimes(2);
    const [, request] = fetchImpl.mock.calls[1];
    expect(JSON.parse(String(request.body))).toMatchObject({
      page_size: 50,
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

  it("renders Notion blocks into markdown detailed content", () => {
    expect(renderNotionBlocks([
      {
        id: "heading-1",
        type: "heading_1",
        heading_1: {
          rich_text: [{ plain_text: "主要摘要" }],
        },
      },
      ...sampleNotionBlocks,
      {
        id: "bullet-1",
        type: "bulleted_list_item",
        bulleted_list_item: {
          rich_text: [{ plain_text: "保留清單項目" }],
        },
      },
      {
        id: "number-1",
        type: "numbered_list_item",
        numbered_list_item: {
          rich_text: [{ plain_text: "第一個步驟" }],
        },
      },
      {
        id: "quote-1",
        type: "quote",
        quote: {
          rich_text: [{ plain_text: "重要引述" }],
        },
      },
      {
        id: "todo-1",
        type: "to_do",
        to_do: {
          rich_text: [{ plain_text: "已完成項目" }],
          checked: true,
        },
      },
      {
        id: "code-1",
        type: "code",
        code: {
          rich_text: [{ plain_text: "const answer = 42;" }],
          language: "typescript",
        },
      },
    ])).toBe([
      "# 主要摘要",
      "Detailed paragraph one.",
      "Detailed paragraph two.",
      "- 保留清單項目",
      "1. 第一個步驟",
      "> 重要引述",
      "- [x] 已完成項目",
      "```typescript\nconst answer = 42;\n```",
    ].join("\n\n"));
  });

  it("preserves raw markdown stored across Notion paragraph rich text chunks", () => {
    expect(renderNotionBlocks([
      {
        id: "markdown-1",
        type: "paragraph",
        paragraph: {
          rich_text: [
            { plain_text: "## 重點整理\n\n" },
            { plain_text: "- 第一點\n- 第二點\n\n" },
            { plain_text: "[參考連結](https://example.com/docs)" },
          ],
        },
      },
    ])).toBe("## 重點整理\n\n- 第一點\n- 第二點\n\n[參考連結](https://example.com/docs)");
  });

  it("preserves nested Notion blocks as indented markdown", () => {
    expect(renderNotionBlocks([
      {
        id: "solution",
        type: "bulleted_list_item",
        bulleted_list_item: {
          rich_text: [{ plain_text: "解決方案：OpenWiki" }],
        },
        children: [
          {
            id: "positioning",
            type: "bulleted_list_item",
            bulleted_list_item: {
              rich_text: [{ plain_text: "定位：獨立於 Agent 的基礎設施" }],
            },
            children: [
              {
                id: "detail",
                type: "paragraph",
                paragraph: {
                  rich_text: [{ plain_text: "**重點**：共同使用的長期知識庫" }],
                },
              },
            ],
          },
          {
            id: "goal",
            type: "numbered_list_item",
            numbered_list_item: {
              rich_text: [{ plain_text: "讓不同 Agent 共用知識庫" }],
            },
          },
        ],
      },
    ])).toBe([
      "- 解決方案：OpenWiki",
      "",
      "    - 定位：獨立於 Agent 的基礎設施",
      "",
      "        **重點**：共同使用的長期知識庫",
      "",
      "    1. 讓不同 Agent 共用知識庫",
    ].join("\n"));
  });

  it("recursively fetches paginated child blocks", async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [{
            id: "parent",
            type: "bulleted_list_item",
            has_children: true,
            bulleted_list_item: { rich_text: [{ plain_text: "Parent" }] },
          }],
          has_more: false,
          next_cursor: null,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [{
            id: "child-1",
            type: "paragraph",
            has_children: true,
            paragraph: { rich_text: [{ plain_text: "First child" }] },
          }],
          has_more: true,
          next_cursor: "next page",
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [{
            id: "child-2",
            type: "paragraph",
            has_children: false,
            paragraph: { rich_text: [{ plain_text: "Second child" }] },
          }],
          has_more: false,
          next_cursor: null,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [{
            id: "grandchild",
            type: "bulleted_list_item",
            has_children: false,
            bulleted_list_item: { rich_text: [{ plain_text: "Grandchild" }] },
          }],
          has_more: false,
          next_cursor: null,
        }),
      });

    const blocks = await fetchPageBlocks("secret", "page-id", fetchImpl);

    expect(blocks[0].children?.map((child) => child.id)).toEqual(["child-1", "child-2"]);
    expect(blocks[0].children?.[0].children?.[0].id).toBe("grandchild");
    expect(fetchImpl).toHaveBeenCalledTimes(4);
    expect(fetchImpl.mock.calls.map(([url]) => url)).toEqual([
      "https://api.notion.com/v1/blocks/page-id/children?page_size=100",
      "https://api.notion.com/v1/blocks/parent/children?page_size=100",
      "https://api.notion.com/v1/blocks/parent/children?page_size=100&start_cursor=next+page",
      "https://api.notion.com/v1/blocks/child-1/children?page_size=100",
    ]);
  });

  it("preserves Notion rich text annotations without escaping raw markdown text", () => {
    expect(renderNotionBlocks([
      {
        id: "rich-1",
        type: "paragraph",
        paragraph: {
          rich_text: [
            {
              plain_text: "bold *literal*",
              annotations: { bold: true },
            },
            { plain_text: " and " },
            { plain_text: "**already markdown** and " },
            {
              plain_text: "docs",
              href: "https://example.com/docs?x=1&y=2",
            },
            { plain_text: " plus " },
            {
              plain_text: "inline_code()",
              annotations: { code: true },
            },
          ],
        },
      },
    ])).toBe("**bold *literal*** and **already markdown** and [docs](https://example.com/docs?x=1&y=2) plus `inline_code()`");
  });

  it("leaves raw HTML text for the markdown renderer to escape", () => {
    expect(renderNotionBlocks([
      {
        id: "html-1",
        type: "paragraph",
        paragraph: {
          rich_text: [{ plain_text: "<script>alert('xss')</script>" }],
        },
      },
    ])).toBe("<script>alert('xss')</script>");
  });

  it("fetches showcase detail content from Notion page blocks", async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          properties: {
            Name: { type: "title" },
            Summary: { type: "rich_text" },
            URL: { type: "url" },
            "Created time": { type: "created_time" },
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => sampleNotionPages[0],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: sampleNotionBlocks,
          has_more: false,
          next_cursor: null,
        }),
      });

    const result = await fetchShowcaseDetail({
      apiKey: "secret",
      databaseId: "database-id",
      pageId: "result-2-page-id",
      fetchImpl,
    });

    expect(result.title).toBe("Second result");
    expect(result.content).toBe("Detailed paragraph one.\n\nDetailed paragraph two.");
  });

  it("surfaces compact Notion API error details when the query fails", async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          properties: {
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
        fetchImpl,
      }),
    ).rejects.toThrow('Failed to query Notion (404): {"object":"error","message":"Could not find database with ID: demo"}');
  });

  it("resolves a status-like property from database schema", () => {
    const statusConfig = resolveStatusConfig({
      properties: {
        標題: { type: "title" },
      },
    });

    expect(statusConfig.filter.kind).toBe("none");
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
