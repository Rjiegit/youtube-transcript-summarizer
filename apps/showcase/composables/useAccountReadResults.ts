import { computed, watch } from 'vue';
import type { ReadStateMutation, ReadStateSnapshotResponse, SyncedReadMap } from '../types/read-sync';
import { useAccountAuth } from './useAccountAuth';

let loadPromise: Promise<void> | null = null;
let loadingUserId: string | null = null;
let loadingGeneration = -1;
let requestQueue: Promise<void> = Promise.resolve();

function enqueueRequest(operation: () => Promise<void>): Promise<void> {
  const pending = requestQueue.then(operation);
  requestQueue = pending.catch(() => {});
  return pending;
}

export function useAccountReadResults() {
  const auth = useAccountAuth();
  const entries = useState<SyncedReadMap>('account-read-entries', () => ({}));
  const loadedUserId = useState<string | null>('account-read-loaded-user', () => null);
  const accountGeneration = useState('account-read-generation', () => 0);
  const ready = useState('account-read-ready', () => true);
  const revision = useState('account-read-revision', () => 0);
  const status = useState<'local' | 'connecting' | 'authentication_required' | 'synced' | 'error'>(
    'account-read-status', () => 'authentication_required');

  const readMap = computed(() => Object.fromEntries(Object.entries(entries.value)
    .filter(([, entry]) => entry.status === 'read')
    .map(([id, entry]) => [id, { readAt: entry.updatedAt }])));

  function clearForAccount(userId: string | null): void {
    if (loadedUserId.value === userId) return;
    loadedUserId.value = userId;
    accountGeneration.value += 1;
    entries.value = {};
    ready.value = !userId;
    status.value = userId ? 'connecting' : 'authentication_required';
    revision.value += 1;
  }

  async function syncRemoteState(): Promise<void> {
    const userId = auth.userId.value;
    clearForAccount(userId);
    if (!userId) return;
    const generation = accountGeneration.value;
    const isCurrent = () => auth.userId.value === userId && accountGeneration.value === generation;
    if (loadPromise) {
      if (loadingUserId === userId && loadingGeneration === generation) return loadPromise;
      await loadPromise;
      if (!isCurrent()) return;
      return syncRemoteState();
    }
    loadingUserId = userId;
    loadingGeneration = generation;
    loadPromise = enqueueRequest(async () => {
      if (!isCurrent()) return;
      try {
        const token = await auth.getAccessToken();
        if (!isCurrent()) return;
        if (!token) { status.value = 'authentication_required'; return; }
        const response = await $fetch<ReadStateSnapshotResponse>('/api/read-state', {
          headers: { Authorization: `Bearer ${token}` }, timeout: 15000, retry: 0,
        });
        if (!isCurrent()) return;
        entries.value = response.entries;
        status.value = 'synced';
        revision.value += 1;
      } catch {
        if (isCurrent()) status.value = 'error';
      } finally {
        if (isCurrent()) ready.value = true;
      }
    }).finally(() => { loadPromise = null; loadingUserId = null; loadingGeneration = -1; });
    return loadPromise;
  }

  async function recordMutations(mutations: ReadStateMutation[]): Promise<void> {
    const userId = auth.userId.value;
    if (!userId || !ready.value || mutations.length === 0) return;
    const generation = accountGeneration.value;
    const isCurrent = () => auth.userId.value === userId && accountGeneration.value === generation;
    return enqueueRequest(async () => {
      if (!isCurrent()) return;
      status.value = 'connecting';
      try {
        const token = await auth.getAccessToken();
        if (!isCurrent()) return;
        if (!token) { status.value = 'authentication_required'; return; }
        const response = await $fetch<ReadStateSnapshotResponse>('/api/read-state/mutations', {
          method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: { mutations },
          timeout: 15000, retry: 0,
        });
        if (!isCurrent()) return;
        entries.value = response.entries;
        status.value = 'synced';
        revision.value += 1;
      } catch {
        if (isCurrent()) status.value = 'error';
      }
    });
  }

  function change(ids: string[], nextStatus: 'read' | 'unread'): void {
    if (!auth.userId.value || !ready.value) return;
    const updatedAt = new Date().toISOString();
    const mutations = [...new Set(ids.map((id) => id.trim()).filter(Boolean))]
      .filter((id) => entries.value[id]?.status !== nextStatus)
      .map((contentKey) => ({ contentKey, status: nextStatus, updatedAt }));
    void recordMutations(mutations);
  }

  watch(auth.userId, (userId) => {
    clearForAccount(userId);
    if (userId) void syncRemoteState();
  }, { immediate: true, flush: 'sync' });
  if (import.meta.client) void auth.initialize();

  return {
    isReady: computed(() => ready.value),
    readIds: computed(() => Object.keys(readMap.value)),
    readMap,
    readRevision: computed(() => revision.value),
    isRemoteSyncEnabled: computed(() => Boolean(auth.userId.value)),
    remoteSyncStatus: computed(() => status.value),
    isRead: (id: string) => Boolean(readMap.value[id]),
    markAsRead: (id: string) => change([id], 'read'),
    markManyAsRead: (ids: string[]) => change(ids, 'read'),
    markAsUnread: (id: string) => change([id], 'unread'),
    refreshReadState: () => { if (auth.userId.value) void syncRemoteState(); },
    setRemoteSyncEnabled: async () => { await syncRemoteState(); },
    authenticateRemoteSync: async () => false,
    syncRemoteState,
  };
}
