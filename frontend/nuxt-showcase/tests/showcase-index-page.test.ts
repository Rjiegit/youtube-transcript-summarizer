import { flushPromises, mount } from "@vue/test-utils";
import { renderToString } from "vue/server-renderer";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createSSRApp, defineComponent, h, reactive, ref, Suspense } from "vue";

import type { ShowcaseApiResponse } from "../types/showcase";

const useFetchMock = vi.fn();
const route = reactive({
  fullPath: "/",
});

vi.stubGlobal("useFetch", useFetchMock);
vi.stubGlobal("useHead", vi.fn());
vi.stubGlobal("useRoute", () => route);

const response: ShowcaseApiResponse = {
  items: [
    {
      id: "result-1",
      title: "First result",
      summary: "First summary.",
      source_url: "https://www.youtube.com/watch?v=first",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    },
    {
      id: "result-1-duplicate",
      title: "First result duplicate",
      summary: "First summary again.",
      source_url: "https://www.youtube.com/watch?v=first#duplicate",
      created_at: "2026-03-28T12:00:00.000Z",
      processing_duration: 4.8,
    },
    {
      id: "result-2",
      title: "Second result",
      summary: "Second summary.",
      source_url: "https://www.youtube.com/watch?v=second",
      created_at: "2026-03-28T00:00:00.000Z",
      processing_duration: 5.1,
    },
  ],
  generated_at: "2026-04-11T00:00:00.000Z",
  cache_ttl_seconds: 3600,
};

function stubNuxtState() {
  const stateStore = new Map<string, ReturnType<typeof ref>>();

  vi.stubGlobal("useState", vi.fn((key: string, init?: () => unknown) => {
    if (!stateStore.has(key)) {
      stateStore.set(key, ref(init ? init() : undefined));
    }
    return stateStore.get(key)!;
  }));
}

  function stubLocalStorage() {
    const store = new Map<string, string>();
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
  Object.defineProperty(window, "localStorage", {
    value: localStorageMock,
    configurable: true,
  });

  return {
    setRaw(key: string, value: string) {
      store.set(key, value);
    },
  };
}

describe("showcase index page", () => {
  beforeEach(() => {
    vi.resetModules();
    useFetchMock.mockReset();
    route.fullPath = "/";
    stubNuxtState();
  });

  function loadPageModule() {
    return import("../pages/index.vue?t=" + Date.now() + Math.random());
  }

  it("keeps read state updates and duplicate filtering without article counts", async () => {
    stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const TestHost = defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      template: "<Suspense><IndexPage /></Suspense>",
    });
    const wrapper = mount(TestHost, {
      global: {
        stubs: {
          ClientOnly: defineComponent({
            template: "<slot />",
          }),
          ShowcaseCard: defineComponent({
            props: {
              item: {
                type: Object,
                required: true,
              },
              isRead: {
                type: Boolean,
                default: false,
              },
            },
            emits: ["mark-read"],
            template: `
              <article :data-testid="'card-' + item.id">
                <span>{{ item.title }} {{ isRead ? 'read' : 'unread' }}</span>
                <button
                  v-if="!isRead"
                  type="button"
                  :data-testid="'quick-read-' + item.id"
                  @click="$emit('mark-read')"
                >
                  quick read
                </button>
              </article>
            `,
          }),
        },
      },
    });
    await flushPromises();

    expect(wrapper.find('[data-testid="unread-count"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="total-count"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="card-result-1-duplicate"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("unread");

    await wrapper.get('[data-testid="quick-read-result-1"]').trigger("click");

    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("read");
    expect(wrapper.find('[data-testid="quick-read-result-1"]').exists()).toBe(false);
    expect(JSON.parse(window.localStorage.getItem("nuxt-showcase-read-results") || "{}")).toMatchObject({
      "url:https://www.youtube.com/watch?v=first": expect.any(Object),
      "result-1": expect.any(Object),
      "result-1-duplicate": expect.any(Object),
    });
  });

  it("marks the current list as read from the toolbar button", async () => {
    stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const TestHost = defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      template: "<Suspense><IndexPage /></Suspense>",
    });
    const wrapper = mount(TestHost, {
      global: {
        stubs: {
          ClientOnly: defineComponent({
            template: "<slot />",
          }),
          ShowcaseCard: defineComponent({
            props: {
              item: {
                type: Object,
                required: true,
              },
              isRead: {
                type: Boolean,
                default: false,
              },
            },
            emits: ["mark-read"],
            template: `
              <article :data-testid="'card-' + item.id">
                <span>{{ item.title }} {{ isRead ? 'read' : 'unread' }}</span>
              </article>
            `,
          }),
        },
      },
    });
    await flushPromises();

    const button = wrapper.get('[data-testid="mark-all-read-button"]');
    expect(button.attributes("disabled")).toBeUndefined();
    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("unread");
    expect(wrapper.get('[data-testid="card-result-2"]').text()).toContain("unread");

    await button.trigger("click");

    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("read");
    expect(wrapper.get('[data-testid="card-result-2"]').text()).toContain("read");
    expect(wrapper.get('[data-testid="mark-all-read-button"]').attributes("disabled")).toBeDefined();
  });

  it("marks only filtered results as read from the toolbar button", async () => {
    stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const TestHost = defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      template: "<Suspense><IndexPage /></Suspense>",
    });
    const wrapper = mount(TestHost, {
      global: {
        stubs: {
          ClientOnly: defineComponent({
            template: "<slot />",
          }),
          ShowcaseCard: defineComponent({
            props: {
              item: {
                type: Object,
                required: true,
              },
              isRead: {
                type: Boolean,
                default: false,
              },
            },
            emits: ["mark-read"],
            template: `
              <article :data-testid="'card-' + item.id">
                <span>{{ item.title }} {{ isRead ? 'read' : 'unread' }}</span>
              </article>
            `,
          }),
        },
      },
    });
    await flushPromises();

    await wrapper.get('[data-testid="title-search-input"]').setValue("Second");
    await wrapper.get('[data-testid="mark-all-read-button"]').trigger("click");
    await wrapper.get('[data-testid="title-search-input"]').setValue("");

    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("unread");
    expect(wrapper.get('[data-testid="card-result-2"]').text()).toContain("read");
    expect(wrapper.get('[data-testid="mark-all-read-button"]').attributes("disabled")).toBeUndefined();
  });

  it("does not server-render the mark all read button with stale disabled state", async () => {
    stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const TestHost = createSSRApp({
      render() {
        return h(Suspense, null, {
          default: () => h(pageModule.default),
        });
      },
    });
    TestHost.component("ClientOnly", defineComponent({
      setup(_, { slots }) {
        return () => slots.fallback?.() ?? null;
      },
    }));

    const html = await renderToString(TestHost);

    expect(html).not.toContain('data-testid="mark-all-read-button"');
  });

  it("refreshes read state from localStorage when returning to the page", async () => {
    const storage = stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const TestHost = defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      template: "<Suspense><IndexPage /></Suspense>",
    });
    const wrapper = mount(TestHost, {
      global: {
        stubs: {
          ClientOnly: defineComponent({
            template: "<slot />",
          }),
          ShowcaseCard: defineComponent({
            props: {
              item: {
                type: Object,
                required: true,
              },
              isRead: {
                type: Boolean,
                default: false,
              },
            },
            emits: ["mark-read"],
            template: `
              <article :data-testid="'card-' + item.id">
                <span>{{ item.title }} {{ isRead ? 'read' : 'unread' }}</span>
              </article>
            `,
          }),
        },
      },
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("unread");

    storage.setRaw("nuxt-showcase-read-results", JSON.stringify({
      "url:https://www.youtube.com/watch?v=first": { readAt: "2026-04-12T00:00:00.000Z" },
    }));
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("read");
  });

  it("forces the list to rerender after a persisted browser history restore", async () => {
    stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });
    let mountedCards = 0;

    const pageModule = await loadPageModule();
    const TestHost = defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      template: "<Suspense><IndexPage /></Suspense>",
    });
    const wrapper = mount(TestHost, {
      global: {
        stubs: {
          ClientOnly: defineComponent({
            template: "<slot />",
          }),
          ShowcaseCard: defineComponent({
            props: {
              item: {
                type: Object,
                required: true,
              },
              isRead: {
                type: Boolean,
                default: false,
              },
            },
            setup() {
              mountedCards += 1;
            },
            template: `
              <article>
                <span>{{ item.title }} {{ isRead ? 'read' : 'unread' }}</span>
              </article>
            `,
          }),
        },
      },
    });
    await flushPromises();
    const initialMountedCards = mountedCards;

    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
    await wrapper.vm.$nextTick();

    expect(mountedCards).toBeGreaterThan(initialMountedCards);
  });

  it("refreshes read state when the page becomes visible again", async () => {
    const storage = stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const TestHost = defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      template: "<Suspense><IndexPage /></Suspense>",
    });
    const wrapper = mount(TestHost, {
      global: {
        stubs: {
          ClientOnly: defineComponent({
            template: "<slot />",
          }),
          ShowcaseCard: defineComponent({
            props: {
              item: {
                type: Object,
                required: true,
              },
              isRead: {
                type: Boolean,
                default: false,
              },
            },
            emits: ["mark-read"],
            template: `
              <article :data-testid="'card-' + item.id">
                <span>{{ item.title }} {{ isRead ? 'read' : 'unread' }}</span>
              </article>
            `,
          }),
        },
      },
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="card-result-2"]').text()).toContain("unread");

    storage.setRaw("nuxt-showcase-read-results", JSON.stringify({
      "url:https://www.youtube.com/watch?v=second": { readAt: "2026-04-12T00:00:00.000Z" },
    }));
    Object.defineProperty(document, "visibilityState", {
      value: "visible",
      configurable: true,
    });
    document.dispatchEvent(new Event("visibilitychange"));
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="card-result-2"]').text()).toContain("read");
  });

  it("refreshes read state when SPA history navigation returns to the list page", async () => {
    const storage = stubLocalStorage();
    useFetchMock.mockResolvedValue({
      data: ref(response),
      pending: ref(false),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const TestHost = defineComponent({
      components: {
        IndexPage: pageModule.default,
      },
      template: "<Suspense><IndexPage /></Suspense>",
    });
    const wrapper = mount(TestHost, {
      global: {
        stubs: {
          ClientOnly: defineComponent({
            template: "<slot />",
          }),
          ShowcaseCard: defineComponent({
            props: {
              item: {
                type: Object,
                required: true,
              },
              isRead: {
                type: Boolean,
                default: false,
              },
            },
            template: `
              <article :data-testid="'card-' + item.id">
                <span>{{ item.title }} {{ isRead ? 'read' : 'unread' }}</span>
              </article>
            `,
          }),
        },
      },
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("unread");

    route.fullPath = "/results/result-1";
    await wrapper.vm.$nextTick();
    storage.setRaw("nuxt-showcase-read-results", JSON.stringify({
      "url:https://www.youtube.com/watch?v=first": { readAt: "2026-04-12T00:00:00.000Z" },
    }));
    route.fullPath = "/";
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="card-result-1"]').text()).toContain("read");
  });
});
