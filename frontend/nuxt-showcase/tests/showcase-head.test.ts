import { defineComponent, h, Suspense } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

const useFetchMock = vi.fn();
const useRouteMock = vi.fn();
const useHeadMock = vi.fn();
const useRuntimeConfigMock = vi.fn();
const markAsReadMock = vi.fn();
let readResultIds = new Set<string>();
const SITE_NAME = "影片筆記庫";
const DEFAULT_DESCRIPTION = "收藏從影片整理出的重點筆記";

vi.mock("../composables/useReadResults", () => ({
  useReadResults: () => ({
    isRead: vi.fn((id: string) => readResultIds.has(id)),
    isReady: { value: true },
    readIds: { value: [] },
    readMap: {
      value: Object.fromEntries(
        [...readResultIds].map((id) => [id, { readAt: "2026-04-11T00:00:00.000Z" }]),
      ),
    },
    readRevision: { value: 0 },
    markAsRead: markAsReadMock,
    markManyAsRead: vi.fn(),
    markAsUnread: vi.fn(),
    refreshReadState: vi.fn(),
  }),
}));

vi.stubGlobal("useFetch", useFetchMock);
vi.stubGlobal("useRoute", useRouteMock);
vi.stubGlobal("useHead", useHeadMock);
vi.stubGlobal("useRuntimeConfig", useRuntimeConfigMock);
vi.stubGlobal("useNuxtApp", () => ({
  hook: vi.fn(() => vi.fn()),
}));
vi.stubGlobal("createError", (input: { statusCode: number; statusMessage: string }) => {
  const error = new Error(input.statusMessage);
  return Object.assign(error, input);
});

describe("showcase head metadata", () => {
  beforeEach(() => {
    readResultIds = new Set<string>();
    vi.clearAllMocks();
    const stateStore = new Map<string, ReturnType<typeof ref>>();
    vi.stubGlobal("useState", vi.fn((key: string, init?: () => unknown) => {
      if (!stateStore.has(key)) {
        stateStore.set(key, ref(init ? init() : undefined));
      }
      return stateStore.get(key)!;
    }));
    useRouteMock.mockReturnValue({
      fullPath: "/",
    });
    useRuntimeConfigMock.mockReturnValue({
      public: {
        buildDate: "2026.06.26",
        commitSha: "abc123456789",
      },
    });
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
    expect(headArg.titleTemplate()).toBe(SITE_NAME);
    expect(headArg.titleTemplate(SITE_NAME)).toBe(SITE_NAME);
    expect(headArg.titleTemplate("Second result")).toBe(`Second result | ${SITE_NAME}`);
    expect(headArg.meta).toEqual(expect.arrayContaining([
      expect.objectContaining({ name: "description", content: DEFAULT_DESCRIPTION }),
      expect.objectContaining({ property: "og:site_name", content: SITE_NAME }),
    ]));
    expect(headArg.link).toEqual(expect.arrayContaining([
      expect.objectContaining({ rel: "stylesheet", href: "/showcase.css" }),
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
      title: SITE_NAME,
      meta: expect.arrayContaining([
        expect.objectContaining({ name: "description", content: DEFAULT_DESCRIPTION }),
        expect.objectContaining({ property: "og:title", content: SITE_NAME }),
        expect.objectContaining({ property: "og:description", content: DEFAULT_DESCRIPTION }),
        expect.objectContaining({ name: "twitter:card", content: "summary" }),
        expect.objectContaining({ name: "twitter:title", content: SITE_NAME }),
        expect.objectContaining({ name: "twitter:description", content: DEFAULT_DESCRIPTION }),
      ]),
    }));
    const homeHeadArg = useHeadMock.mock.calls.find(([arg]) => arg?.title === SITE_NAME)?.[0];
    expect(homeHeadArg?.meta).not.toEqual(expect.arrayContaining([
      expect.objectContaining({ property: "og:image" }),
      expect.objectContaining({ name: "twitter:image" }),
    ]));
  });

  it("does not show unread and total counts on the home page", async () => {
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

    expect(wrapper.find('[data-testid="unread-count"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="total-count"]').exists()).toBe(false);
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

  it("strips markdown syntax from detail metadata descriptions", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "result-2-page-id" },
    });
    useFetchMock.mockReturnValue({
      data: ref({
        id: "result-2-page-id",
        title: "Second result",
        summary: "",
        content: "## 重點整理\n\n這是一段包含 [參考連結](https://example.com/docs) 與 `inline_code()` 的內容。",
        source_url: null,
        created_at: "2026-03-28T12:00:00.000Z",
        processing_duration: 12.4,
      }),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await import("../pages/results/[id].vue?t=" + Date.now() + Math.random());
    mount(pageModule.default, {
      global: {
        stubs: {
          NuxtLink: true,
        },
      },
    });

    const lastCall = useHeadMock.mock.calls.at(-1)?.[0];
    expect(lastCall?.meta).toEqual(expect.arrayContaining([
      expect.objectContaining({
        name: "description",
        content: "重點整理 這是一段包含 參考連結 與 inline_code() 的內容。",
      }),
      expect.objectContaining({
        property: "og:description",
        content: "重點整理 這是一段包含 參考連結 與 inline_code() 的內容。",
      }),
    ]));
  });

  it("uses the default description when detail content is empty", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "result-2-page-id" },
    });
    useFetchMock.mockReturnValue({
      data: ref({
        id: "result-2-page-id",
        title: "Second result",
        summary: "",
        content: "",
        source_url: null,
        created_at: "2026-03-28T12:00:00.000Z",
        processing_duration: 12.4,
      }),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await import("../pages/results/[id].vue?t=" + Date.now() + Math.random());
    mount(pageModule.default, {
      global: {
        stubs: {
          NuxtLink: true,
        },
      },
    });

    const lastCall = useHeadMock.mock.calls.at(-1)?.[0];
    expect(lastCall?.meta).toEqual(expect.arrayContaining([
      expect.objectContaining({ name: "description", content: DEFAULT_DESCRIPTION }),
      expect.objectContaining({ property: "og:description", content: DEFAULT_DESCRIPTION }),
      expect.objectContaining({ name: "twitter:description", content: DEFAULT_DESCRIPTION }),
    ]));
  });
});
