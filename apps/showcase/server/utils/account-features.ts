export interface AccountFeatures {
  authEnabled: boolean;
  configured: boolean;
}

function enabled(value: string | undefined): boolean {
  return ['1', 'true', 'yes', 'on'].includes((value || '').trim().toLowerCase());
}

export function resolveAccountFeatures(env: Record<string, string | undefined>): AccountFeatures {
  const authEnabled = enabled(env.SHOWCASE_ACCOUNT_AUTH_ENABLED);
  return {
    authEnabled,
    configured: Boolean(env.SHOWCASE_SUPABASE_URL?.trim() && env.SHOWCASE_SUPABASE_PUBLISHABLE_KEY?.trim()),
  };
}
