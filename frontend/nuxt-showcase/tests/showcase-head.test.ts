import { defineComponent, h, Suspense } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

const useFetchMock = vi.fn();
const useRouteMock = vi.fn();
const useHeadMock = vi.fn();
const markAsReadMock = vi.fn();
let readResultIds = new Set<string>();

vi.mock("../composables/useReadResults", () => ({
  useReadResults: () => ({
    isRead: vi.fn((id: string) => readResultIds.has(id)),
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
  beforeEach(() => {
    readResultIds = new Set<string>();
    vi.clearAllMocks();
  });

  it("uses the global title template without the nuxt-showcase suffix", async () => {
    const appModule = await import("../app.vue?t=" + Date.now());
    mount(appModule.default, {
      global: {
        stubs: {
          NuxtPage: true,
        },
      },
    });

    const headArg = useHeadMock.mock.calls[0]?.[0];
    expect(headArg.titleTemplate()).toBe("影片知識庫");
    expect(headArg.titleTemplate("影片知識庫")).toBe("影片知識庫");
    expect(headArg.titleTemplate("Second result")).toBe("Second result | 影片知識庫");
    expect(headArg.link).toEqual(expect.arrayContaining([
      expect.objectContaining({ rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }),
      expect.objectContaining({ rel: "shortcut icon", type: "image/x-icon", href: "/favicon.ico" }),
      expect.objectContaining({ rel: "apple-touch-icon", sizes: "180x180", href: "/apple-touch-icon.png" }),
      expect.objectContaining({ rel: "manifest", href: "/site.webmanifest" }),
    ]));
  });

  it("sets the home page title", async () => {
    useFetchMock.mockReturnValue({
      data: ref({
        items: [
          {
            id: "result-2-page-id",
            title: "Second result",
            summary: "Summary",
            source_url: null,
            created_at: "2026-04-11T10:53:00.000Z",
            processing_duration: 12.4,
          },
        ],
        generated_at: "2026-04-11T12:00:00.000Z",
        cache_ttl_seconds: 3600,
      }),
      pending: ref(false),
      error: ref(null),
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
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(useHeadMock).toHaveBeenCalledWith(expect.objectContaining({
      title: "影片知識庫",
      meta: expect.arrayContaining([
        expect.objectContaining({ name: "description" }),
        expect.objectContaining({ property: "og:title", content: "影片知識庫" }),
        expect.objectContaining({ property: "og:description" }),
        expect.objectContaining({ name: "twitter:card", content: "summary" }),
        expect.objectContaining({ name: "twitter:title", content: "影片知識庫" }),
        expect.objectContaining({ name: "twitter:description" }),
      ]),
    }));
    const homeHeadArg = useHeadMock.mock.calls.find(([arg]) => arg?.title === "影片知識庫")?.[0];
    expect(homeHeadArg?.meta).not.toEqual(expect.arrayContaining([
      expect.objectContaining({ property: "og:image" }),
      expect.objectContaining({ name: "twitter:image" }),
    ]));
  });

  it("shows unread and total counts on the home page", async () => {
    readResultIds = new Set(["result-2"]);
    useFetchMock.mockReturnValue({
      data: ref({
        items: [
          {
            id: "result-1",
            title: "First result",
            summary: "Summary",
            source_url: null,
            created_at: "2026-04-12T10:53:00.000Z",
            processing_duration: 10,
          },
          {
            id: "result-2",
            title: "Second result",
            summary: "Summary",
            source_url: null,
            created_at: "2026-04-11T10:53:00.000Z",
            processing_duration: 12.4,
          },
          {
            id: "result-3",
            title: "Third result",
            summary: "Summary",
            source_url: null,
            created_at: "2026-04-10T10:53:00.000Z",
            processing_duration: 9.6,
          },
        ],
        generated_at: "2026-04-12T12:00:00.000Z",
        cache_ttl_seconds: 3600,
      }),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await import("../pages/index.vue?t=" + Date.now() + Math.random());
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
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="unread-count"]').text()).toContain("2 篇");
    expect(wrapper.get('[data-testid="total-count"]').text()).toContain("3 篇");
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
    expect(lastCall?.meta).toEqual(expect.arrayContaining([
      expect.objectContaining({ name: "description", content: "Summary" }),
      expect.objectContaining({ property: "og:title", content: "Second result" }),
      expect.objectContaining({ property: "og:description", content: "Summary" }),
      expect.objectContaining({ name: "twitter:card", content: "summary" }),
      expect.objectContaining({ name: "twitter:title", content: "Second result" }),
      expect.objectContaining({ name: "twitter:description", content: "Summary" }),
    ]));
    expect(lastCall?.meta).not.toEqual(expect.arrayContaining([
      expect.objectContaining({ property: "og:image" }),
      expect.objectContaining({ name: "twitter:image" }),
    ]));
  });
});
