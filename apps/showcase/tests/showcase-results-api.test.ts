import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ShowcaseApiResponse } from "../types/showcase";

const runtimeConfigMock = vi.fn();
const setHeaderMock = vi.fn();
const fetchLatestCompletedResultsMock = vi.fn();

vi.mock("../server/utils/notion", () => ({
  fetchLatestCompletedResults: fetchLatestCompletedResultsMock,
}));

vi.mock("h3", async () => {
  const actual = await vi.importActual<typeof import("h3")>("h3");
  return {
    ...actual,
    setHeader: setHeaderMock,
  };
});

vi.stubGlobal("useRuntimeConfig", runtimeConfigMock);

const cachedResponse: ShowcaseApiResponse = {
  items: [
    {
      id: "cached-result",
      title: "Cached result",
      summary: "Cached summary.",
      source_url: "https://example.com/cached",
      created_at: "2026-04-11T00:00:00.000Z",
      processing_duration: 3.1,
    },
  ],
  generated_at: "2026-04-11T00:00:00.000Z",
  cache_ttl_seconds: 600,
};

const refreshedResponse: ShowcaseApiResponse = {
  items: [
    {
      id: "refreshed-result",
      title: "Refreshed result",
      summary: "Refreshed summary.",
      source_url: "https://example.com/refreshed",
      created_at: "2026-04-12T00:00:00.000Z",
      processing_duration: 4.2,
    },
  ],
  generated_at: "2026-04-12T00:00:00.000Z",
  cache_ttl_seconds: 600,
};

describe("showcase results API cache", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
    runtimeConfigMock.mockReset();
    setHeaderMock.mockReset();
    fetchLatestCompletedResultsMock.mockReset();
    process.env = { ...originalEnv };
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "600";
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "api-key",
      notionDatabaseId: "database-id",
      showcaseCacheTtlSeconds: 0,
    });
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  function createEvent(refresh = false) {
    return {
      node: {
        req: {
          url: refresh ? "/api/showcase/results?refresh=1&ts=123" : "/api/showcase/results",
        },
      },
    };
  }

  it("force refreshes the cached results when refresh=1 is requested", async () => {
    fetchLatestCompletedResultsMock
      .mockResolvedValueOnce(cachedResponse)
      .mockResolvedValueOnce(refreshedResponse);

    const handler = (await import("../server/api/showcase/results.get")).default;
    expect(await handler(createEvent())).toMatchObject({ items: [{ id: "cached-result" }] });

    const refreshed = await handler(createEvent(true));

    expect(refreshed).toMatchObject({ items: [{ id: "refreshed-result" }] });
    expect(fetchLatestCompletedResultsMock).toHaveBeenCalledTimes(2);
    expect(setHeaderMock).toHaveBeenLastCalledWith(
      expect.anything(),
      "Cache-Control",
      "no-store",
    );
  });

  it("falls back to the last successful results snapshot when force refresh fails", async () => {
    fetchLatestCompletedResultsMock
      .mockResolvedValueOnce(cachedResponse)
      .mockRejectedValueOnce(new Error("Notion unavailable"));

    const handler = (await import("../server/api/showcase/results.get")).default;
    expect(await handler(createEvent())).toMatchObject({ items: [{ id: "cached-result" }] });
    const fallback = await handler(createEvent(true));

    expect(fallback).toMatchObject({ items: [{ id: "cached-result" }] });
    expect(fetchLatestCompletedResultsMock).toHaveBeenCalledTimes(2);
  });
});
