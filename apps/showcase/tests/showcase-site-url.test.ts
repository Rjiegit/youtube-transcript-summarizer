import { describe, expect, it } from "vitest";
import { DEFAULT_SITE_URL, resolveSiteUrl } from "../utils/site-url";

describe("share metadata site URL", () => {
  it("uses the configured HTTPS origin without query or path", () => {
    expect(resolveSiteUrl(" https://preview.example.com/path?test=1#fragment ")).toBe("https://preview.example.com");
  });

  it.each([undefined, "", "not a URL", "javascript:alert(1)", "http://example.com", "https://user:pass@example.com"])(
    "falls back to the public site for invalid configuration %s", (value) => {
      expect(resolveSiteUrl(value)).toBe(DEFAULT_SITE_URL);
    },
  );
});
