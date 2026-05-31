import { computed } from "vue";

const STORAGE_KEY = "nuxt-showcase-read-results";
const READ_RESULTS_STATE_KEY = "showcase-read-results";
const READ_RESULTS_READY_STATE_KEY = "showcase-read-results-ready";
const MAX_READ_RESULTS = 100;

type ReadEntry = {
  readAt: string;
};

type ReadMap = Record<string, ReadEntry>;

function normalizeReadMap(rawValue: unknown): ReadMap {
  if (!rawValue || typeof rawValue !== "object" || Array.isArray(rawValue)) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(rawValue).filter(([id, value]) =>
      typeof id === "string" &&
      id.trim().length > 0 &&
      value &&
      typeof value === "object" &&
      typeof (value as { readAt?: unknown }).readAt === "string"),
  );
}

function trimReadMap(rawValue: unknown): ReadMap {
  const normalizedValue = normalizeReadMap(rawValue);

  return Object.fromEntries(
    Object.entries(normalizedValue)
      .sort(([, leftEntry], [, rightEntry]) => rightEntry.readAt.localeCompare(leftEntry.readAt))
      .slice(0, MAX_READ_RESULTS),
  );
}

function canUseLocalStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function readStoredReadMap(): ReadMap {
  if (!canUseLocalStorage()) {
    return {};
  }

  try {
    const rawValue = window.localStorage.getItem(STORAGE_KEY);
    if (!rawValue) {
      return {};
    }
    return trimReadMap(JSON.parse(rawValue));
  } catch {
    return {};
  }
}

function persistReadMap(value: ReadMap): void {
  if (!canUseLocalStorage()) {
    return;
  }

  try {
    if (Object.keys(value).length === 0) {
      window.localStorage.removeItem(STORAGE_KEY);
      return;
    }

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    // Ignore storage quota and privacy mode failures; in-memory state still works for this session.
  }
}

function mergeReadMaps(left: ReadMap, right: ReadMap): ReadMap {
  return trimReadMap({
    ...left,
    ...right,
  });
}

export function useReadResults() {
  const state = useState<ReadMap>(READ_RESULTS_STATE_KEY, () => ({}));
  const isReady = useState<boolean>(READ_RESULTS_READY_STATE_KEY, () => false);

  if (!isReady.value && canUseLocalStorage()) {
    state.value = mergeReadMaps(readStoredReadMap(), state.value);
    persistReadMap(state.value);
    isReady.value = true;
  }

  const readMap = computed<ReadMap>({
    get() {
      return state.value;
    },
    set(value) {
      const normalizedValue = trimReadMap(value);
      state.value = normalizedValue;
      persistReadMap(normalizedValue);
    },
  });

  const readIds = computed(() => Object.keys(readMap.value));

  function isRead(id: string): boolean {
    return Boolean(id && readMap.value[id]);
  }

  function markAsRead(id: string): void {
    if (!id) {
      return;
    }

    const nextValue = {
      ...readMap.value,
      [id]: {
        readAt: new Date().toISOString(),
      },
    };

    readMap.value = nextValue;
    if (canUseLocalStorage()) {
      isReady.value = true;
    }
  }

  function markManyAsRead(ids: string[]): void {
    const unreadIds = Array.from(new Set(ids.map((id) => id.trim()).filter((id) => id && !readMap.value[id])));

    if (unreadIds.length === 0) {
      return;
    }

    const readAt = new Date().toISOString();
    const nextValue = {
      ...readMap.value,
    };

    for (const id of unreadIds) {
      nextValue[id] = {
        readAt,
      };
    }

    readMap.value = nextValue;
    if (canUseLocalStorage()) {
      isReady.value = true;
    }
  }

  function markAsUnread(id: string): void {
    if (!id || !readMap.value[id]) {
      return;
    }

    const nextMap = { ...readMap.value };
    delete nextMap[id];
    readMap.value = nextMap;
    if (canUseLocalStorage()) {
      isReady.value = true;
    }
  }

  return {
    isReady: computed(() => isReady.value),
    readIds,
    readMap: computed(() => readMap.value),
    isRead,
    markAsRead,
    markManyAsRead,
    markAsUnread,
  };
}
