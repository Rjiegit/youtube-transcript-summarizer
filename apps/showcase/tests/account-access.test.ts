// @vitest-environment node
import { beforeEach, expect, it, vi } from 'vitest';
import { createClient } from '@supabase/supabase-js';
import { createApp, toWebHandler } from 'h3';
import sessionHandler from '../server/api/account/session.get';

vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(),
}));

const config = {
  accountAuthEnabled: true,
  accountSupabaseUrl: 'https://project.supabase.co',
  accountSupabasePublishableKey: 'publishable',
  accountAllowedUserIds: 'invited-user',
};

beforeEach(() => {
  vi.stubGlobal('useRuntimeConfig', () => config);
  vi.mocked(createClient).mockReturnValue({
    auth: { getUser: vi.fn().mockResolvedValue({ data: { user: { id: 'invited-user' } }, error: null }) },
  } as never);
});

it('rejects requests without a bearer token', async () => {
  const app = createApp().use('/api/account/session', sessionHandler);
  const response = await toWebHandler(app)(new Request('https://site.test/api/account/session'));
  expect(response.status).toBe(401);
});

it('allows only configured user IDs after Supabase validates the token', async () => {
  const app = createApp().use('/api/account/session', sessionHandler);
  const response = await toWebHandler(app)(new Request('https://site.test/api/account/session', {
    headers: { authorization: 'Bearer access-token' },
  }));
  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({ userId: 'invited-user' });
  expect(vi.mocked(createClient).mock.results[0].value.auth.getUser).toHaveBeenCalledWith('access-token');
});

it('denies a valid Supabase user outside the allowed IDs', async () => {
  vi.mocked(createClient).mockReturnValue({ auth: {
    getUser: vi.fn().mockResolvedValue({ data: { user: { id: 'other-user' } }, error: null }),
  } } as never);
  const app = createApp().use('/api/account/session', sessionHandler);
  const response = await toWebHandler(app)(new Request('https://site.test/api/account/session', {
    headers: { authorization: 'Bearer valid-token' },
  }));
  expect(response.status).toBe(403);
});
