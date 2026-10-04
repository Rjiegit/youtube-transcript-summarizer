// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchDatabaseSchema, fetchLatestCompletedResults, fetchPage, fetchPageBlocks } from "../server/utils/notion";

afterEach(() => vi.restoreAllMocks());

describe("Notion request timeout", () => {
  it.each(["schema", "page", "blocks", "query"])("aborts a stalled %s request using a five-second timeout", async (kind) => {
    const controller = new AbortController();
    const timeout = vi.spyOn(AbortSignal, "timeout").mockReturnValue(controller.signal);
    let notifyStarted!: () => void;
    const started = new Promise<void>((resolve) => { notifyStarted = resolve; });
    const fetchImpl = vi.fn<typeof fetch>(async (url, init) => {
      if (kind === "query" && !String(url).endsWith("/query")) {
        return new Response(JSON.stringify({ properties: {} }));
      }
      notifyStarted();
      expect(init?.signal).toBe(controller.signal);
      return new Promise<Response>((_resolve, reject) => {
        init!.signal!.addEventListener("abort", () => reject(init!.signal!.reason), { once: true });
      });
    });
    const request = kind === "schema" ? fetchDatabaseSchema("key", "database", fetchImpl)
      : kind === "page" ? fetchPage("key", "page", fetchImpl)
      : kind === "blocks" ? fetchPageBlocks("key", "page", fetchImpl)
      : fetchLatestCompletedResults({ apiKey: "key", databaseId: "database", fetchImpl });
    const observed = request.then(() => null, (error: unknown) => error);
    await started;
    expect(fetchImpl).toHaveBeenCalledTimes(kind === "query" ? 2 : 1);
    const error = new DOMException("The operation timed out", "TimeoutError");
    controller.abort(error);
    expect(await observed).toBe(error);
    expect(timeout).toHaveBeenCalled();
    for (const [duration] of timeout.mock.calls) expect(duration).toBe(5000);
  });

  it("creates an independent timeout for each blocks page and nested child", async () => {
    const timeout = vi.spyOn(AbortSignal, "timeout").mockImplementation(() => new AbortController().signal);
    const fetchImpl = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        results: [{ id: "child", type: "paragraph", has_children: true }], has_more: true, next_cursor: "next",
      })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ results: [], has_more: false })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ results: [], has_more: false })));
    await fetchPageBlocks("key", "page", fetchImpl);
    expect(timeout.mock.calls).toEqual([[5000], [5000], [5000]]);
    const signals = fetchImpl.mock.calls.map(([, init]) => init?.signal);
    expect(signals.every((signal) => signal instanceof AbortSignal)).toBe(true);
    expect(new Set(signals).size).toBe(3);
  });
});
