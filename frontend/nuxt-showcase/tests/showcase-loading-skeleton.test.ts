import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AppLoadingSkeleton from "../components/AppLoadingSkeleton.vue";

describe("AppLoadingSkeleton", () => {
  it("renders a responsive list-page content skeleton", () => {
    const wrapper = mount(AppLoadingSkeleton, {
      props: { variant: "list" },
    });

    expect(wrapper.classes()).toContain("app-loading-skeleton--list");
    expect(wrapper.find(".app-loading-skeleton__list-hero").exists()).toBe(true);
    expect(wrapper.find(".app-loading-skeleton__list-toolbar").exists()).toBe(true);
    expect(wrapper.findAll(".app-loading-skeleton__card")).toHaveLength(3);
    expect(wrapper.find(".app-loading-skeleton__detail").exists()).toBe(false);
    expect(wrapper.text()).toBe("");
    expect(wrapper.attributes("role")).toBe("status");
    expect(wrapper.attributes("aria-live")).toBe("polite");
    expect(wrapper.attributes("aria-label")).toBe("頁面載入中");
  });

  it("renders an article-page content skeleton", () => {
    const wrapper = mount(AppLoadingSkeleton, {
      props: { variant: "detail" },
    });

    expect(wrapper.classes()).toContain("app-loading-skeleton--detail");
    expect(wrapper.find(".app-loading-skeleton__detail").exists()).toBe(true);
    expect(wrapper.find(".app-loading-skeleton__detail-nav").exists()).toBe(true);
    expect(wrapper.find(".app-loading-skeleton__detail-title").exists()).toBe(true);
    expect(wrapper.findAll(".app-loading-skeleton__detail-line").length).toBeGreaterThan(3);
    expect(wrapper.find(".app-loading-skeleton__card").exists()).toBe(false);
    expect(wrapper.text()).toBe("");
    expect(wrapper.attributes("aria-label")).toBe("頁面載入中");
  });
});
