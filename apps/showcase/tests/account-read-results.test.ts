import { beforeEach, expect, it, vi } from 'vitest';
import { nextTick, ref } from 'vue';

beforeEach(() => { vi.resetModules(); vi.unstubAllGlobals(); });

it('does not track guest reads or use the legacy localStorage state', async () => {
  vi.stubGlobal('useRuntimeConfig', () => ({ public: { accountAuthEnabled: true } }));
  const state = new Map<string, ReturnType<typeof ref>>();
  vi.stubGlobal('useState', (key: string, init: () => unknown) => {
    if (!state.has(key)) state.set(key, ref(init()));
    return state.get(key);
  });
  const userId = ref<string | null>(null);
  vi.doMock('../composables/useAccountAuth', () => ({ useAccountAuth: () => ({
    userId, initialize: vi.fn().mockResolvedValue(undefined), getAccessToken: vi.fn().mockResolvedValue(null),
  }) }));
  const fetchMock = vi.fn();
  vi.stubGlobal('$fetch', fetchMock);
  const { useReadResults } = await import('../composables/useReadResults');
  const reads = useReadResults();
  reads.markAsRead('article-1');
  expect(reads.isRead('article-1')).toBe(false);
  expect(reads.isReady.value).toBe(true);
  expect(reads.remoteSyncStatus.value).toBe('authentication_required');
  expect(fetchMock).not.toHaveBeenCalled();
});

it('loads only the signed-in account snapshot and sends a bearer token for changes', async () => {
  const state = new Map<string, ReturnType<typeof ref>>();
  vi.stubGlobal('useState', (key: string, init: () => unknown) => {
    if (!state.has(key)) state.set(key, ref(init()));
    return state.get(key);
  });
  const userId = ref<string | null>('invited-user');
  vi.doMock('../composables/useAccountAuth', () => ({ useAccountAuth: () => ({
    userId, initialize: vi.fn().mockResolvedValue(undefined),
    getAccessToken: vi.fn().mockResolvedValue('access-token'),
  }) }));
  const fetchMock = vi.fn(async (path: string) => ({ entries: path === '/api/read-state'
    ? { first: { status: 'read', updatedAt: '2026-10-23T00:00:00.000Z' } }
    : { first: { status: 'unread', updatedAt: '2026-10-23T01:00:00.000Z' } } }));
  vi.stubGlobal('$fetch', fetchMock);
  const { useAccountReadResults } = await import('../composables/useAccountReadResults');
  const reads = useAccountReadResults();
  await reads.syncRemoteState();
  expect(reads.isRead('first')).toBe(true);
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ headers: { Authorization: 'Bearer access-token' } });
  reads.markAsUnread('first');
  await vi.waitFor(() => expect(reads.isRead('first')).toBe(false));
  expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'POST',
    headers: { Authorization: 'Bearer access-token' } });
});

it('loads the next account after an earlier account request finishes', async () => {
  const state = new Map<string, ReturnType<typeof ref>>();
  vi.stubGlobal('useState', (key: string, init: () => unknown) => {
    if (!state.has(key)) state.set(key, ref(init()));
    return state.get(key);
  });
  const userId = ref<string | null>('first-user');
  vi.doMock('../composables/useAccountAuth', () => ({ useAccountAuth: () => ({
    userId, initialize: vi.fn().mockResolvedValue(undefined),
    getAccessToken: vi.fn().mockResolvedValue('access-token'),
  }) }));
  let finishFirst!: (value: unknown) => void;
  const fetchMock = vi.fn()
    .mockImplementationOnce(() => new Promise((resolve) => { finishFirst = resolve; }))
    .mockResolvedValueOnce({ entries: { second: { status: 'read', updatedAt: '2026-10-23T00:00:00.000Z' } } });
  vi.stubGlobal('$fetch', fetchMock);
  const { useAccountReadResults } = await import('../composables/useAccountReadResults');
  const reads = useAccountReadResults();
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  userId.value = 'second-user';
  finishFirst({ entries: { first: { status: 'read', updatedAt: '2026-10-23T00:00:00.000Z' } } });
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  await vi.waitFor(() => expect(reads.isRead('second')).toBe(true));
  expect(reads.isRead('first')).toBe(false);
});

async function setupAccountReads(fetchMock: ReturnType<typeof vi.fn>) {
  const state = new Map<string, ReturnType<typeof ref>>();
  vi.stubGlobal('useState', (key: string, init: () => unknown) => {
    if (!state.has(key)) state.set(key, ref(init()));
    return state.get(key);
  });
  const userId = ref<string | null>('invited-user');
  const getAccessToken = vi.fn().mockResolvedValue('access-token');
  vi.doMock('../composables/useAccountAuth', () => ({ useAccountAuth: () => ({
    userId, initialize: vi.fn().mockResolvedValue(undefined),
    getAccessToken,
  }) }));
  vi.stubGlobal('$fetch', fetchMock);
  const { useAccountReadResults } = await import('../composables/useAccountReadResults');
  return { reads: useAccountReadResults(), userId, getAccessToken };
}

it('fetches a fresh snapshot after returning to the same account during an earlier request', async () => {
  let finishEarlier!: (value: unknown) => void;
  const fetchMock = vi.fn()
    .mockImplementationOnce(() => new Promise((resolve) => { finishEarlier = resolve; }))
    .mockResolvedValue({ entries: { fresh: { status: 'read', updatedAt: '2026-10-23T01:00:00.000Z' } } });
  const { reads, userId } = await setupAccountReads(fetchMock);
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  userId.value = null;
  await nextTick();
  userId.value = 'invited-user';
  await nextTick();
  finishEarlier({ entries: { stale: { status: 'read', updatedAt: '2026-10-23T00:00:00.000Z' } } });
  await vi.waitFor(() => expect(reads.isRead('fresh')).toBe(true));
  expect(reads.isRead('stale')).toBe(false);
});

it('serializes changes so earlier snapshots cannot overwrite later read operations', async () => {
  let finishFirst!: (value: unknown) => void;
  let finishSecond!: (value: unknown) => void;
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ entries: {} })
    .mockImplementationOnce(() => new Promise((resolve) => { finishFirst = resolve; }))
    .mockImplementationOnce(() => new Promise((resolve) => { finishSecond = resolve; }));
  const { reads } = await setupAccountReads(fetchMock);
  await reads.syncRemoteState();
  reads.markAsRead('first');
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  reads.markAsRead('second');
  await nextTick();
  await Promise.resolve();
  expect(fetchMock).toHaveBeenCalledTimes(2);
  const first = { status: 'read', updatedAt: '2026-10-23T00:00:00.000Z' };
  finishFirst({ entries: { first } });
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  finishSecond({ entries: { first, second: first } });
  await vi.waitFor(() => expect(reads.isRead('second')).toBe(true));
  expect(reads.isRead('first')).toBe(true);
});

it('discards queued changes and stale responses across sign-out and sign-in', async () => {
  let finishEarlier!: (value: unknown) => void;
  const entry = { status: 'read', updatedAt: '2026-10-23T00:00:00.000Z' };
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ entries: {} })
    .mockImplementationOnce(() => new Promise((resolve) => { finishEarlier = resolve; }))
    .mockResolvedValueOnce({ entries: { fresh: entry } });
  const { reads, userId } = await setupAccountReads(fetchMock);
  await reads.syncRemoteState();
  reads.markAsRead('first');
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  reads.markAsRead('queued');
  userId.value = null;
  userId.value = 'invited-user';
  finishEarlier({ entries: { first: entry } });
  await vi.waitFor(() => expect(reads.isRead('fresh')).toBe(true));
  expect(fetchMock.mock.calls.map(([path]) => path))
    .toEqual(['/api/read-state', '/api/read-state/mutations', '/api/read-state']);
  expect(reads.isRead('first')).toBe(false);
  expect(reads.isRead('queued')).toBe(false);
});

it('reports a token refresh failure without sending a mutation', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ entries: {} });
  const { reads, getAccessToken } = await setupAccountReads(fetchMock);
  await reads.syncRemoteState();
  getAccessToken.mockRejectedValueOnce(new Error('Session unavailable'));
  reads.markAsRead('first');
  await vi.waitFor(() => expect(reads.remoteSyncStatus.value).toBe('error'));
  expect(fetchMock).toHaveBeenCalledTimes(1);
});
