import { describe, expect, it } from "vitest";

import { findTitleMatches, normalizeTitleSearch, prepareTitleSearch, splitTitleSearch } from "../utils/title-search";

describe("title search script equivalence", () => {
  it.each([
    ["㗲視頻㗲", "𠵾视频", ["㗲視頻"]],
    ["㗲視頻㗲", "视频", ["視頻"]],
    ["視頻摘要", "视频", ["視頻"]],
    ["视频摘要", "視頻", ["视频"]],
    ["視频摘要", "视频", ["視频"]],
    ["頭髮與發展", "发", ["髮", "發"]],
    ["後來的皇后", "后", ["後", "后"]],
    ["乾燥與幹活", "干", ["乾", "幹"]],
    ["视频摘要與視頻教學", " 視頻 ", ["视频", "視頻"]],
    ["😀İ視頻 Mini", "视频 mini", ["視頻 Mini"]],
    ["İstanbul 視頻", "i", ["İ"]],
    ["ΟΣ 視頻", "ος", ["ΟΣ"]],
    ["影片摘要", "视频", []],
    ["人工智慧", "人工智能", []],
    ["🚀𠀀未知字", "𠀀", ["𠀀"]],
    ["<img src=x>視頻", "<img", ["<img"]],
    ["視頻.*摘要", ".*", [".*"]],
    ["任意標題", "   ", []],
    ["", "视频", []],
  ])("matches %s with %s without changing the title", (title, query, expected) => {
    const prepared = prepareTitleSearch(title);
    const ranges = findTitleMatches(prepared, normalizeTitleSearch(query));
    expect(ranges.map(({ start, end }) => title.slice(start, end))).toEqual(expected);
    const parts = splitTitleSearch(title, ranges);
    expect(parts.map((part) => part.text).join("")).toBe(title);
    expect(parts.filter((part) => part.matched).map((part) => part.text)).toEqual(expected);
  });

  it("preserves title whitespace and contextual lowercase", () => {
    expect(prepareTitleSearch(" ΟΣ 視頻 ").normalized).toBe(" ος 视频 ");
    expect(normalizeTitleSearch(" ΟΣ 視頻 ")).toBe("ος 视频");
  });

  it("merges matches that point to the same expanded source character", () => {
    const title = "İİİ";
    const ranges = findTitleMatches(prepareTitleSearch(title), normalizeTitleSearch("\u0307i"));
    expect(ranges).toEqual([{ start: 0, end: 3 }]);
    expect(splitTitleSearch(title, ranges)).toEqual([{ text: title, matched: true }]);
  });
});
