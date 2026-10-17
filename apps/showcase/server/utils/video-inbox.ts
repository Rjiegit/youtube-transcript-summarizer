import { createError } from 'h3';
import { isReadSyncAccessTokenValid } from './read-sync-auth';

export function authorizeSubmission(token: unknown, expected: string, origin: string, allowedOrigin: string) {
  if (!expected || !allowedOrigin) throw createError({ statusCode: 503, statusMessage: 'Inbox unavailable' });
  if (origin !== allowedOrigin || !isReadSyncAccessTokenValid(token, expected)) {
    throw createError({ statusCode: 403, statusMessage: 'Submission access denied' });
  }
}

export function validateSubmission(body: unknown): { submission_id: string; url: string } {
  const value = body as Record<string, unknown> | null;
  const invalid = () => createError({ statusCode: 400, statusMessage: 'Invalid video submission' });
  if (!value || typeof value.submission_id !== 'string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value.submission_id) ||
      typeof value.url !== 'string' || value.url.length > 2048) throw invalid();
  let parsed: URL;
  try { parsed = new URL(value.url); } catch { throw invalid(); }
  if (!['https:', 'http:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.port ||
      !['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'].includes(parsed.hostname)) throw invalid();
  const id = parsed.hostname === 'youtu.be' ? parsed.pathname.slice(1) :
    parsed.pathname === '/watch' ? parsed.searchParams.get('v') :
      /^\/(shorts|embed)\/([^/]+)$/.exec(parsed.pathname)?.[2];
  if (!id || !/^[A-Za-z0-9_-]{11}$/.test(id)) throw invalid();
  return { submission_id: value.submission_id.toLowerCase(), url: `https://www.youtube.com/watch?v=${id}` };
}
