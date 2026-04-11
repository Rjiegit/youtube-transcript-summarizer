import { computed, ref } from "vue";

const STORAGE_KEY = "nuxt-showcase:read-results";

type ReadEntry = {
  readAt: string;
};

type ReadMap = Record<string, ReadEntry>;

const readMap = ref<ReadMap>({});
let initialized = false;

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function parseStoredReadMap(rawValue: string | null): ReadMap {
  if (!rawValue) {
    return {};
  }

  try {
    const parsed = JSON.parse(rawValue) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {};
    }

    return Object.fromEntries(
      Object.entries(parsed).filter(([id, value]) =>
        typeof id === "string" &&
        id.trim().length > 0 &&
        value &&
        typeof value === "object" &&
        typeof (value as { readAt?: unknown }).readAt === "string"),
    );
  } catch {
    return {};
  }
}

function persistReadMap() {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(readMap.value));
}

function ensureInitialized() {
  if (!canUseStorage() || initialized) {
    return;
  }

  readMap.value = parseStoredReadMap(window.localStorage.getItem(STORAGE_KEY));
  initialized = true;
}

export function useReadResults() {
  ensureInitialized();

  const readIds = computed(() => Object.keys(readMap.value));

  function isRead(id: string): boolean {
    return Boolean(id && readMap.value[id]);
  }

  function markAsRead(id: string): void {
    if (!id) {
      return;
    }

    ensureInitialized();
    readMap.value = {
      ...readMap.value,
      [id]: {
        readAt: new Date().toISOString(),
      },
    };
    persistReadMap();
  }

  function markAsUnread(id: string): void {
    if (!id || !readMap.value[id]) {
      return;
    }

    const nextMap = { ...readMap.value };
    delete nextMap[id];
    readMap.value = nextMap;
    persistReadMap();
  }

  return {
    readIds,
    readMap: computed(() => readMap.value),
    isRead,
    markAsRead,
    markAsUnread,
  };
}
