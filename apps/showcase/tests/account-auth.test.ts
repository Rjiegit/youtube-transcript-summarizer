import { beforeEach, expect, it, vi } from 'vitest';
import { ref } from 'vue';

beforeEach(() => {
  vi.resetModules();
  vi.unstubAllGlobals();
  const state = new Map<string, ReturnType<typeof ref>>();
  vi.stubGlobal('useState', (key: string, initial: () => unknown) => {
    if (!state.has(key)) state.set(key, ref(initial()));
    return state.get(key);
  });
});

it('shows a configuration error without constructing the client when setup is incomplete', async () => {
  vi.stubGlobal('useRuntimeConfig', () => ({ public: { accountAuthEnabled: true } }));
  const getClient = vi.fn();
  vi.doMock('../utils/account-client', () => ({ getAccountClient: getClient }));
  const { useAccountAuth } = await import('../composables/useAccountAuth');
  const auth = useAccountAuth();
  await auth.initialize();
  expect(auth.ready.value).toBe(true);
  expect(auth.error.value).toContain('尚未完成設定');
  expect(getClient).not.toHaveBeenCalled();
});

it('ignores an identity response that arrives after sign-out', async () => {
  vi.stubGlobal('useRuntimeConfig', () => ({ public: {
    accountAuthEnabled: true, accountSupabaseUrl: 'https://project.supabase.co',
    accountSupabasePublishableKey: 'publishable',
  } }));
  vi.doMock('../utils/account-client', () => ({ getAccountClient: () => ({ auth: {
    getSession: vi.fn().mockResolvedValue({ data: { session: {
      user: { id: 'invited-user' }, access_token: 'access-token',
    } } }),
    signOut: vi.fn().mockResolvedValue({ error: null }),
  } }) }));
  let finishIdentity!: (value: unknown) => void;
  const fetchIdentity = vi.fn(() => new Promise((resolve) => { finishIdentity = resolve; }));
  vi.stubGlobal('$fetch', fetchIdentity);
  const { useAccountAuth } = await import('../composables/useAccountAuth');
  const auth = useAccountAuth();
  const refreshing = auth.refreshIdentity();
  await vi.waitFor(() => expect(fetchIdentity).toHaveBeenCalledOnce());
  await auth.signOut();
  finishIdentity({ userId: 'invited-user' });
  await refreshing;
  expect(auth.userId.value).toBeNull();
  expect(auth.sessionUserId.value).toBeNull();
});
