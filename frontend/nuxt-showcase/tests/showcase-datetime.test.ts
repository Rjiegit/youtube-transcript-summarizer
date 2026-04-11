import { describe, expect, it } from "vitest";

import { formatTaipeiDate, formatTaipeiDateTime } from "../utils/datetime";
import { getLatestResultCreatedAt } from "../utils/showcase";

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

  it("uses the latest result created time for the home page stat", () => {
    expect(getLatestResultCreatedAt([
      {
        id: "latest",
        title: "Latest",
        summary: "Latest summary",
        source_url: null,
        created_at: "2026-04-11T10:53:00.000Z",
        processing_duration: null,
      },
      {
        id: "older",
        title: "Older",
        summary: "Older summary",
        source_url: null,
        created_at: "2026-04-10T10:53:00.000Z",
        processing_duration: null,
      },
    ])).toBe("2026-04-11T10:53:00.000Z");
    expect(getLatestResultCreatedAt([])).toBe("");
  });
});
