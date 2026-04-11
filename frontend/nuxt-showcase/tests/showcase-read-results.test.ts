import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

describe("useReadResults", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("returns unread when cookie state is empty", async () => {
    vi.stubGlobal("useCookie", vi.fn(() => ref({})));

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds } = useReadResults();

    expect(isRead("result-1")).toBe(false);
    expect(readIds.value).toEqual([]);
  });

  it("marks an item as read and persists it to cookie state", async () => {
    const cookieRef = ref({});
    vi.stubGlobal("useCookie", vi.fn(() => cookieRef));

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsRead, readMap } = useReadResults();

    markAsRead("result-1");

    expect(isRead("result-1")).toBe(true);
    expect(readMap.value["result-1"]).toBeDefined();
    expect(cookieRef.value).toHaveProperty("result-1");
  });

  it("removes an item when marked unread", async () => {
    const cookieRef = ref({
      "result-1": { readAt: "2026-04-11T00:00:00.000Z" },
    });
    vi.stubGlobal("useCookie", vi.fn(() => cookieRef));

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsUnread } = useReadResults();

    markAsUnread("result-1");

    expect(isRead("result-1")).toBe(false);
    expect(cookieRef.value).toEqual({});
  });

  it("falls back safely when cookie state is invalid", async () => {
    vi.stubGlobal("useCookie", vi.fn(() => ref("invalid-cookie-value")));

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds } = useReadResults();

    expect(isRead("result-1")).toBe(false);
    expect(readIds.value).toEqual([]);
  });
});
