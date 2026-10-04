import { describe, expect, it, vi } from "vitest";
import { fetchShowcaseDetail } from "../server/utils/notion";

const options = { apiKey: "test-key", databaseId: "database", pageId: "page" };
const payloads = [
  { properties: { Name: { type: "title" }, Summary: { type: "rich_text" } } },
  { id: "page", created_time: "2026-04-11", properties: {
    Name: { title: [{ plain_text: "Title" }] }, Summary: { rich_text: [{ plain_text: "Summary" }] },
  } },
  { results: [], has_more: false },
];

describe("detail request concurrency", () => {
  it("starts all three requests before schema resolves and preserves summary fallback", async () => {
    let releaseSchema!: (response: Response) => void;
    const schema = new Promise<Response>((resolve) => { releaseSchema = resolve; });
    const fetchImpl = vi.fn<typeof fetch>()
      .mockReturnValueOnce(schema)
      .mockResolvedValueOnce(new Response(JSON.stringify(payloads[1])))
      .mockResolvedValueOnce(new Response(JSON.stringify(payloads[2])));
    const result = fetchShowcaseDetail({ ...options, fetchImpl });
    const started = fetchImpl.mock.calls.map(([url]) => String(url));
    // Release even when the assertion fails, so no pending work is left behind.
    releaseSchema(new Response(JSON.stringify(payloads[0])));
    expect(await result).toMatchObject({ id: "page", title: "Title", summary: "Summary", content: "Summary" });
    expect(started).toEqual([
      "https://api.notion.com/v1/databases/database",
      "https://api.notion.com/v1/pages/page",
      "https://api.notion.com/v1/blocks/page/children?page_size=100",
    ]);
  });

  it.each([0, 1, 2])("propagates connection failure at request %i without automatic retry", async (failed) => {
    const error = new TypeError("fetch failed");
    const fetchImpl = vi.fn<typeof fetch>(async (url) => {
      const index = String(url).includes("/databases/") ? 0 : String(url).includes("/pages/") ? 1 : 2;
      if (index === failed) throw error;
      return new Response(JSON.stringify(payloads[index]));
    });
    await expect(fetchShowcaseDetail({ ...options, fetchImpl })).rejects.toBe(error);
    expect(fetchImpl.mock.calls.filter(([url]) => String(url).includes(
      ["/databases/", "/pages/", "/blocks/"][failed],
    ))).toHaveLength(1);
  });
});
