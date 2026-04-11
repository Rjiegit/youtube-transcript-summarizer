import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

type ReadMap = Record<string, { readAt: string }>;

describe("useReadResults", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
  });

  function stubNuxtState() {
    const stateStore = new Map<string, ReturnType<typeof ref>>();

    vi.stubGlobal("useState", vi.fn((key: string, init?: () => unknown) => {
      if (!stateStore.has(key)) {
        stateStore.set(key, ref(init ? init() : undefined));
      }
      return stateStore.get(key)!;
    }));
  }

  function stubLocalStorage(initial: Record<string, string> = {}) {
    const store = new Map(Object.entries(initial));
    const localStorageMock = {
      getItem: vi.fn((key: string) => store.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => {
        store.set(key, value);
      }),
      removeItem: vi.fn((key: string) => {
        store.delete(key);
      }),
    };

    vi.stubGlobal("localStorage", localStorageMock);
    vi.stubGlobal("window", { localStorage: localStorageMock });

    return {
      localStorageMock,
      readRaw(key: string) {
        return store.get(key) ?? null;
      },
    };
  }

  it("starts unread and ready when localStorage is available but empty", async () => {
    stubNuxtState();
    stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds, isReady } = useReadResults();

    expect(isReady.value).toBe(true);
    expect(isRead("result-1")).toBe(false);
    expect(readIds.value).toEqual([]);
  });

  it("hydrates read state from localStorage and marks the composable as ready", async () => {
    stubNuxtState();
    stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify({
        "result-9": { readAt: "2026-04-11T00:00:00.000Z" },
      }),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds, isReady } = useReadResults();

    expect(isReady.value).toBe(true);
    expect(isRead("result-9")).toBe(true);
    expect(readIds.value).toEqual(["result-9"]);
  });

  it("marks an item as read and persists it to localStorage", async () => {
    stubNuxtState();
    const storage = stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsRead, readMap, isReady } = useReadResults();

    expect(isReady.value).toBe(true);

    markAsRead("result-1");

    expect(isRead("result-1")).toBe(true);
    expect(readMap.value["result-1"]).toBeDefined();
    expect(storage.localStorageMock.setItem).toHaveBeenCalled();
    expect(storage.readRaw("nuxt-showcase-read-results")).toContain("result-1");
  });

  it("removes an item when marked unread and updates localStorage", async () => {
    stubNuxtState();
    const storage = stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify({
        "result-1": { readAt: "2026-04-11T00:00:00.000Z" },
      }),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsUnread } = useReadResults();

    markAsUnread("result-1");

    expect(isRead("result-1")).toBe(false);
    expect(storage.readRaw("nuxt-showcase-read-results")).toBeNull();
    expect(storage.localStorageMock.removeItem).toHaveBeenCalledWith("nuxt-showcase-read-results");
  });

  it("falls back safely when localStorage state is invalid", async () => {
    stubNuxtState();
    stubLocalStorage({
      "nuxt-showcase-read-results": "invalid-json",
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds, isReady } = useReadResults();

    expect(isReady.value).toBe(true);
    expect(isRead("result-1")).toBe(false);
    expect(readIds.value).toEqual([]);
  });

  it("shares read state across multiple composable calls and persists it to localStorage", async () => {
    stubNuxtState();
    const storage = stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const first = useReadResults();
    const second = useReadResults();

    first.markAsRead("result-2");

    expect(first.isRead("result-2")).toBe(true);
    expect(second.isRead("result-2")).toBe(true);
    expect(second.readIds.value).toEqual(["result-2"]);
    expect(storage.readRaw("nuxt-showcase-read-results")).toContain("result-2");
  });
});
