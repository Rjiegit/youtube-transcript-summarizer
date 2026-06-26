export interface SWRCacheOptions {
  ttlMs: number;
  now?: () => number;
}

export interface SWRCache<T> {
  get(fetcher: () => Promise<T>): Promise<T>;
  refresh(fetcher: () => Promise<T>): Promise<T>;
  peek(): T | null;
  ageMs(): number | null;
}

export function createSWRCache<T>(options: SWRCacheOptions): SWRCache<T> {
  let snapshot: { value: T; fetchedAt: number } | null = null;
  let refreshPromise: Promise<T> | null = null;
  let latestRefreshId = 0;
  const now = options.now ?? (() => Date.now());

  const startRefresh = (
    fetcher: () => Promise<T>,
    options: { swallowError: boolean; reuseInFlight: boolean },
  ): Promise<T> => {
    if (options.reuseInFlight && refreshPromise) {
      return refreshPromise;
    }

    const refreshId = latestRefreshId + 1;
    latestRefreshId = refreshId;
    const nextRefreshPromise = fetcher()
      .then((value) => {
        if (refreshId === latestRefreshId) {
          snapshot = {
            value,
            fetchedAt: now(),
          };
        }
        return value;
      })
      .catch((error) => {
        if (options.swallowError && snapshot) {
          return snapshot.value;
        }
        throw error;
      })
      .finally(() => {
        if (refreshPromise === nextRefreshPromise) {
          refreshPromise = null;
        }
      });

    refreshPromise = nextRefreshPromise;
    return nextRefreshPromise;
  };

  return {
    async get(fetcher: () => Promise<T>): Promise<T> {
      if (snapshot) {
        const age = now() - snapshot.fetchedAt;
        if (age < options.ttlMs) {
          return snapshot.value;
        }

        void startRefresh(fetcher, { swallowError: true, reuseInFlight: true });
        return snapshot.value;
      }

      return startRefresh(fetcher, { swallowError: false, reuseInFlight: true });
    },
    refresh(fetcher: () => Promise<T>): Promise<T> {
      return startRefresh(fetcher, { swallowError: false, reuseInFlight: false });
    },
    peek(): T | null {
      return snapshot?.value ?? null;
    },
    ageMs(): number | null {
      return snapshot ? now() - snapshot.fetchedAt : null;
    },
  };
}
