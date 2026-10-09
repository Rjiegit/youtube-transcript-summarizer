import { describe, expect, it, vi } from "vitest";

const { getRequestURL, getResponseStatus, setHeader } = vi.hoisted(() => ({
  getRequestURL: vi.fn(),
  getResponseStatus: vi.fn(),
  setHeader: vi.fn(),
}));
vi.mock("h3", () => ({ getRequestURL, getResponseStatus, setHeader }));
vi.stubGlobal("defineNitroPlugin", (plugin: unknown) => plugin);

describe("showcase final error cache policy", () => {
  it("uses the thrown HTTP status when Nitro has not set the response status yet", async () => {
    setHeader.mockClear();
    getRequestURL.mockReturnValue({ pathname: "/api/showcase/insights/missing" });
    getResponseStatus.mockReturnValue(200);
    const hook = vi.fn();
    const plugin = (await import("../server/plugins/showcase-error-cache")).default;
    plugin({ hooks: { hook } });
    const event = { node: { res: { headersSent: false } } };
    hook.mock.calls[0][1](Object.assign(new Error("missing"), { statusCode: 404 }), { event });
    expect(setHeader).toHaveBeenCalledWith(event, "Cache-Control", "no-store");
  });

  it.each([
    ["/api/showcase/results", 500, true],
    ["/api/showcase/results/page-id", 502, true],
    ["/api/showcase/results", 200, false],
    ["/results/page-id", 502, true],
    ["/results/page-id", 404, true],
    ["/results/page-id", 200, false],
    ["/results-other", 500, false],
    ["/api/read-state", 500, false],
    ["/api/showcase/results-other", 500, false],
    ["/api/showcase/insights", 500, true],
    ["/api/showcase/insights/2026-09-06", 404, true],
    ["/insights/2026-09-06", 404, true],
    ["/insights", 502, true],
    ["/insights", 200, false],
    ["/insights-other", 404, false],
  ])("applies no-store to %s with status %s: %s", async (pathname, status, expected) => {
    setHeader.mockClear();
    getRequestURL.mockReturnValue({ pathname });
    getResponseStatus.mockReturnValue(status);
    const hook = vi.fn();
    const plugin = (await import("../server/plugins/showcase-error-cache")).default;
    plugin({ hooks: { hook } });
    const event = { node: { res: { headersSent: false } } };
    hook.mock.calls[0][1](new Error("private upstream message"), { event });
    if (expected) {
      expect(setHeader).toHaveBeenCalledWith(event, "Cache-Control", "no-store");
    } else {
      expect(setHeader).not.toHaveBeenCalled();
    }
  });
});
