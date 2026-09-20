import { createError, getCookie, setHeader } from "h3";
import type { H3Event } from "h3";

import {
  READ_SYNC_COOKIE_NAME,
  verifyReadSyncSessionToken,
} from "./read-sync-auth";
import type { ReadSyncPrincipal } from "./read-sync-auth";
import { resolveReadSyncConfig } from "./read-sync-config";
import type { ReadSyncConfig } from "./read-sync-config";

export function getRequestReadSyncConfig(event: H3Event): ReadSyncConfig {
  return resolveReadSyncConfig({ runtimeConfig: useRuntimeConfig(event) });
}

export function setPrivateNoStore(event: H3Event): void {
  setHeader(event, "Cache-Control", "private, no-store");
}

export function resolveReadSyncPrincipal(
  event: H3Event,
  config: ReadSyncConfig,
): ReadSyncPrincipal | null {
  return verifyReadSyncSessionToken(getCookie(event, READ_SYNC_COOKIE_NAME), config);
}

export function requireReadSyncPrincipal(
  event: H3Event,
  config: ReadSyncConfig,
): ReadSyncPrincipal {
  if (!config.configured) {
    throw createError({
      statusCode: 503,
      statusMessage: "Read-state sync is not configured.",
    });
  }
  const principal = resolveReadSyncPrincipal(event, config);
  if (!principal) {
    throw createError({
      statusCode: 401,
      statusMessage: "Read-state sync authentication is required.",
    });
  }
  return principal;
}
