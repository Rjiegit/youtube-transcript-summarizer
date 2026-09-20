import {
  createError,
  defineEventHandler,
  readBody,
  setCookie,
} from "h3";

import {
  createReadSyncSessionToken,
  isReadSyncAccessTokenValid,
  READ_SYNC_COOKIE_NAME,
  READ_SYNC_SESSION_MAX_AGE_SECONDS,
} from "../../utils/read-sync-auth";
import {
  getRequestReadSyncConfig,
  setPrivateNoStore,
} from "../../utils/read-sync-server";

export default defineEventHandler(async (event) => {
  setPrivateNoStore(event);
  const config = getRequestReadSyncConfig(event);
  if (!config.configured) {
    throw createError({ statusCode: 503, statusMessage: "Read-state sync is not configured." });
  }

  const body = await readBody<{ accessToken?: unknown }>(event);
  if (!isReadSyncAccessTokenValid(body?.accessToken, config.accessToken)) {
    throw createError({ statusCode: 401, statusMessage: "Invalid read-state sync access token." });
  }

  setCookie(event, READ_SYNC_COOKIE_NAME, createReadSyncSessionToken(config), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: READ_SYNC_SESSION_MAX_AGE_SECONDS,
  });

  return { available: true, authenticated: true };
});
