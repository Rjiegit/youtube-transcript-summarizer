import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, ref } from "vue";

import type { ShowcaseApiResponse } from "../types/showcase";

const useFetchMock = vi.fn();

vi.stubGlobal("useFetch", useFetchMock);
vi.stubGlobal("useHead", vi.fn());

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
}

describe("showcase index page", () => {
  beforeEach(() => {
    vi.resetModules();
    useFetchMock.mockReset();
    stubNuxtState();
    stubLocalStorage();
  });

  function loadPageModule() {
    return import("../pages/index.vue?t=" + Date.now() + Math.random());
  }

  it("updates the unread count when a card is marked as read", async () => {
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
              <button
                type="button"
                :data-testid="'card-' + item.id"
                @click="$emit('mark-read')"
              >
                {{ item.title }} {{ isRead ? 'read' : 'unread' }}
              </button>
            `,
          }),
        },
      },
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="unread-count"]').text()).toContain("2 篇");
    expect(wrapper.find('[data-testid="card-result-1-duplicate"]').exists()).toBe(false);

    await wrapper.get('[data-testid="card-result-1"]').trigger("click");

    expect(wrapper.get('[data-testid="unread-count"]').text()).toContain("1 篇");
  });
});
