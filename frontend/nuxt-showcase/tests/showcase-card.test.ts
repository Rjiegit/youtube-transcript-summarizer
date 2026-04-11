import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ShowcaseCard from "../components/ShowcaseCard.vue";
import type { ShowcaseResult } from "../types/showcase";

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
          NuxtLink: {
            template: "<a :href=\"to\"><slot /></a>",
            props: ["to"],
          },
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
          NuxtLink: {
            template: "<a :href=\"to\"><slot /></a>",
            props: ["to"],
          },
        },
      },
    });

    expect(wrapper.classes()).toContain("showcase-card--read");
    expect(wrapper.text()).toContain("Read");
  });
});
