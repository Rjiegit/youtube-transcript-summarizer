import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

const useRuntimeConfigMock = vi.fn();
const loadingHooks = new Map<string, () => void>();

vi.stubGlobal("useHead", vi.fn());
vi.stubGlobal("useRuntimeConfig", useRuntimeConfigMock);
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
    const stateStore = new Map<string, ReturnType<typeof ref>>();
    vi.stubGlobal("useState", vi.fn((key: string, init?: () => unknown) => {
      if (!stateStore.has(key)) {
        stateStore.set(key, ref(init ? init() : undefined));
      }
      return stateStore.get(key)!;
    }));
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

  it("shows one top progress bar and dims content during route loading", async () => {
    useRuntimeConfigMock.mockReturnValue({ public: {} });
    const wrapper = await mountApp();

    expect(wrapper.get('[data-testid="app-loading-progress"]').isVisible()).toBe(false);
    loadingHooks.get("page:loading:start")?.();
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="app-loading-progress"]').attributes("style") || "").not.toContain("display: none");
    expect(wrapper.get('[data-testid="app-content"]').classes()).toContain("app-frame__content--loading");
    expect(wrapper.get('[data-testid="app-content"]').attributes("aria-busy")).toBe("true");

    loadingHooks.get("page:loading:end")?.();
    await wrapper.vm.$nextTick();
    expect(wrapper.get('[data-testid="app-loading-progress"]').isVisible()).toBe(false);
  });
});
