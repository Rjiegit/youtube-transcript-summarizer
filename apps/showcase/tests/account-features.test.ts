import { describe, expect, it } from 'vitest';
import { resolveAccountFeatures } from '../server/utils/account-features';

describe('account feature toggles', () => {
  it('keeps account mode off by default', () => {
    expect(resolveAccountFeatures({})).toEqual({
      authEnabled: false,
      configured: false,
    });
  });

  it('enables account mode with one switch and reports incomplete configuration', () => {
    expect(resolveAccountFeatures({
      SHOWCASE_ACCOUNT_AUTH_ENABLED: 'true',
    })).toEqual({
      authEnabled: true,
      configured: false,
    });
  });

  it('reports a configured account mode when the Supabase settings are present', () => {
    expect(resolveAccountFeatures({
      SHOWCASE_ACCOUNT_AUTH_ENABLED: 'true',
      SHOWCASE_SUPABASE_URL: 'https://project.supabase.co',
      SHOWCASE_SUPABASE_PUBLISHABLE_KEY: 'publishable',
    })).toEqual({ authEnabled: true, configured: true });
  });
});
