import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ShowcaseCard from "../components/ShowcaseCard.vue";
import type { ShowcaseResult } from "../types/showcase";

describe("ShowcaseCard", () => {
  it("renders title and links without showing summary fallback text", () => {
    const item: ShowcaseResult = {
      id: "abc",
      title: "A showcase entry",
      summary: "",
      source_url: "https://youtube.com/watch?v=abc",
      notion_url: "https://www.notion.so/workspace/abc",
      created_at: "2026-03-29T00:00:00.000Z",
      processing_duration: 4.2,
    };

    const wrapper = mount(ShowcaseCard, {
      props: { item },
    });

    expect(wrapper.text()).toContain("A showcase entry");
    expect(wrapper.text()).not.toContain("這筆結果尚未提供摘要內容。");
    expect(wrapper.find('a[href="https://youtube.com/watch?v=abc"]').exists()).toBe(true);
    expect(wrapper.find('a[href="https://www.notion.so/workspace/abc"]').exists()).toBe(true);
  });
});
