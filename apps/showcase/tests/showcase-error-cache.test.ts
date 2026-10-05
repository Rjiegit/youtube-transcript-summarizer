import { describe, expect, it, vi } from "vitest";

const { getRequestURL, getResponseStatus, setHeader } = vi.hoisted(() => ({
  getRequestURL: vi.fn(),
  getResponseStatus: vi.fn(),
  setHeader: vi.fn(),
}));
vi.mock("h3", () => ({ getRequestURL, getResponseStatus, setHeader }));
vi.stubGlobal("defineNitroPlugin", (plugin: unknown) => plugin);

describe("showcase final error cache policy", () => {
  it.each([
    ["/api/showcase/results", 500, true],
    ["/api/showcase/results/page-id", 502, true],
    ["/api/showcase/results", 200, false],
    ["/api/read-state", 500, false],
    ["/api/showcase/results-other", 500, false],
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
