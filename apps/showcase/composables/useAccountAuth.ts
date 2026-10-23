import { computed, ref, type Ref } from 'vue';
import { getAccountClient } from '../utils/account-client';

let initPromise: Promise<void> | null = null;
let identityRevision = 0;

export function useAccountAuth() {
  const config = typeof useRuntimeConfig === 'function' ? useRuntimeConfig().public : {};
  const enabled = Boolean(config.accountAuthEnabled);
  const configured = Boolean(config.accountSupabaseUrl && config.accountSupabasePublishableKey);
  const state = <T>(key: string, initial: () => T): Ref<T> =>
    typeof useState === 'function' ? useState<T>(key, initial) : ref(initial()) as Ref<T>;
  const ready = state('account-auth-ready', () => !enabled);
  const userId = state<string | null>('account-auth-user-id', () => null);
  const sessionUserId = state<string | null>('account-auth-session-user-id', () => null);
  const error = state('account-auth-error', () => '');

  async function getAccessToken(): Promise<string | null> {
    if (!enabled || !configured || import.meta.server) return null;
    const { data } = await getAccountClient().auth.getSession();
    return data.session?.access_token || null;
  }

  async function refreshIdentity(): Promise<void> {
    const revision = ++identityRevision;
    userId.value = null;
    const { data } = await getAccountClient().auth.getSession();
    if (revision !== identityRevision) return;
    sessionUserId.value = data.session?.user.id || null;
    const token = data.session?.access_token || null;
    if (!token) {
      ready.value = true;
      return;
    }
    try {
      const result = await $fetch<{ userId: string }>('/api/account/session', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (revision !== identityRevision) return;
      userId.value = result.userId;
      error.value = '';
    } catch {
      if (revision === identityRevision) error.value = '這個帳號尚未取得網站使用權限。';
    } finally {
      if (revision === identityRevision) ready.value = true;
    }
  }

  function initialize(): Promise<void> {
    if (!enabled || import.meta.server || ready.value) return Promise.resolve();
    if (!configured) {
      error.value = '帳號登入尚未完成設定。';
      ready.value = true;
      return Promise.resolve();
    }
    if (!initPromise) {
      initPromise = Promise.resolve().then(() => {
        const client = getAccountClient();
        client.auth.onAuthStateChange(() => {
          setTimeout(() => {
            void refreshIdentity().catch(() => {
              error.value = '登入服務暫時無法使用。';
              ready.value = true;
            });
          }, 0);
        });
        return refreshIdentity();
      })
        .catch(() => {
          error.value = '登入服務暫時無法使用。';
          ready.value = true;
        })
        .finally(() => { initPromise = null; });
    }
    return initPromise;
  }

  async function signInWithPassword(email: string, password: string): Promise<void> {
    const { error: signInError } = await getAccountClient().auth.signInWithPassword({
      email, password,
    });
    if (signInError) throw signInError;
    await refreshIdentity();
  }

  async function requestPasswordReset(email: string): Promise<void> {
    const { error: resetError } = await getAccountClient().auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/login`,
    });
    if (resetError) throw resetError;
  }

  async function updatePassword(password: string): Promise<void> {
    const { error: updateError } = await getAccountClient().auth.updateUser({ password });
    if (updateError) throw updateError;
  }

  async function signOut(): Promise<void> {
    const { error: signOutError } = await getAccountClient().auth.signOut();
    if (signOutError) throw signOutError;
    identityRevision += 1;
    userId.value = null;
    sessionUserId.value = null;
    ready.value = true;
    error.value = '';
  }

  return {
    enabled,
    ready: computed(() => ready.value),
    userId: computed(() => userId.value),
    sessionUserId: computed(() => sessionUserId.value),
    error: computed(() => error.value),
    initialize,
    refreshIdentity,
    getAccessToken,
    signInWithPassword,
    requestPasswordReset,
    updatePassword,
    signOut,
  };
}
