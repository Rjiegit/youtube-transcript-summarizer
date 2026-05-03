import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import type { ShowcaseDetailResult } from "../types/showcase";

const useFetchMock = vi.fn();
const useRouteMock = vi.fn();
const markAsReadMock = vi.fn();

vi.mock("../composables/useReadResults", () => ({
  useReadResults: () => ({
    isRead: vi.fn(() => false),
    readIds: { value: [] },
    readMap: { value: {} },
    markAsRead: markAsReadMock,
    markAsUnread: vi.fn(),
  }),
}));

vi.stubGlobal("useFetch", useFetchMock);
vi.stubGlobal("useRoute", useRouteMock);
vi.stubGlobal("useHead", vi.fn());
vi.stubGlobal("createError", (input: { statusCode: number; statusMessage: string }) => {
  const error = new Error(input.statusMessage);
  return Object.assign(error, input);
});
vi.stubGlobal("showError", vi.fn((error: unknown) => error));

const detailResponse: ShowcaseDetailResult = {
  id: "result-2-page-id",
  title: "Second result",
  summary: "A concise summary of the second result.",
  content: "Detailed paragraph one.\n\nDetailed paragraph two.",
  source_url: "https://www.youtube.com/watch?v=second",
  created_at: "2026-03-28T12:00:00.000Z",
  processing_duration: 12.4,
};

const nonYoutubeDetailResponse: ShowcaseDetailResult = {
  ...detailResponse,
  source_url: "https://example.com/video/second",
};

describe("Showcase detail page", () => {
  beforeEach(() => {
    useFetchMock.mockReset();
    useRouteMock.mockReset();
    markAsReadMock.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  function loadPageModule() {
    return import("../pages/results/[id].vue?t=" + Date.now() + Math.random());
  }

  it("renders the selected showcase item with a YouTube embed and without exposing a Notion link", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "result-2-page-id" },
    });
    useFetchMock.mockReturnValue({
      data: { value: detailResponse },
      pending: { value: false },
      error: { value: null },
    });

    const pageModule = await loadPageModule();
    const wrapper = mount(pageModule.default, {
      global: {
        stubs: {
          NuxtLink: {
            template: "<a :href=\"to\"><slot /></a>",
            props: ["to"],
          },
        },
      },
    });

    expect(wrapper.text()).toContain("Second result");
    expect(wrapper.text()).toContain("Detailed paragraph one.");
    expect(wrapper.text()).toContain("Detailed paragraph two.");
    expect(wrapper.find('a[href="/"]').exists()).toBe(true);
    expect(wrapper.find('a[href="https://www.youtube.com/watch?v=second"]').exists()).toBe(true);
    const embed = wrapper.find('iframe[src="https://www.youtube-nocookie.com/embed/second"]');
    expect(embed.exists()).toBe(true);
    expect(wrapper.find('[data-testid="detail-video"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="detail-summary"]').exists()).toBe(true);
    const summaryNode = wrapper.get('[data-testid="detail-summary"]').element;
    const videoNode = wrapper.get('[data-testid="detail-video"]').element;
    expect(summaryNode.compareDocumentPosition(videoNode) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(wrapper.text()).not.toContain("Notion");
    expect(markAsReadMock).toHaveBeenCalledWith("result-2-page-id");
  });

  it("keeps the original video link without embedding non-YouTube sources", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "result-2-page-id" },
    });
    useFetchMock.mockReturnValue({
      data: { value: nonYoutubeDetailResponse },
      pending: { value: false },
      error: { value: null },
    });

    const pageModule = await loadPageModule();
    const wrapper = mount(pageModule.default, {
      global: {
        stubs: {
          NuxtLink: {
            template: "<a :href=\"to\"><slot /></a>",
            props: ["to"],
          },
        },
      },
    });

    expect(wrapper.find('a[href="https://example.com/video/second"]').exists()).toBe(true);
    expect(wrapper.find("iframe").exists()).toBe(false);
    expect(wrapper.find('[data-testid="detail-video"]').exists()).toBe(false);
  });

  it("shows loading state before the fetch resolves", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "result-2-page-id" },
    });
    useFetchMock.mockReturnValue({
      data: ref(null),
      pending: ref(true),
      error: ref(null),
    });

    const pageModule = await loadPageModule();
    const wrapper = mount(pageModule.default, {
      global: {
        stubs: {
          NuxtLink: true,
        },
      },
    });

    expect(wrapper.text()).toContain("載入展示資料中");
    expect(wrapper.text()).not.toContain("Second result");
    expect(markAsReadMock).not.toHaveBeenCalled();
  });

  it("renders an error state when fetch fails", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "result-2-page-id" },
    });
    useFetchMock.mockReturnValue({
      data: ref(null),
      pending: ref(false),
      error: ref({
        statusMessage: "Fetch failed",
        message: "Fetch failed",
      }),
    });

    const pageModule = await loadPageModule();
    const wrapper = mount(pageModule.default, {
      global: {
        stubs: {
          NuxtLink: true,
        },
      },
    });

    expect(wrapper.text()).toContain("目前無法載入展示內容");
    expect(wrapper.text()).toContain("Fetch failed");
    expect(markAsReadMock).not.toHaveBeenCalled();
  });

  it("throws a 404 error only after fetch resolves and the item is still missing", async () => {
    useRouteMock.mockReturnValue({
      params: { id: "missing-id" },
    });
    const data = ref(null);
    const pending = ref(false);
    const error = ref(null);
    useFetchMock.mockReturnValue({
      data,
      pending,
      error,
    });

    const pageModule = await loadPageModule();

    try {
      mount(pageModule.default, {
        global: {
          stubs: {
            NuxtLink: true,
          },
        },
      });
      throw new Error("Expected mount to throw a 404 error.");
    } catch (error) {
      expect(error).toMatchObject({
        statusCode: 404,
        statusMessage: "Showcase result not found.",
      });
    }
  });
});
