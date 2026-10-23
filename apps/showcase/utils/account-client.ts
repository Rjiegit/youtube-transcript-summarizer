import { createClient } from '@supabase/supabase-js';
import type { SupabaseClient } from '@supabase/supabase-js';

let client: SupabaseClient | null = null;

export function getAccountClient(): SupabaseClient {
  if (import.meta.server) {
    throw new Error('Account client is browser-only.');
  }
  if (!client) {
    const config = useRuntimeConfig().public;
    if (!config.accountAuthEnabled || !config.accountSupabaseUrl || !config.accountSupabasePublishableKey) {
      throw new Error('Account sign-in is not configured.');
    }
    client = createClient(String(config.accountSupabaseUrl), String(config.accountSupabasePublishableKey));
  }
  return client;
}
