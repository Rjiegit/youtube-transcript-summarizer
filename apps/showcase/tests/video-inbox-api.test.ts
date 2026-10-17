// @vitest-environment node

import { afterEach, expect, it, vi } from 'vitest';
import { createApp, toWebHandler } from 'h3';
import handler from '../server/api/video-inbox/index.post';

const config = {
  videoInboxAccessToken: 'allowed', videoInboxOrigin: 'https://site.test',
  videoInboxSupabaseUrl: 'https://project.supabase.co', videoInboxSubmitToken: 'scoped-submit',
  videoInboxPublishableKey: 'publishable',
};
afterEach(() => vi.unstubAllGlobals());
it('authenticates before forwarding only validated data to the scoped submit RPC', async () => {
  vi.stubGlobal('useRuntimeConfig', () => config);
  const rpc = vi.fn().mockResolvedValue(null);
  vi.stubGlobal('$fetch', rpc);
  const call = toWebHandler(createApp().use(handler));
  const url = 'https://site.test/api/video-inbox';
  const request = { method: 'POST', headers: { origin: 'https://site.test', 'content-type': 'application/json' },
    body: JSON.stringify({ submission_id: 'b1cdf760-37af-4b70-95ac-64484a97da91', url: 'https://youtu.be/dQw4w9WgXcQ' }) };
  expect((await call(new Request(url, request))).status).toBe(403);
  expect(rpc).not.toHaveBeenCalled();
  const response = await call(new Request(url, { ...request, headers: { ...request.headers, 'x-video-inbox-token': 'allowed' } }));
  expect(response.status).toBe(200);
  expect(response.headers.get('cache-control')).toBe('private, no-store');
  expect(rpc.mock.calls[0][0]).toBe('https://project.supabase.co/rest/v1/rpc/video_inbox_submit');
  expect(rpc.mock.calls[0][1].headers['x-video-inbox-key']).toBe('scoped-submit');
  expect(rpc.mock.calls[0][1].body.video_url).toBe('https://www.youtube.com/watch?v=dQw4w9WgXcQ');

});

it('logs only safe upstream metadata and preserves an unconfirmed response', async () => {
  vi.stubGlobal('useRuntimeConfig', () => config);
  vi.stubGlobal('$fetch', vi.fn().mockRejectedValue({ statusCode: 401, message: 'private-key', data: 'private-body' }));
  const log = vi.spyOn(console, 'warn').mockImplementation(() => {});
  try {
    const call = toWebHandler(createApp().use(handler));
    const response = await call(new Request('https://site.test/api/video-inbox', {
      method: 'POST', headers: { origin: 'https://site.test', 'content-type': 'application/json', 'x-video-inbox-token': 'allowed' },
      body: JSON.stringify({ submission_id: 'b1cdf760-37af-4b70-95ac-64484a97da91', url: 'https://youtu.be/dQw4w9WgXcQ' }),
    }));
    expect(response.status).toBe(503);
    expect(log).toHaveBeenCalledWith('Video inbox submission failed', { category: 'credentials', status: 401 });
    expect(JSON.stringify(log.mock.calls)).not.toContain('private');
    expect(await response.text()).not.toContain('private');
  } finally { log.mockRestore(); }
});
