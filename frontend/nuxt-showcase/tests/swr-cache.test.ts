import { describe, expect, it, vi } from "vitest";

import { createSWRCache } from "../server/utils/swr-cache";

describe("SWR cache", () => {
  it("returns the cached value while still fresh", async () => {
    let now = 0;
    const cache = createSWRCache<string>({ ttlMs: 1000, now: () => now });
    const fetcher = vi.fn()
      .mockResolvedValueOnce("alpha")
      .mockResolvedValueOnce("beta");

    expect(await cache.get(fetcher)).toBe("alpha");
    now = 500;
    expect(await cache.get(fetcher)).toBe("alpha");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("returns stale data immediately and refreshes in background", async () => {
    let now = 0;
    const cache = createSWRCache<string>({ ttlMs: 1000, now: () => now });
    const refreshStarted = vi.fn();
    let releaseRefresh: (() => void) | null = null;

    const fetcher = vi.fn()
      .mockResolvedValueOnce("alpha")
      .mockImplementationOnce(
        () =>
          new Promise<string>((resolve) => {
            refreshStarted();
            releaseRefresh = () => resolve("beta");
          }),
      );

    expect(await cache.get(fetcher)).toBe("alpha");
    now = 1500;

    expect(await cache.get(fetcher)).toBe("alpha");
    expect(refreshStarted).toHaveBeenCalledTimes(1);
    releaseRefresh?.();
    await Promise.resolve();
    await Promise.resolve();

    now = 1600;
    expect(await cache.get(fetcher)).toBe("beta");
  });

  it("throws if the initial fetch fails and no snapshot exists", async () => {
    const cache = createSWRCache<string>({ ttlMs: 1000 });
    await expect(cache.get(async () => {
      throw new Error("boom");
    })).rejects.toThrow("boom");
  });
});
