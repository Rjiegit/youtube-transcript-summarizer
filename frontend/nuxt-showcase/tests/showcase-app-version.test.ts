import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useRuntimeConfigMock = vi.fn();

vi.stubGlobal("useHead", vi.fn());
vi.stubGlobal("useRuntimeConfig", useRuntimeConfigMock);

describe("showcase app version footer", () => {
  beforeEach(() => {
    vi.resetModules();
    useRuntimeConfigMock.mockReset();
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
});
