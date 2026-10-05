import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import HighlightedTitle from "../components/HighlightedTitle.vue";

describe("HighlightedTitle", () => {
  it.each([
    ["MiniMax mini MINI", " mini ", ["Mini", "mini", "MINI"]],
    ["İstanbul", "i", ["İ"]],
    ["İMini", "mini", ["Mini"]],
    ["ΟΣ", "ος", ["ΟΣ"]],
    ["😀 Mini", "mini", ["Mini"]],
    ["中文標題中文", "中文", ["中文", "中文"]],
    ["A [test].* B", "[test].*", ["[test].*"]],
    ["MiniMax", "missing", []],
    ["MiniMax", "   ", []],
  ])("highlights literal matches in %s", (title, query, expected) => {
    const wrapper = mount(HighlightedTitle, { props: { title, query } });
    expect(wrapper.findAll("mark").map((mark) => mark.text())).toEqual(expected);
    expect(wrapper.text()).toBe(title);
  });

  it("renders HTML characters as text", () => {
    const title = '<img src=x onerror="alert(1)">';
    const wrapper = mount(HighlightedTitle, { props: { title, query: "<img" } });
    expect(wrapper.find("img").exists()).toBe(false);
    expect(wrapper.get("mark").text()).toBe("<img");
    expect(wrapper.text()).toBe(title);
  });
});
