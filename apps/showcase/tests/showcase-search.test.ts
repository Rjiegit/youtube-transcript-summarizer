import { mount } from "@vue/test-utils";
import { defineComponent, h, Suspense } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises } from "@vue/test-utils";
import { ref } from "vue";

const useFetchMock = vi.fn();
const useRouteMock = vi.fn();

vi.mock("../composables/useReadResults", () => ({
  useReadResults: () => ({
    isRead: vi.fn(() => false),
    isReady: { value: true },
    readIds: { value: [] },
    readMap: { value: {} },
    readRevision: { value: 0 },
    isRemoteSyncEnabled: { value: false },
    remoteSyncStatus: { value: "local" },
    markAsRead: vi.fn(),
    markManyAsRead: vi.fn(),
    markAsUnread: vi.fn(),
    refreshReadState: vi.fn(),
    setRemoteSyncEnabled: vi.fn(),
    authenticateRemoteSync: vi.fn(),
    syncRemoteState: vi.fn(),
  }),
}));

vi.stubGlobal("useFetch", useFetchMock);
vi.stubGlobal("useRoute", useRouteMock);
vi.stubGlobal("useHead", vi.fn());

const nuxtLinkStub = defineComponent({
  props: {
    to: {
      type: String,
      required: true,
    },
    custom: {
      type: Boolean,
      default: false,
    },
  },
  setup(props) {
    return {
      href: props.to,
      navigate: () => Promise.resolve(),
    };
  },
  template: `
    <template v-if="custom">
      <slot :href="href" :navigate="navigate"></slot>
    </template>
    <a v-else :href="to"><slot /></a>
  `,
});

describe("showcase title search", () => {
  beforeEach(() => {
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
    useFetchMock.mockReturnValue({
      data: ref({
        items: [
          {
            id: "result-1",
            title: "OpenAI Whisper Pipeline",
            summary: "Pipeline summary",
            source_url: null,
            created_at: "2026-04-12T10:53:00.000Z",
            processing_duration: 10,
          },
          {
            id: "result-2",
            title: "Nuxt Showcase SEO Notes",
            summary: "SEO summary",
            source_url: null,
            created_at: "2026-04-11T10:53:00.000Z",
            processing_duration: 12.4,
          },
        ],
        generated_at: "2026-04-12T12:00:00.000Z",
        cache_ttl_seconds: 3600,
      }),
      pending: ref(false),
      error: ref(null),
    });
  });

  async function mountIndexPage() {
    const pageModule = await import("../pages/index.vue?t=" + Date.now() + Math.random());
    const wrapper = mount(defineComponent({
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
          NuxtLink: nuxtLinkStub,
        },
      },
    });
    await flushPromises();
    await wrapper.vm.$nextTick();
    return wrapper;
  }

  it("filters the home page list by title only", async () => {
    const wrapper = await mountIndexPage();

    await wrapper.get('[data-testid="title-search-input"]').setValue("seo");

    expect(wrapper.text()).toContain("Nuxt Showcase SEO Notes");
    expect(wrapper.text()).not.toContain("OpenAI Whisper Pipeline");
  });

  it("restores all results when the title search is cleared", async () => {
    const wrapper = await mountIndexPage();
    const input = wrapper.get('[data-testid="title-search-input"]');

    await input.setValue("whisper");
    await input.setValue("   ");

    expect(wrapper.text()).toContain("Nuxt Showcase SEO Notes");
    expect(wrapper.text()).toContain("OpenAI Whisper Pipeline");
  });

  it("highlights matching text and removes highlights when cleared", async () => {
    const wrapper = await mountIndexPage();
    const input = wrapper.get('[data-testid="title-search-input"]');
    await input.setValue("  whisper  ");
    const titles = wrapper.findAll(".showcase-card__title");
    expect(titles.length).toBeGreaterThan(0);
    for (const title of titles) {
      expect(title.get("mark").text()).toBe("Whisper");
      expect(title.text()).toBe("OpenAI Whisper Pipeline");
    }
    await input.setValue("");
    expect(wrapper.find("mark").exists()).toBe(false);
  });

  it("highlights Unicode matches included by the title filter", async () => {
    useFetchMock().data.value.items[0].title = "İstanbul";
    const wrapper = await mountIndexPage();
    await wrapper.get('[data-testid="title-search-input"]').setValue("i");
    const title = wrapper.get(".showcase-card__title");
    expect(title.text()).toBe("İstanbul");
    expect(title.get("mark").text()).toBe("İ");
  });

  it.each([
    ["視頻摘要與視頻教學", "视频", ["視頻", "視頻"]],
    ["视频摘要", "視頻", ["视频"]],
    ["視频摘要", "视频", ["視频"]],
    ["頭髮與發展", "发", ["髮", "發"]],
  ])("uses the same matches for filtering and highlighting %s", async (title, query, matches) => {
    useFetchMock().data.value.items[0].title = title;
    const wrapper = await mountIndexPage();
    const input = wrapper.get('[data-testid="title-search-input"]');
    await input.setValue(query);
    // The stub renders both the client list and fallback, so verify both.
    const titles = wrapper.findAll(".showcase-card__title");
    expect(titles).toHaveLength(2);
    for (const rendered of titles) {
      expect(rendered.text()).toBe(title);
      expect(rendered.findAll("mark").map((mark) => mark.text())).toEqual(matches);
    }
    await input.setValue("");
    expect(wrapper.findAll(".showcase-card__title")).toHaveLength(4);
    expect(wrapper.find("mark").exists()).toBe(false);
  });

  it("refreshes prepared title matches when list data changes", async () => {
    const wrapper = await mountIndexPage();
    await wrapper.get('[data-testid="title-search-input"]').setValue("视频");
    expect(wrapper.text()).toContain("找不到符合的標題");
    useFetchMock().data.value.items[0].title = "視頻新標題";
    await wrapper.vm.$nextTick();
    expect(wrapper.get(".showcase-card__title").get("mark").text()).toBe("視頻");
  });

  it("shows an empty state when no title matches", async () => {
    const wrapper = await mountIndexPage();

    await wrapper.get('[data-testid="title-search-input"]').setValue("missing title");

    expect(wrapper.text()).toContain("找不到符合的標題");
  });
});
