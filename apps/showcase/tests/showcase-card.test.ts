import { mount } from "@vue/test-utils";
import { defineComponent } from "vue";
import { describe, expect, it } from "vitest";

import ShowcaseCard from "../components/ShowcaseCard.vue";
import type { ShowcaseResult } from "../types/showcase";

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
    function navigate(event?: MouseEvent) {
      event?.preventDefault();
      return Promise.resolve();
    }

    return {
      navigate,
      href: props.to,
    };
  },
  template: `
    <template v-if="custom">
      <slot :href="href" :navigate="navigate"></slot>
    </template>
    <a v-else :href="to"><slot /></a>
  `,
});

describe("ShowcaseCard", () => {
  it("renders a detail link, summary preview, and original video link", () => {
    const item: ShowcaseResult = {
      id: "abc",
      title: "A showcase entry with detail page",
      summary: "A concise summary preview for the showcase card.",
      source_url: "https://youtube.com/watch?v=abc",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    };

    const wrapper = mount(ShowcaseCard, {
      props: { item },
      global: {
        stubs: {
          NuxtLink: nuxtLinkStub,
        },
      },
    });

    expect(wrapper.text()).toContain("A showcase entry with detail page");
    expect(wrapper.text()).toContain("A concise summary preview for the showcase card.");
    expect(wrapper.find('a[href="/results/abc"]').exists()).toBe(true);
    expect(wrapper.find('a[href="https://youtube.com/watch?v=abc"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain("Open in Notion");
  });

  it("shows a read badge and read class when the item is marked as read", () => {
    const item: ShowcaseResult = {
      id: "abc",
      title: "A showcase entry with detail page",
      summary: "A concise summary preview for the showcase card.",
      source_url: "https://youtube.com/watch?v=abc",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    };

    const wrapper = mount(ShowcaseCard, {
      props: {
        item,
        isRead: true,
      },
      global: {
        stubs: {
          NuxtLink: nuxtLinkStub,
        },
      },
    });

    expect(wrapper.classes()).toContain("showcase-card--read");
    expect(wrapper.text()).toContain("已讀");
    expect(wrapper.find(".showcase-card__read-badge").exists()).toBe(true);
  });

  it("keeps the badge slot rendered even when the item is unread", () => {
    const item: ShowcaseResult = {
      id: "abc",
      title: "A showcase entry with detail page",
      summary: "A concise summary preview for the showcase card.",
      source_url: "https://youtube.com/watch?v=abc",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    };

    const wrapper = mount(ShowcaseCard, {
      props: {
        item,
        isRead: false,
      },
      global: {
        stubs: {
          NuxtLink: nuxtLinkStub,
        },
      },
    });

    const badge = wrapper.find(".showcase-card__read-badge");
    expect(badge.exists()).toBe(true);
    expect(badge.attributes("aria-hidden")).toBe("true");
    expect(badge.text()).toBe("已讀");
    expect(wrapper.get('[data-testid="quick-mark-read"]').text()).toBe("標記已讀");
  });

  it("emits mark-read when the quick read button is clicked", async () => {
    const item: ShowcaseResult = {
      id: "abc",
      title: "A showcase entry with detail page",
      summary: "A concise summary preview for the showcase card.",
      source_url: "https://youtube.com/watch?v=abc",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    };

    const wrapper = mount(ShowcaseCard, {
      props: { item },
      global: {
        stubs: {
          NuxtLink: nuxtLinkStub,
        },
      },
    });

    await wrapper.get('[data-testid="quick-mark-read"]').trigger("click");

    expect(wrapper.emitted("mark-read")?.length ?? 0).toBe(1);
  });

  it("hides the quick read button when the item is marked as read", () => {
    const item: ShowcaseResult = {
      id: "abc",
      title: "A showcase entry with detail page",
      summary: "A concise summary preview for the showcase card.",
      source_url: "https://youtube.com/watch?v=abc",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    };

    const wrapper = mount(ShowcaseCard, {
      props: {
        item,
        isRead: true,
      },
      global: {
        stubs: {
          NuxtLink: nuxtLinkStub,
        },
      },
    });

    expect(wrapper.find('[data-testid="quick-mark-read"]').exists()).toBe(false);
    expect(wrapper.find(".showcase-card__read-badge").exists()).toBe(true);
  });

  it("emits mark-read when the main card link is clicked", async () => {
    const item: ShowcaseResult = {
      id: "abc",
      title: "A showcase entry with detail page",
      summary: "A concise summary preview for the showcase card.",
      source_url: "https://youtube.com/watch?v=abc",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    };

    const wrapper = mount(ShowcaseCard, {
      props: { item },
      global: {
        stubs: {
          NuxtLink: nuxtLinkStub,
        },
      },
    });

    await wrapper.find('a[href="/results/abc"]').trigger("click");

    expect(wrapper.emitted("mark-read")?.length ?? 0).toBeGreaterThan(0);
  });

  it("keeps the read badge inside the title row for long titles", () => {
    const item: ShowcaseResult = {
      id: "long-title",
      title: "限制AI自由 | AI編程的正確姿勢 | Superpowers | gstack | OpenSpec | ExtremelyLongEnglishSegmentWithoutNaturalBreakpoints",
      summary: "Summary preview.",
      source_url: null,
      created_at: "2026-03-31T00:00:00.000Z",
      processing_duration: 8.4,
    };

    const wrapper = mount(ShowcaseCard, {
      props: {
        item,
        isRead: true,
      },
      global: {
        stubs: {
          NuxtLink: nuxtLinkStub,
        },
      },
    });

    const titleRow = wrapper.find(".showcase-card__title-row");
    const title = wrapper.find(".showcase-card__title");
    const badge = wrapper.find(".showcase-card__read-badge");

    expect(titleRow.exists()).toBe(true);
    expect(title.exists()).toBe(true);
    expect(badge.exists()).toBe(true);
    expect(titleRow.element.contains(title.element)).toBe(true);
    expect(titleRow.element.contains(badge.element)).toBe(true);
  });
});
