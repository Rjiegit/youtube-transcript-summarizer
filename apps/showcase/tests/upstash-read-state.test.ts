import { afterEach, describe, expect, it, vi } from "vitest";

import {
  applyReadStateMutations,
  getReadStateSnapshot,
} from "../server/utils/upstash-read-state";

const config = {
  url: "https://example.upstash.io",
  token: "redis-token",
};

describe("Upstash read state repository", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads and normalizes a Redis hash snapshot", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      result: [
        "article-1",
        JSON.stringify({ status: "read", updatedAt: "2026-09-20T00:00:00.000Z" }),
        "invalid",
        "not-json",
      ],
    }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getReadStateSnapshot(config, "personal")).resolves.toEqual({
      "article-1": { status: "read", updatedAt: "2026-09-20T00:00:00.000Z" },
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "https://example.upstash.io",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ Authorization: "Bearer redis-token" }),
      }),
    );
  });

  it("applies a mutation batch using one atomic script command", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      result: [
        "article-1",
        JSON.stringify({ status: "unread", updatedAt: "2026-09-20T00:01:00.000Z" }),
      ],
    }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await applyReadStateMutations(config, "personal", [{
      contentKey: "article-1",
      status: "unread",
      updatedAt: "2026-09-20T00:01:00.000Z",
    }]);

    expect(result["article-1"]?.status).toBe("unread");
    const request = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(JSON.parse(String(request.body))[0]).toBe("EVAL");
  });

  it("reports Upstash errors without leaking credentials", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: "ERR max requests limit exceeded",
    }), { status: 200 })));

    await expect(getReadStateSnapshot(config, "personal")).rejects.toThrow("ERR max requests limit exceeded");
  });
});
