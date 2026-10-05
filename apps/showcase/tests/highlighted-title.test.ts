import { renderToString } from "@vue/server-renderer";
import { createSSRApp, h, nextTick } from "vue";
import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { findTitleMatches, normalizeTitleSearch, prepareTitleSearch } from "../utils/title-search";
import HighlightedTitle from "../components/HighlightedTitle.vue";

describe("HighlightedTitle", () => {
  it.each([
    ["MiniMax mini MINI", " mini ", ["Mini", "mini", "MINI"]],
    ["İstanbul", "i", ["İ"]],
    ["İMini", "mini", ["Mini"]],
    ["ΟΣ", "ος", ["ΟΣ"]],
    ["😀 Mini", "mini", ["Mini"]],
    ["視頻摘要與视频教學", "视频", ["視頻", "视频"]],
    ["中文標題中文", "中文", ["中文", "中文"]],
    ["A [test].* B", "[test].*", ["[test].*"]],
    ["MiniMax", "missing", []],
    ["MiniMax", "   ", []],
  ])("highlights literal matches in %s", (title, query, expected) => {
    const wrapper = mount(HighlightedTitle, { props: { title, ranges: findTitleMatches(prepareTitleSearch(title), normalizeTitleSearch(query)) } });
    expect(wrapper.findAll("mark").map((mark) => mark.text())).toEqual(expected);
    expect(wrapper.text()).toBe(title);
  });

  it("hydrates server-rendered original text and highlights without mismatch", async () => {
    const title = "😀İ視頻與视频摘要";
    const props = { title, ranges: findTitleMatches(prepareTitleSearch(title), normalizeTitleSearch("视频")) };
    const container = document.createElement("div");
    container.innerHTML = await renderToString(createSSRApp({ render: () => h(HighlightedTitle, props) }));
    document.body.appendChild(container);
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const app = createSSRApp({ render: () => h(HighlightedTitle, props) });
    try {
      app.mount(container);
      await nextTick();
      expect(container.textContent).toBe(title);
      expect(Array.from(container.querySelectorAll("mark"), (mark) => mark.textContent)).toEqual(["視頻", "视频"]);
      expect(warn).not.toHaveBeenCalled();
      expect(error).not.toHaveBeenCalled();
    } finally {
      app.unmount();
      container.remove();
      warn.mockRestore();
      error.mockRestore();
    }
  });

  it("renders HTML characters as text", () => {
    const title = '<img src=x onerror="alert(1)">';
    const wrapper = mount(HighlightedTitle, { props: { title, ranges: findTitleMatches(prepareTitleSearch(title), normalizeTitleSearch("<img")) } });
    expect(wrapper.find("img").exists()).toBe(false);
    expect(wrapper.get("mark").text()).toBe("<img");
    expect(wrapper.text()).toBe(title);
  });
});
