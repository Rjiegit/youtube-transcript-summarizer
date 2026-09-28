import { computed } from "vue";

import type {
  ReadStateMutation,
  ReadStateSnapshotResponse,
  ReadSyncSessionResponse,
  SyncedReadEntry,
  SyncedReadMap,
} from "../types/read-sync";

const STORAGE_KEY = "nuxt-showcase-read-results";
const SYNC_STATE_STORAGE_KEY = "nuxt-showcase-read-sync-state";
const READ_RESULTS_STATE_KEY = "showcase-read-results";
const READ_RESULTS_READY_STATE_KEY = "showcase-read-results-ready";
const READ_RESULTS_REVISION_STATE_KEY = "showcase-read-results-revision";
const READ_SYNC_STATE_KEY = "showcase-read-sync-state";
const READ_SYNC_ENABLED_STATE_KEY = "showcase-read-sync-enabled";
const READ_SYNC_INITIALIZED_STATE_KEY = "showcase-read-sync-initialized";
const READ_SYNC_STATUS_STATE_KEY = "showcase-read-sync-status";
const MAX_READ_ENTRIES = 500;
const MAX_SYNC_ENTRIES = 100;

type ReadEntry = {
  readAt: string;
};

type ReadMap = Record<string, ReadEntry>;

export type RemoteSyncStatus =
  | "local"
  | "connecting"
  | "authentication_required"
  | "unavailable"
  | "synced"
  | "error";

let remoteSyncPromise: Promise<void> | null = null;

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
      .slice(0, MAX_READ_ENTRIES),
  );
}

function normalizeSyncMap(rawValue: unknown): SyncedReadMap {
  if (!rawValue || typeof rawValue !== "object" || Array.isArray(rawValue)) {
    return {};
  }
  const entries: Array<[string, SyncedReadEntry]> = [];
  for (const [id, rawEntry] of Object.entries(rawValue)) {
    if (!id.trim() || !rawEntry || typeof rawEntry !== "object") {
      continue;
    }
    const entry = rawEntry as Partial<SyncedReadEntry>;
    if ((entry.status !== "read" && entry.status !== "unread") ||
        typeof entry.updatedAt !== "string" || !Number.isFinite(Date.parse(entry.updatedAt))) {
      continue;
    }
    entries.push([id, { status: entry.status, updatedAt: entry.updatedAt }]);
  }
  return Object.fromEntries(entries
    .sort(([, left], [, right]) => right.updatedAt.localeCompare(left.updatedAt))
    .slice(0, MAX_SYNC_ENTRIES));
}

function areReadMapsEqual(left: ReadMap, right: ReadMap): boolean {
  const leftEntries = Object.entries(left);
  const rightEntries = Object.entries(right);
  if (leftEntries.length !== rightEntries.length) {
    return false;
  }
  return leftEntries.every(([id, entry]) => right[id]?.readAt === entry.readAt);
}

function canUseLocalStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function readStoredJson(key: string): unknown {
  if (!canUseLocalStorage()) {
    return {};
  }
  try {
    const rawValue = window.localStorage.getItem(key);
    return rawValue ? JSON.parse(rawValue) : {};
  } catch {
    return {};
  }
}

function readStoredReadMap(): ReadMap {
  return trimReadMap(readStoredJson(STORAGE_KEY));
}

function readStoredSyncMap(): SyncedReadMap {
  return normalizeSyncMap(readStoredJson(SYNC_STATE_STORAGE_KEY));
}

function persistJson(key: string, value: Record<string, unknown>): void {
  if (!canUseLocalStorage()) {
    return;
  }
  try {
    if (Object.keys(value).length === 0) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, JSON.stringify(value));
    }
  } catch {
    // In-memory state remains available when storage quota or privacy mode blocks persistence.
  }
}

function persistReadMap(value: ReadMap): void {
  persistJson(STORAGE_KEY, value);
}

function persistSyncMap(value: SyncedReadMap): void {
  persistJson(SYNC_STATE_STORAGE_KEY, value);
}

function mergeReadMaps(left: ReadMap, right: ReadMap): ReadMap {
  return trimReadMap({ ...left, ...right });
}

function mergeSyncMaps(left: SyncedReadMap, right: SyncedReadMap): SyncedReadMap {
  const merged = { ...left };
  for (const [id, entry] of Object.entries(right)) {
    if (!merged[id] || entry.updatedAt > merged[id].updatedAt) {
      merged[id] = entry;
    }
  }
  return normalizeSyncMap(merged);
}

function seedSyncMapFromReads(syncMap: SyncedReadMap, readMap: ReadMap): SyncedReadMap {
  const seeded = { ...syncMap };
  for (const [id, entry] of Object.entries(readMap)) {
    if (!seeded[id] || entry.readAt > seeded[id].updatedAt) {
      seeded[id] = { status: "read", updatedAt: entry.readAt };
    }
  }
  return normalizeSyncMap(seeded);
}

function errorStatusCode(error: unknown): number | null {
  if (!error || typeof error !== "object") {
    return null;
  }
  const candidate = error as { status?: unknown; statusCode?: unknown; response?: { status?: unknown } };
  for (const value of [candidate.statusCode, candidate.status, candidate.response?.status]) {
    if (typeof value === "number") {
      return value;
    }
  }
  return null;
}

export function useReadResults() {
  const state = useState<ReadMap>(READ_RESULTS_STATE_KEY, () => ({}));
  const isReady = useState<boolean>(READ_RESULTS_READY_STATE_KEY, () => false);
  const revision = useState<number>(READ_RESULTS_REVISION_STATE_KEY, () => 0);
  const syncState = useState<SyncedReadMap>(READ_SYNC_STATE_KEY, () => ({}));
  const isRemoteSyncEnabled = useState<boolean>(READ_SYNC_ENABLED_STATE_KEY, () => false);
  const isRemoteSyncInitialized = useState<boolean>(READ_SYNC_INITIALIZED_STATE_KEY, () => false);
  const remoteSyncStatus = useState<RemoteSyncStatus>(READ_SYNC_STATUS_STATE_KEY, () => "local");

  function setReadMapValue(value: unknown, options: { forceRevision?: boolean } = {}): void {
    const normalizedValue = trimReadMap(value);
    const changed = !areReadMapsEqual(state.value, normalizedValue);
    state.value = normalizedValue;
    persistReadMap(normalizedValue);
    if (changed || options.forceRevision) {
      revision.value += 1;
    }
  }

  const readMap = computed<ReadMap>({
    get() {
      return state.value;
    },
    set(value) {
      setReadMapValue(value);
    },
  });

  function setSyncMapValue(value: unknown): void {
    syncState.value = normalizeSyncMap(value);
    persistSyncMap(syncState.value);
  }

  function applySyncMapToReads(value: SyncedReadMap): void {
    const nextReadMap = { ...readMap.value };
    for (const [id, entry] of Object.entries(value)) {
      if (entry.status === "read") {
        nextReadMap[id] = { readAt: entry.updatedAt };
      } else {
        delete nextReadMap[id];
      }
    }
    setSyncMapValue(value);
    setReadMapValue(nextReadMap);
  }

  function hydrateLocalState(options: { forceRender?: boolean } = {}): void {
    if (!canUseLocalStorage()) {
      return;
    }
    setReadMapValue(mergeReadMaps(readStoredReadMap(), readMap.value), {
      forceRevision: options.forceRender,
    });
    const storedSyncMap = mergeSyncMaps(readStoredSyncMap(), syncState.value);
    if (Object.keys(storedSyncMap).length > 0) {
      applySyncMapToReads(seedSyncMapFromReads(storedSyncMap, readMap.value));
    }
    isReady.value = true;
  }

  if (!isReady.value) {
    hydrateLocalState();
  }

  async function requestRemoteSnapshot(): Promise<ReadStateSnapshotResponse> {
    return await $fetch<ReadStateSnapshotResponse>("/api/read-state");
  }

  function setRemoteFailureStatus(error: unknown): void {
    if (errorStatusCode(error) === 401) {
      isRemoteSyncEnabled.value = false;
      remoteSyncStatus.value = "authentication_required";
      return;
    }
    remoteSyncStatus.value = "error";
  }

  async function pushRemoteMutations(mutations: ReadStateMutation[]): Promise<void> {
    if (!isRemoteSyncEnabled.value || mutations.length === 0) {
      return;
    }
    try {
      remoteSyncStatus.value = "connecting";
      const response = await $fetch<ReadStateSnapshotResponse>("/api/read-state/mutations", {
        method: "POST",
        body: { mutations },
      });
      applySyncMapToReads(mergeSyncMaps(syncState.value, normalizeSyncMap(response.entries)));
      remoteSyncStatus.value = "synced";
    } catch (error) {
      setRemoteFailureStatus(error);
    }
  }

  async function performRemoteSync(): Promise<void> {
    remoteSyncStatus.value = "connecting";
    const session = await $fetch<ReadSyncSessionResponse>("/api/read-sync/session");
    if (!session.available) {
      isRemoteSyncEnabled.value = false;
      remoteSyncStatus.value = "unavailable";
      return;
    }
    if (!session.authenticated) {
      isRemoteSyncEnabled.value = false;
      remoteSyncStatus.value = "authentication_required";
      return;
    }
    isRemoteSyncEnabled.value = true;
    const localSnapshot = seedSyncMapFromReads(syncState.value, readMap.value);
    const remoteResponse = await requestRemoteSnapshot();
    const remoteSnapshot = normalizeSyncMap(remoteResponse.entries);
    const localWinners = Object.entries(localSnapshot)
      .filter(([id, entry]) => !remoteSnapshot[id] || entry.updatedAt > remoteSnapshot[id].updatedAt)
      .map(([contentKey, entry]) => ({ contentKey, ...entry }));
    const merged = mergeSyncMaps(remoteSnapshot, localSnapshot);
    if (localWinners.length > 0) {
      const response = await $fetch<ReadStateSnapshotResponse>("/api/read-state/mutations", {
        method: "POST",
        body: { mutations: localWinners },
      });
      applySyncMapToReads(mergeSyncMaps(
        mergeSyncMaps(merged, normalizeSyncMap(response.entries)),
        syncState.value,
      ));
    } else {
      applySyncMapToReads(mergeSyncMaps(merged, syncState.value));
    }
    remoteSyncStatus.value = "synced";
  }

  function syncRemoteState(checkSession = false): Promise<void> {
    if (!isRemoteSyncEnabled.value && !checkSession) {
      remoteSyncStatus.value = "local";
      return Promise.resolve();
    }
    if (remoteSyncPromise) {
      return remoteSyncPromise;
    }
    remoteSyncPromise = performRemoteSync()
      .catch(setRemoteFailureStatus)
      .finally(() => {
        remoteSyncPromise = null;
      });
    return remoteSyncPromise;
  }

  function refreshReadState(options: { forceRender?: boolean } = {}): void {
    hydrateLocalState(options);
    if (isRemoteSyncEnabled.value) {
      void syncRemoteState();
    } else if (remoteSyncStatus.value === "error") {
      void syncRemoteState(true);
    }
  }

  async function setRemoteSyncEnabled(enabled: boolean): Promise<void> {
    if (!enabled) {
      isRemoteSyncEnabled.value = false;
      remoteSyncStatus.value = "local";
      return;
    }
    await syncRemoteState(true);
  }

  async function authenticateRemoteSync(accessToken: string): Promise<boolean> {
    try {
      remoteSyncStatus.value = "connecting";
      await $fetch<ReadSyncSessionResponse>("/api/read-sync/session", {
        method: "POST",
        body: { accessToken },
      });
      isRemoteSyncEnabled.value = true;
      await syncRemoteState();
      return remoteSyncStatus.value === "synced";
    } catch (error) {
      setRemoteFailureStatus(error);
      return false;
    }
  }

  const readIds = computed(() => Object.keys(readMap.value));

  function isRead(id: string): boolean {
    return Boolean(id && readMap.value[id]);
  }

  function recordMutations(mutations: ReadStateMutation[]): void {
    if (!isRemoteSyncEnabled.value && Object.keys(syncState.value).length === 0) {
      return;
    }
    const nextSyncMap = { ...syncState.value };
    for (const mutation of mutations) {
      nextSyncMap[mutation.contentKey] = {
        status: mutation.status,
        updatedAt: mutation.updatedAt,
      };
    }
    setSyncMapValue(nextSyncMap);
    void pushRemoteMutations(mutations);
  }

  function markAsRead(id: string): void {
    if (!id) {
      return;
    }
    const readAt = new Date().toISOString();
    readMap.value = {
      ...readMap.value,
      [id]: { readAt },
    };
    recordMutations([{ contentKey: id, status: "read", updatedAt: readAt }]);
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
    const nextValue = { ...readMap.value };
    for (const id of unreadIds) {
      nextValue[id] = { readAt };
    }
    readMap.value = nextValue;
    recordMutations(unreadIds.map((contentKey) => ({
      contentKey,
      status: "read",
      updatedAt: readAt,
    })));
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
    recordMutations([{
      contentKey: id,
      status: "unread",
      updatedAt: new Date().toISOString(),
    }]);
    if (canUseLocalStorage()) {
      isReady.value = true;
    }
  }

  if (canUseLocalStorage() && !isRemoteSyncInitialized.value) {
    isRemoteSyncInitialized.value = true;
    void syncRemoteState(true);
  }

  return {
    isReady: computed(() => isReady.value),
    readIds,
    readMap: computed(() => readMap.value),
    readRevision: computed(() => revision.value),
    isRemoteSyncEnabled: computed(() => isRemoteSyncEnabled.value),
    remoteSyncStatus: computed(() => remoteSyncStatus.value),
    isRead,
    markAsRead,
    markManyAsRead,
    markAsUnread,
    refreshReadState,
    setRemoteSyncEnabled,
    authenticateRemoteSync,
    syncRemoteState,
  };
}
