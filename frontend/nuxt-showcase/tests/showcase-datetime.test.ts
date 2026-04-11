import { describe, expect, it } from "vitest";

import { formatTaipeiDate, formatTaipeiDateTime } from "../utils/datetime";

describe("showcase datetime formatting", () => {
  it("formats updated timestamps in Asia/Taipei", () => {
    expect(formatTaipeiDateTime("2026-04-11T10:53:00.000Z")).toBe("2026年4月11日 下午06:53");
  });

  it("formats card dates in Asia/Taipei", () => {
    expect(formatTaipeiDate("2026-04-11T10:53:00.000Z")).toBe("2026年4月11日");
  });

  it("returns an empty string for missing values", () => {
    expect(formatTaipeiDateTime("")).toBe("");
    expect(formatTaipeiDate(null)).toBe("");
  });
});
