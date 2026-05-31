import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

type ReadMap = Record<string, { readAt: string }>;
const MAX_READ_ENTRIES = 500;

function createReadMap(size: number): ReadMap {
  const entries = Array.from({ length: size }, (_, index) => {
    const id = `result-${index + 1}`;
    const readAt = new Date(Date.UTC(2026, 3, 11, 0, 0, index)).toISOString();

    return [id, { readAt }] as const;
  });

  return Object.fromEntries(entries);
}

function createArticleReadMap(size: number): ReadMap {
  const entries = Array.from({ length: size }, (_, index) => {
    const articleNumber = index + 1;
    const readAt = new Date(Date.UTC(2026, 3, 11, 0, 0, index)).toISOString();

    return [
      [`result-${articleNumber}`, { readAt }],
      [`url:https://example.com/article-${articleNumber}`, { readAt }],
    ] as const;
  }).flat();

  return Object.fromEntries(entries);
}

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
      setRaw(key: string, value: string) {
        store.set(key, value);
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

  it("trims hydrated localStorage data to the most recent 500 entries", async () => {
    stubNuxtState();
    const sourceMap = createReadMap(MAX_READ_ENTRIES + 5);
    stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify(sourceMap),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds, readMap } = useReadResults();

    expect(readIds.value).toHaveLength(MAX_READ_ENTRIES);
    expect(Object.keys(readMap.value)).toHaveLength(MAX_READ_ENTRIES);
    expect(isRead("result-1")).toBe(false);
    expect(isRead("result-6")).toBe(true);
    expect(readIds.value[0]).toBe(`result-${MAX_READ_ENTRIES + 5}`);
  });

  it("keeps id and URL read keys for the latest 100 articles", async () => {
    stubNuxtState();
    stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify(createArticleReadMap(100)),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds } = useReadResults();

    expect(readIds.value).toHaveLength(200);
    expect(isRead("result-1")).toBe(true);
    expect(isRead("url:https://example.com/article-1")).toBe(true);
    expect(isRead("result-100")).toBe(true);
    expect(isRead("url:https://example.com/article-100")).toBe(true);
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

  it("marks many items as read and persists once", async () => {
    stubNuxtState();
    const storage = stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markManyAsRead, readMap } = useReadResults();

    markManyAsRead(["result-1", "result-2"]);

    expect(isRead("result-1")).toBe(true);
    expect(isRead("result-2")).toBe(true);
    expect(Object.keys(readMap.value)).toEqual(["result-1", "result-2"]);
    expect(storage.localStorageMock.setItem).toHaveBeenCalledTimes(1);
    expect(storage.readRaw("nuxt-showcase-read-results")).toContain("result-1");
    expect(storage.readRaw("nuxt-showcase-read-results")).toContain("result-2");
  });

  it("ignores empty values when marking many items as read", async () => {
    stubNuxtState();
    const storage = stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const { markManyAsRead, readIds } = useReadResults();

    markManyAsRead(["", "   "]);

    expect(readIds.value).toEqual([]);
    expect(storage.localStorageMock.setItem).not.toHaveBeenCalled();
  });

  it("keeps only the latest 500 read entries when new items are added", async () => {
    stubNuxtState();
    const storage = stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify(createReadMap(MAX_READ_ENTRIES)),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsRead, readIds, readMap } = useReadResults();

    markAsRead("result-501");

    expect(readIds.value).toHaveLength(MAX_READ_ENTRIES);
    expect(Object.keys(readMap.value)).toHaveLength(MAX_READ_ENTRIES);
    expect(isRead("result-1")).toBe(false);
    expect(isRead("result-501")).toBe(true);

    const persisted = JSON.parse(storage.readRaw("nuxt-showcase-read-results") || "{}") as ReadMap;
    expect(Object.keys(persisted)).toHaveLength(MAX_READ_ENTRIES);
    expect(persisted["result-1"]).toBeUndefined();
    expect(persisted["result-501"]).toBeDefined();
  });

  it("keeps only the latest 500 read entries when many new items are added", async () => {
    stubNuxtState();
    const storage = stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify(createReadMap(MAX_READ_ENTRIES)),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markManyAsRead, readIds } = useReadResults();

    markManyAsRead(["result-501", "result-502"]);

    expect(readIds.value).toHaveLength(MAX_READ_ENTRIES);
    expect(isRead("result-1")).toBe(false);
    expect(isRead("result-2")).toBe(false);
    expect(isRead("result-501")).toBe(true);
    expect(isRead("result-502")).toBe(true);

    const persisted = JSON.parse(storage.readRaw("nuxt-showcase-read-results") || "{}") as ReadMap;
    expect(Object.keys(persisted)).toHaveLength(MAX_READ_ENTRIES);
    expect(persisted["result-1"]).toBeUndefined();
    expect(persisted["result-2"]).toBeUndefined();
    expect(persisted["result-501"]).toBeDefined();
    expect(persisted["result-502"]).toBeDefined();
  });

  it("refreshes an existing item without increasing the stored read count", async () => {
    stubNuxtState();
    stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify(createReadMap(MAX_READ_ENTRIES)),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { markAsRead, readIds, readMap } = useReadResults();
    const previousReadAt = readMap.value["result-1"]?.readAt;

    markAsRead("result-1");

    expect(readIds.value).toHaveLength(MAX_READ_ENTRIES);
    expect(readMap.value["result-1"]?.readAt).toBeDefined();
    expect(readMap.value["result-1"]?.readAt).not.toBe(previousReadAt);
    expect(readIds.value[0]).toBe("result-1");
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

  it("refreshes ready state from localStorage without dropping in-memory reads", async () => {
    stubNuxtState();
    const storage = stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify({
        "result-from-storage": { readAt: "2026-04-11T00:00:00.000Z" },
      }),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsRead, refreshReadState } = useReadResults();

    markAsRead("result-from-memory");
    storage.setRaw("nuxt-showcase-read-results", JSON.stringify({
      "result-from-storage": { readAt: "2026-04-11T00:00:00.000Z" },
      "result-from-external": { readAt: "2026-04-12T00:00:00.000Z" },
    }));

    refreshReadState();

    expect(isRead("result-from-memory")).toBe(true);
    expect(isRead("result-from-storage")).toBe(true);
    expect(isRead("result-from-external")).toBe(true);
  });

  it("keeps in-memory reads when refreshing invalid localStorage", async () => {
    stubNuxtState();
    const storage = stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, markAsRead, refreshReadState } = useReadResults();

    markAsRead("result-from-memory");
    storage.setRaw("nuxt-showcase-read-results", "invalid-json");

    refreshReadState();

    expect(isRead("result-from-memory")).toBe(true);
  });

  it("trims refreshed localStorage data to the most recent 500 entries", async () => {
    stubNuxtState();
    const storage = stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const { isRead, readIds, refreshReadState } = useReadResults();

    storage.setRaw("nuxt-showcase-read-results", JSON.stringify(createReadMap(MAX_READ_ENTRIES + 5)));

    refreshReadState();

    expect(readIds.value).toHaveLength(MAX_READ_ENTRIES);
    expect(isRead("result-1")).toBe(false);
    expect(isRead(`result-${MAX_READ_ENTRIES + 5}`)).toBe(true);
  });

  it("increments read revision when read state changes", async () => {
    stubNuxtState();
    stubLocalStorage();

    const { useReadResults } = await import("../composables/useReadResults");
    const { markAsRead, markAsUnread, readRevision } = useReadResults();
    const initialRevision = readRevision.value;

    markAsRead("result-1");
    expect(readRevision.value).toBe(initialRevision + 1);

    markAsUnread("result-1");
    expect(readRevision.value).toBe(initialRevision + 2);
  });

  it("force refresh increments read revision even when storage is unchanged", async () => {
    stubNuxtState();
    stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify({
        "result-1": { readAt: "2026-04-11T00:00:00.000Z" },
      }),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { readRevision, refreshReadState } = useReadResults();
    const initialRevision = readRevision.value;

    refreshReadState({ forceRender: true });

    expect(readRevision.value).toBe(initialRevision + 1);
  });

  it("does not increment read revision when normal refresh finds no changes", async () => {
    stubNuxtState();
    stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify({
        "result-1": { readAt: "2026-04-11T00:00:00.000Z" },
      }),
    });

    const { useReadResults } = await import("../composables/useReadResults");
    const { readRevision, refreshReadState } = useReadResults();
    const initialRevision = readRevision.value;

    refreshReadState();

    expect(readRevision.value).toBe(initialRevision);
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

  it("keeps in-memory read state when client storage hydrates later", async () => {
    stubNuxtState();
    vi.stubGlobal("window", undefined);

    const { useReadResults } = await import("../composables/useReadResults");
    const first = useReadResults();

    first.markAsRead("result-from-detail");
    expect(first.isRead("result-from-detail")).toBe(true);

    const storage = stubLocalStorage({
      "nuxt-showcase-read-results": JSON.stringify({
        "result-from-storage": { readAt: "2026-04-11T00:00:00.000Z" },
      }),
    });
    const second = useReadResults();

    expect(second.isRead("result-from-detail")).toBe(true);
    expect(second.isRead("result-from-storage")).toBe(true);
    expect(storage.readRaw("nuxt-showcase-read-results")).toContain("result-from-detail");
  });
});
