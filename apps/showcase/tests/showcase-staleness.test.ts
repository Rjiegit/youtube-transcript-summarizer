import { describe, expect, it } from "vitest";

import type { ShowcaseApiResponse } from "../types/showcase";
import { isShowcaseResponseStale } from "../utils/showcase";

const response: ShowcaseApiResponse = {
  items: [],
  generated_at: "2026-07-10T07:00:00.000Z",
  cache_ttl_seconds: 60,
};

describe("showcase response freshness", () => {
  it("keeps a response fresh until its cache TTL expires", () => {
    expect(isShowcaseResponseStale(response, Date.parse("2026-07-10T07:00:59.999Z"))).toBe(false);
    expect(isShowcaseResponseStale(response, Date.parse("2026-07-10T07:01:00.000Z"))).toBe(true);
  });

  it("treats missing or invalid generated times as stale", () => {
    expect(isShowcaseResponseStale({ ...response, generated_at: "" }, Date.now())).toBe(true);
    expect(isShowcaseResponseStale({ ...response, generated_at: "not-a-date" }, Date.now())).toBe(true);
  });

  it("treats invalid cache TTL values as stale", () => {
    expect(isShowcaseResponseStale({ ...response, cache_ttl_seconds: 0 }, Date.now())).toBe(true);
  });
});
