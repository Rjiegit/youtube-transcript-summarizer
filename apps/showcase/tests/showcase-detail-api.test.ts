import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const runtimeConfigMock = vi.fn();
const setHeaderMock = vi.fn();
const fetchShowcaseDetailMock = vi.fn();

vi.mock("../server/utils/notion", () => ({
  fetchShowcaseDetail: fetchShowcaseDetailMock,
}));

vi.mock("h3", async () => {
  const actual = await vi.importActual<typeof import("h3")>("h3");
  return {
    ...actual,
    setHeader: setHeaderMock,
  };
});

vi.stubGlobal("useRuntimeConfig", runtimeConfigMock);

describe("showcase detail API cache", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
    vi.useRealTimers();
    runtimeConfigMock.mockReset();
    setHeaderMock.mockReset();
    fetchShowcaseDetailMock.mockReset();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  function createEvent(pageId: string) {
    return {
      context: {
        params: {
          id: pageId,
        },
      },
    };
  }

  it("sets cache headers using SHOWCASE_CACHE_TTL_SECONDS", async () => {
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "600";
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "api-key",
      notionDatabaseId: "database-id",
      showcaseCacheTtlSeconds: 0,
    });
    fetchShowcaseDetailMock.mockResolvedValue({
      id: "page-1",
      title: "Title",
      summary: "Summary",
      content: "Content",
      source_url: null,
      created_at: "2026-04-11T00:00:00.000Z",
      processing_duration: 3.1,
    });

    const handler = (await import("../server/api/showcase/results/[id].get")).default;
    await handler(createEvent("page-1"));

    expect(setHeaderMock).toHaveBeenCalledWith(
      expect.anything(),
      "Cache-Control",
      "public, s-maxage=600, stale-while-revalidate=600",
    );
  });

  it("reuses cached detail responses for the same page id within the TTL", async () => {
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "600";
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "api-key",
      notionDatabaseId: "database-id",
      showcaseCacheTtlSeconds: 0,
    });
    fetchShowcaseDetailMock.mockResolvedValue({
      id: "page-1",
      title: "Title",
      summary: "Summary",
      content: "Content",
      source_url: null,
      created_at: "2026-04-11T00:00:00.000Z",
      processing_duration: 3.1,
    });

    const handler = (await import("../server/api/showcase/results/[id].get")).default;
    const first = await handler(createEvent("page-1"));
    const second = await handler(createEvent("page-1"));

    expect(first).toEqual(second);
    expect(fetchShowcaseDetailMock).toHaveBeenCalledTimes(1);
  });

  it("keeps cache entries isolated per page id", async () => {
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "600";
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "api-key",
      notionDatabaseId: "database-id",
      showcaseCacheTtlSeconds: 0,
    });
    fetchShowcaseDetailMock
      .mockResolvedValueOnce({
        id: "page-1",
        title: "Title 1",
        summary: "Summary",
        content: "Content",
        source_url: null,
        created_at: "2026-04-11T00:00:00.000Z",
        processing_duration: 3.1,
      })
      .mockResolvedValueOnce({
        id: "page-2",
        title: "Title 2",
        summary: "Summary",
        content: "Content",
        source_url: null,
        created_at: "2026-04-12T00:00:00.000Z",
        processing_duration: 4.2,
      });

    const handler = (await import("../server/api/showcase/results/[id].get")).default;
    const first = await handler(createEvent("page-1"));
    const second = await handler(createEvent("page-2"));

    expect(first).toMatchObject({ id: "page-1" });
    expect(second).toMatchObject({ id: "page-2" });
    expect(fetchShowcaseDetailMock).toHaveBeenCalledTimes(2);
  });

  it("falls back to the last successful snapshot when refresh fails", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-04-11T00:00:00.000Z"));
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "1";
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "api-key",
      notionDatabaseId: "database-id",
      showcaseCacheTtlSeconds: 0,
    });
    fetchShowcaseDetailMock
      .mockResolvedValueOnce({
        id: "page-1",
        title: "Cached title",
        summary: "Summary",
        content: "Content",
        source_url: null,
        created_at: "2026-04-11T00:00:00.000Z",
        processing_duration: 3.1,
      })
      .mockRejectedValueOnce(new Error("Notion unavailable"));

    const handler = (await import("../server/api/showcase/results/[id].get")).default;
    const first = await handler(createEvent("page-1"));
    vi.setSystemTime(new Date("2026-04-11T00:00:02.000Z"));
    const second = await handler(createEvent("page-1"));

    expect(first).toMatchObject({ title: "Cached title" });
    expect(second).toMatchObject({ title: "Cached title" });
    expect(fetchShowcaseDetailMock).toHaveBeenCalledTimes(2);
  });

  it.each([
    new TypeError("fetch failed"),
    new DOMException("The operation timed out", "TimeoutError"),
  ])("returns 502 on a cold failure (%s) and tries again on the next request", async (error) => {
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "api-key", notionDatabaseId: "database-id", showcaseCacheTtlSeconds: 600,
    });
    fetchShowcaseDetailMock
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce({ id: "page-1", content: "Recovered" });
    const handler = (await import("../server/api/showcase/results/[id].get")).default;
    await expect(handler(createEvent("page-1"))).rejects.toMatchObject({ statusCode: 502 });
    expect(fetchShowcaseDetailMock).toHaveBeenCalledTimes(1);
    await expect(handler(createEvent("page-1"))).resolves.toMatchObject({ content: "Recovered" });
    expect(fetchShowcaseDetailMock).toHaveBeenCalledTimes(2);
  });
  it("does not expose upstream secrets in errors or logs", async () => {
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "private-key", notionDatabaseId: "private-database", showcaseCacheTtlSeconds: 600,
    });
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    try {
      fetchShowcaseDetailMock.mockRejectedValue(new Error("private-key private-database raw-notion-body"));
      const handler = (await import("../server/api/showcase/results/[id].get")).default;
      await expect(handler(createEvent("page-1"))).rejects.toMatchObject({
        statusCode: 502, statusMessage: "Failed to load showcase detail.",
      });
      expect(setHeaderMock).toHaveBeenLastCalledWith(expect.anything(), "Cache-Control", "no-store");
      expect(log).toHaveBeenCalled();
      const output = JSON.stringify(log.mock.calls);
      for (const secret of ["private-key", "private-database", "raw-notion-body"]) {
        expect(output).not.toContain(secret);
      }
    } finally {
      log.mockRestore();
    }
  });
  it("keeps missing configuration private and uncacheable", async () => {
    for (const key of ["NOTION_API_KEY", "NUXT_NOTION_API_KEY", "NOTION_DATABASE_ID", "NUXT_NOTION_DATABASE_ID"]) {
      delete process.env[key];
    }
    runtimeConfigMock.mockReturnValue({});
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    try {
      const handler = (await import("../server/api/showcase/results/[id].get")).default;
      await expect(handler(createEvent("page-1"))).rejects.toMatchObject({
        statusCode: 500, statusMessage: "Showcase service is unavailable.",
      });
      expect(setHeaderMock).toHaveBeenLastCalledWith(expect.anything(), "Cache-Control", "no-store");
      expect(fetchShowcaseDetailMock).not.toHaveBeenCalled();
      expect(log).toHaveBeenCalled();
    } finally {
      log.mockRestore();
    }
  });

});
