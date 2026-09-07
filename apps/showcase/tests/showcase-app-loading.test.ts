import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

describe("global app loading state", () => {
  beforeEach(() => {
    vi.resetModules();
    const stateStore = new Map<string, ReturnType<typeof ref>>();
    vi.stubGlobal("useState", vi.fn((key: string, init?: () => unknown) => {
      if (!stateStore.has(key)) {
        stateStore.set(key, ref(init ? init() : undefined));
      }
      return stateStore.get(key)!;
    }));
  });

  it("stays active until every overlapping loading source finishes", async () => {
    const { useAppLoading } = await import("../composables/useAppLoading");
    const loading = useAppLoading();

    loading.start("route-navigation");
    loading.start("showcase-list-refresh");
    expect(loading.isLoading.value).toBe(true);

    loading.finish("route-navigation");
    expect(loading.isLoading.value).toBe(true);

    loading.finish("showcase-list-refresh");
    expect(loading.isLoading.value).toBe(false);
  });

  it("reference-counts repeated starts from the same source", async () => {
    const { useAppLoading } = await import("../composables/useAppLoading");
    const loading = useAppLoading();

    loading.start("showcase-detail-data");
    loading.start("showcase-detail-data");
    loading.finish("showcase-detail-data");
    expect(loading.isLoading.value).toBe(true);

    loading.finish("showcase-detail-data");
    loading.finish("showcase-detail-data");
    expect(loading.isLoading.value).toBe(false);
  });
});
