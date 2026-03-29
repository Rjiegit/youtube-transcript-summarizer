export interface SWRCacheOptions {
  ttlMs: number;
  now?: () => number;
}

export interface SWRCache<T> {
  get(fetcher: () => Promise<T>): Promise<T>;
  peek(): T | null;
  ageMs(): number | null;
}

export function createSWRCache<T>(options: SWRCacheOptions): SWRCache<T> {
  let snapshot: { value: T; fetchedAt: number } | null = null;
  let refreshPromise: Promise<T> | null = null;
  const now = options.now ?? (() => Date.now());

  const startRefresh = (fetcher: () => Promise<T>, swallowError: boolean): Promise<T> => {
    if (!refreshPromise) {
      refreshPromise = fetcher()
        .then((value) => {
          snapshot = {
            value,
            fetchedAt: now(),
          };
          return value;
        })
        .catch((error) => {
          if (swallowError && snapshot) {
            return snapshot.value;
          }
          throw error;
        })
        .finally(() => {
          refreshPromise = null;
        });
    }

    return refreshPromise;
  };

  return {
    async get(fetcher: () => Promise<T>): Promise<T> {
      if (snapshot) {
        const age = now() - snapshot.fetchedAt;
        if (age < options.ttlMs) {
          return snapshot.value;
        }

        void startRefresh(fetcher, true);
        return snapshot.value;
      }

      return startRefresh(fetcher, false);
    },
    peek(): T | null {
      return snapshot?.value ?? null;
    },
    ageMs(): number | null {
      return snapshot ? now() - snapshot.fetchedAt : null;
    },
  };
}
