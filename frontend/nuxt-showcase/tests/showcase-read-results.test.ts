import { beforeEach, describe, expect, it, vi } from "vitest";

describe("useReadResults", () => {
  beforeEach(() => {
    vi.resetModules();
    window.localStorage.clear();
  });

  it("returns unread when localStorage is empty", async () => {
    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds } = useReadResults();

    expect(isRead("result-1")).toBe(false);
    expect(readIds.value).toEqual([]);
  });

  it("marks an item as read and persists it", async () => {
    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsRead, readMap } = useReadResults();

    markAsRead("result-1");

    expect(isRead("result-1")).toBe(true);
    expect(readMap.value["result-1"]).toBeDefined();
    expect(window.localStorage.getItem("nuxt-showcase:read-results")).toContain("result-1");
  });

  it("removes an item when marked unread", async () => {
    window.localStorage.setItem("nuxt-showcase:read-results", JSON.stringify({
      "result-1": { readAt: "2026-04-11T00:00:00.000Z" },
    }));

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsUnread } = useReadResults();

    markAsUnread("result-1");

    expect(isRead("result-1")).toBe(false);
    expect(window.localStorage.getItem("nuxt-showcase:read-results")).toBe("{}");
  });

  it("falls back safely when localStorage contains invalid JSON", async () => {
    window.localStorage.setItem("nuxt-showcase:read-results", "{invalid-json");

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds } = useReadResults();

    expect(isRead("result-1")).toBe(false);
    expect(readIds.value).toEqual([]);
  });
});
