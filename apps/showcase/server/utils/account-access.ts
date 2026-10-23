import { createClient } from '@supabase/supabase-js';
import { createError, getHeader, setHeader } from 'h3';
import type { H3Event } from 'h3';

interface AccountConfig {
  accountAuthEnabled?: boolean;
  accountSupabaseUrl?: string;
  accountSupabasePublishableKey?: string;
  accountAllowedUserIds?: string;
}

export async function requireAccountUser(event: H3Event): Promise<string> {
  setHeader(event, 'Cache-Control', 'private, no-store');
  const config = useRuntimeConfig(event) as AccountConfig;
  if (!config.accountAuthEnabled || !config.accountSupabaseUrl ||
      !config.accountSupabasePublishableKey || !config.accountAllowedUserIds?.trim()) {
    throw createError({ statusCode: 503, statusMessage: 'Account access unavailable' });
  }
  const authorization = getHeader(event, 'authorization') || '';
  const match = /^Bearer ([^\s]+)$/.exec(authorization);
  if (!match) {
    throw createError({ statusCode: 401, statusMessage: 'Sign in required' });
  }
  const client = createClient(config.accountSupabaseUrl, config.accountSupabasePublishableKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  let result;
  try {
    result = await client.auth.getUser(match[1]);
  } catch {
    throw createError({ statusCode: 503, statusMessage: 'Account service unavailable' });
  }
  const { data, error } = result;
  if (error || !data.user?.id) {
    throw createError({ statusCode: 401, statusMessage: 'Invalid session' });
  }
  const allowedIds = new Set(config.accountAllowedUserIds.split(',').map((id) => id.trim()).filter(Boolean));
  if (!allowedIds.has(data.user.id)) {
    throw createError({ statusCode: 403, statusMessage: 'Account access denied' });
  }
  return data.user.id;
}
