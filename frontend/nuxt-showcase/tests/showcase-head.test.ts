import { defineComponent, h, Suspense } from "vue";
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { ref } from "vue";

const useFetchMock = vi.fn();
const useRouteMock = vi.fn();
const useHeadMock = vi.fn();
const markAsReadMock = vi.fn();

vi.mock("../composables/useReadResults", () => ({
  useReadResults: () => ({
    isRead: vi.fn(() => false),
    isReady: { value: true },
    readIds: { value: [] },
    readMap: { value: {} },
    markAsRead: markAsReadMock,
    markAsUnread: vi.fn(),
  }),
}));

vi.stubGlobal("useFetch", useFetchMock);
vi.stubGlobal("useRoute", useRouteMock);
vi.stubGlobal("useHead", useHeadMock);
vi.stubGlobal("createError", (input: { statusCode: number; statusMessage: string }) => {
  const error = new Error(input.statusMessage);
  return Object.assign(error, input);
});

describe("showcase head metadata", () => {
  it("sets the home page title", async () => {
    useFetchMock.mockResolvedValue({
      data: { value: { items: [], generated_at: "", cache_ttl_seconds: 3600 } },
      pending: { value: false },
      error: { value: null },
    });

    const pageModule = await import("../pages/index.vue?t=" + Date.now());
    const wrapper = mount(defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      render() {
        return h(Suspense, null, {
          default: () => h(pageModule.default),
        });
      },
    }), {
      global: {
        stubs: {
          ClientOnly: {
            template: "<div><slot /><slot name=\"fallback\" /></div>",
          },
          ShowcaseCard: true,
        },
      },
    });
    await Promise.resolve();
    await wrapper.vm.$nextTick();

    expect(useHeadMock).toHaveBeenCalledWith(expect.objectContaining({
      title: "影片知識庫",
    }));
  });

  it("sets the detail title from the loaded item", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "result-2-page-id" },
    });
    useFetchMock.mockReturnValue({
      data: ref({
        id: "result-2-page-id",
        title: "Second result",
        summary: "Summary",
        content: "Content",
        source_url: null,
        created_at: "2026-03-28T12:00:00.000Z",
        processing_duration: 12.4,
      }),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await import("../pages/results/[id].vue?t=" + Date.now());
    mount(pageModule.default, {
      global: {
        stubs: {
          NuxtLink: true,
        },
      },
    });

    const lastCall = useHeadMock.mock.calls.at(-1)?.[0];
    expect(lastCall?.title?.value ?? lastCall?.title).toBe("Second result");
  });
});
