import { computed } from "vue";

const COOKIE_KEY = "nuxt-showcase-read-results";

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

export function useReadResults() {
  const cookie = useCookie<ReadMap | string | null>(COOKIE_KEY, {
    default: () => ({}),
    sameSite: "lax",
  });

  const readMap = computed<ReadMap>({
    get() {
      return normalizeReadMap(cookie.value);
    },
    set(value) {
      cookie.value = value;
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

    readMap.value = {
      ...readMap.value,
      [id]: {
        readAt: new Date().toISOString(),
      },
    };
  }

  function markAsUnread(id: string): void {
    if (!id || !readMap.value[id]) {
      return;
    }

    const nextMap = { ...readMap.value };
    delete nextMap[id];
    readMap.value = nextMap;
  }

  return {
    readIds,
    readMap: computed(() => readMap.value),
    isRead,
    markAsRead,
    markAsUnread,
  };
}
