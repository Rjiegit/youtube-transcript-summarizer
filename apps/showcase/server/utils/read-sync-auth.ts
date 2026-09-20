import { createHash, createHmac, timingSafeEqual } from "node:crypto";

export const READ_SYNC_COOKIE_NAME = "showcase-read-sync-session";
export const READ_SYNC_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30;

interface ReadSyncAuthConfig {
  accessToken: string;
  sessionSecret: string;
  spaceId: string;
}

export interface ReadSyncPrincipal {
  syncSpaceId: string;
  authType: "personal_token" | "account";
}

function digest(value: string): Buffer {
  return createHash("sha256").update(value).digest();
}

function sign(payload: string, secret: string): string {
  return createHmac("sha256", secret).update(payload).digest("base64url");
}

export function isReadSyncAccessTokenValid(candidate: unknown, expected: string): boolean {
  if (typeof candidate !== "string" || !candidate || !expected) {
    return false;
  }
  return timingSafeEqual(digest(candidate), digest(expected));
}

export function createReadSyncSessionToken(
  config: ReadSyncAuthConfig,
  now = new Date(),
  maxAgeSeconds = READ_SYNC_SESSION_MAX_AGE_SECONDS,
): string {
  const payload = Buffer.from(JSON.stringify({
    spaceId: config.spaceId,
    expiresAt: Math.floor(now.getTime() / 1000) + maxAgeSeconds,
  })).toString("base64url");

  return `${payload}.${sign(payload, config.sessionSecret)}`;
}

export function verifyReadSyncSessionToken(
  token: unknown,
  config: ReadSyncAuthConfig,
  now = new Date(),
): ReadSyncPrincipal | null {
  if (typeof token !== "string") {
    return null;
  }

  const [payload, signature, extra] = token.split(".");
  if (!payload || !signature || extra ||
      !timingSafeEqual(digest(signature), digest(sign(payload, config.sessionSecret)))) {
    return null;
  }

  try {
    const parsed = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as {
      spaceId?: unknown;
      expiresAt?: unknown;
    };
    if (parsed.spaceId !== config.spaceId || typeof parsed.expiresAt !== "number" ||
        parsed.expiresAt <= Math.floor(now.getTime() / 1000)) {
      return null;
    }
    return {
      syncSpaceId: config.spaceId,
      authType: "personal_token",
    };
  } catch {
    return null;
  }
}
