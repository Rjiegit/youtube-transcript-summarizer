import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { reactive, ref } from "vue";

const useRuntimeConfigMock = vi.fn();
const loadingHooks = new Map<string, () => void>();
const route = reactive({ path: "/", fullPath: "/" });

vi.stubGlobal("useHead", vi.fn());
vi.stubGlobal("useRuntimeConfig", useRuntimeConfigMock);
vi.stubGlobal("useRoute", () => route);
vi.stubGlobal("useNuxtApp", () => ({
  hook: vi.fn((name: string, callback: () => void) => {
    loadingHooks.set(name, callback);
    return vi.fn();
  }),
}));

describe("showcase app version footer", () => {
  beforeEach(() => {
    vi.resetModules();
    useRuntimeConfigMock.mockReset();
    loadingHooks.clear();
    route.path = "/";
    route.fullPath = "/";
    const stateStore = new Map<string, ReturnType<typeof ref>>();
    vi.stubGlobal("useState", vi.fn((key: string, init?: () => unknown) => {
      if (!stateStore.has(key)) {
        stateStore.set(key, ref(init ? init() : undefined));
      }
      return stateStore.get(key)!;
    }));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  async function mountApp() {
    const appModule = await import("../app.vue?t=" + Date.now() + Math.random());
    return mount(appModule.default, {
      global: {
        stubs: {
          NuxtPage: {
            template: "<main class=\"showcase-shell\">content</main>",
          },
        },
      },
    });
  }

  it("renders the build date and shortened commit sha in the footer", async () => {
    useRuntimeConfigMock.mockReturnValue({
      public: {
        buildDate: "2026.06.26",
        commitSha: "abc123456789",
      },
    });

    const wrapper = await mountApp();

    expect(wrapper.get('[data-testid="app-version"]').text()).toBe("2026.06.26 · abc1234");
  });

  it("falls back to local when the commit sha is missing", async () => {
    useRuntimeConfigMock.mockReturnValue({
      public: {
        buildDate: "2026.06.26",
        commitSha: "",
      },
    });

    const wrapper = await mountApp();

    expect(wrapper.get('[data-testid="app-version"]').text()).toBe("2026.06.26 · local");
  });

  it("covers and locks the page with a spinner overlay during route loading", async () => {
    vi.useFakeTimers();
    useRuntimeConfigMock.mockReturnValue({ public: {} });
    const wrapper = await mountApp();

    expect(wrapper.find('[data-testid="app-loading-overlay"]').exists()).toBe(false);
    loadingHooks.get("page:loading:start")?.();
    await wrapper.vm.$nextTick();

    const overlay = wrapper.get('[data-testid="app-loading-overlay"]');
    expect(overlay.classes()).toContain("app-loading-skeleton--list");
    expect(overlay.find(".app-loading-skeleton__grid").exists()).toBe(true);
    expect(overlay.find(".app-loading-skeleton__sr-only").text()).toBe("頁面載入中");
    expect(wrapper.find('[data-testid="app-loading-progress"]').exists()).toBe(false);
    expect(wrapper.find(".app-loading-status").exists()).toBe(false);
    expect(wrapper.get('[data-testid="app-content"]').classes()).toContain("app-frame__content--loading");
    expect(wrapper.get('[data-testid="app-content"]').attributes("aria-busy")).toBe("true");
    expect(wrapper.get('[data-testid="app-content"]').attributes("inert")).toBeDefined();

    vi.advanceTimersByTime(100);
    loadingHooks.get("page:loading:end")?.();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="app-loading-overlay"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="app-content"]').classes()).toContain("app-frame__content--loading");
    expect(wrapper.get('[data-testid="app-content"]').attributes("aria-busy")).toBe("true");
    expect(wrapper.get('[data-testid="app-content"]').attributes("inert")).toBeDefined();

    vi.advanceTimersByTime(399);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="app-loading-overlay"]').exists()).toBe(true);

    vi.advanceTimersByTime(1);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="app-loading-overlay"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="app-content"]').classes()).not.toContain("app-frame__content--loading");
    expect(wrapper.get('[data-testid="app-content"]').attributes("aria-busy")).toBe("false");
    expect(wrapper.get('[data-testid="app-content"]').attributes("inert")).toBeUndefined();
  });

  it("keeps the loading notice visible when another load starts before it hides", async () => {
    vi.useFakeTimers();
    useRuntimeConfigMock.mockReturnValue({ public: {} });
    const wrapper = await mountApp();

    loadingHooks.get("page:loading:start")?.();
    vi.advanceTimersByTime(100);
    loadingHooks.get("page:loading:end")?.();
    vi.advanceTimersByTime(200);
    loadingHooks.get("page:loading:start")?.();
    await wrapper.vm.$nextTick();

    vi.advanceTimersByTime(200);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="app-loading-overlay"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="app-content"]').classes()).toContain("app-frame__content--loading");
  });

  it("uses the article skeleton on detail routes", async () => {
    vi.useFakeTimers();
    route.path = "/results/result-1";
    route.fullPath = route.path;
    useRuntimeConfigMock.mockReturnValue({ public: {} });
    const wrapper = await mountApp();

    loadingHooks.get("page:loading:start")?.();
    await wrapper.vm.$nextTick();

    const overlay = wrapper.get('[data-testid="app-loading-overlay"]');
    expect(overlay.classes()).toContain("app-loading-skeleton--detail");
    expect(overlay.find(".app-loading-skeleton__detail").exists()).toBe(true);
    expect(overlay.find(".app-loading-skeleton__grid").exists()).toBe(false);
  });
});
