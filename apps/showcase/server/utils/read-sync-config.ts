export interface ReadSyncConfig {
  enabled: boolean;
  configured: boolean;
  upstashUrl: string;
  upstashToken: string;
  accessToken: string;
  sessionSecret: string;
  spaceId: string;
}

interface ReadSyncConfigSource {
  runtimeConfig?: Record<string, unknown>;
  env?: Record<string, string | undefined>;
}

function readString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function readEnv(env: Record<string, string | undefined>, name: string): string {
  return readString(env[name]);
}

function parseEnabled(value: unknown): boolean {
  if (typeof value === "boolean") {
    return value;
  }
  return ["1", "true", "yes", "on"].includes(readString(value).toLowerCase());
}

export function resolveReadSyncConfig(source: ReadSyncConfigSource = {}): ReadSyncConfig {
  const runtimeConfig = source.runtimeConfig ?? {};
  const env = source.env ?? process.env;
  const enabled = parseEnabled(runtimeConfig.readStateSyncEnabled) ||
    parseEnabled(env.READ_STATE_SYNC_ENABLED);
  const upstashUrl = readString(runtimeConfig.upstashRedisRestUrl) ||
    readEnv(env, "UPSTASH_REDIS_REST_URL");
  const upstashToken = readString(runtimeConfig.upstashRedisRestToken) ||
    readEnv(env, "UPSTASH_REDIS_REST_TOKEN");
  const accessToken = readString(runtimeConfig.readStateSyncAccessToken) ||
    readEnv(env, "READ_STATE_SYNC_ACCESS_TOKEN");
  const sessionSecret = readString(runtimeConfig.readStateSyncSessionSecret) ||
    readEnv(env, "READ_STATE_SYNC_SESSION_SECRET");
  const spaceId = readString(runtimeConfig.readStateSyncSpaceId) ||
    readEnv(env, "READ_STATE_SYNC_SPACE_ID") ||
    "personal";

  return {
    enabled,
    configured: Boolean(enabled && upstashUrl && upstashToken && accessToken && sessionSecret && spaceId),
    upstashUrl,
    upstashToken,
    accessToken,
    sessionSecret,
    spaceId,
  };
}
