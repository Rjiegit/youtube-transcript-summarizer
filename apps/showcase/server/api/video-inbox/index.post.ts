import { defineEventHandler, readBody, getHeader, createError, setHeader } from 'h3';
import { authorizeSubmission, validateSubmission } from '../../utils/video-inbox';
import { requireAccountUser } from '../../utils/account-access';

export default defineEventHandler(async (event) => {
  setHeader(event, 'Cache-Control', 'private, no-store');
  const config = useRuntimeConfig(event);
  if (config.accountAuthEnabled) {
    if (!config.videoInboxOrigin || getHeader(event, 'origin') !== config.videoInboxOrigin) {
      throw createError({ statusCode: 403, statusMessage: 'Submission access denied' });
    }
    await requireAccountUser(event);
  } else {
    authorizeSubmission(getHeader(event, 'x-video-inbox-token'), String(config.videoInboxAccessToken || ''),
      getHeader(event, 'origin') || '', String(config.videoInboxOrigin || ''));
  }
  if (!config.videoInboxSupabaseUrl || !config.videoInboxSubmitToken || !config.videoInboxPublishableKey) {
    throw createError({ statusCode: 503, statusMessage: 'Inbox unavailable' });
  }
  const message = validateSubmission(await readBody(event));
  try {
    await $fetch(`${String(config.videoInboxSupabaseUrl).replace(/\/$/, '')}/rest/v1/rpc/video_inbox_submit`, {
      method: 'POST', timeout: 15000, retry: 0,
      headers: { apikey: String(config.videoInboxPublishableKey),
        'x-video-inbox-key': String(config.videoInboxSubmitToken) },
      body: { submission_id: message.submission_id, video_url: message.url },
    });
  } catch (error) {
    const status = typeof (error as { statusCode?: unknown })?.statusCode === 'number'
      ? (error as { statusCode: number }).statusCode : undefined;
    const category = status === 401 || status === 403 ? 'credentials'
      : status === 429 ? 'rate_limit' : status ? 'upstream' : 'network';
    console.warn('Video inbox submission failed', { category, status });
    throw createError({ statusCode: 503, statusMessage: 'Submission unconfirmed; retry with the same ID' });
  }
  return { accepted: true, submission_id: message.submission_id };
});
