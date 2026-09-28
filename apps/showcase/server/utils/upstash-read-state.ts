import type {
  ReadStateMutation,
  SyncedReadEntry,
  SyncedReadMap,
} from "../../types/read-sync";
import { DEFAULT_READ_STATE_SYNC_TTL_SECONDS } from "./read-sync-config";

interface UpstashConfig {
  url: string;
  token: string;
}

interface UpstashResponse {
  result?: unknown;
  error?: string;
}

const MAX_SYNC_ENTRIES = 100;

const APPLY_MUTATIONS_SCRIPT = `
local key = KEYS[1]
local mutations = cjson.decode(ARGV[1])
local ttlSeconds = tonumber(ARGV[2])
local cutoff = ARGV[3]
local maxEntries = tonumber(ARGV[4])
local now = tonumber(redis.call("TIME")[1])
local existing = redis.call("HGETALL", key)
for index = 1, #existing, 2 do
  local ok, entry = pcall(cjson.decode, existing[index + 1])
  local expiresAt = ok and type(entry) == "table" and tonumber(entry.expiresAt) or nil
  local updatedAt = ok and type(entry) == "table" and entry.updatedAt or nil
  if (expiresAt and expiresAt <= now) or (not expiresAt and (type(updatedAt) ~= "string" or updatedAt < cutoff)) then
    redis.call("HDEL", key, existing[index])
  end
end
for _, mutation in ipairs(mutations) do
  local currentJson = redis.call("HGET", key, mutation.contentKey)
  local shouldWrite = not currentJson
  if currentJson then
    local ok, current = pcall(cjson.decode, currentJson)
    shouldWrite = not ok or type(current.updatedAt) ~= "string" or mutation.updatedAt > current.updatedAt
  end
  if shouldWrite then
    redis.call("HSET", key, mutation.contentKey, cjson.encode({
      status = mutation.status,
      updatedAt = mutation.updatedAt,
      expiresAt = now + ttlSeconds
    }))
  end
end
local remaining = redis.call("HGETALL", key)
local ordered = {}
for index = 1, #remaining, 2 do
  local ok, entry = pcall(cjson.decode, remaining[index + 1])
  local updatedAt = ok and type(entry) == "table" and type(entry.updatedAt) == "string" and entry.updatedAt or ""
  table.insert(ordered, { field = remaining[index], updatedAt = updatedAt })
end
table.sort(ordered, function(left, right)
  return left.updatedAt < right.updatedAt
end)
for index = 1, #ordered - maxEntries do
  redis.call("HDEL", key, ordered[index].field)
end
redis.call("EXPIRE", key, ttlSeconds)
return redis.call("HGETALL", key)
`;

const GET_SNAPSHOT_SCRIPT = `
local key = KEYS[1]
local ttlSeconds = tonumber(ARGV[1])
local cutoff = ARGV[2]
local maxEntries = tonumber(ARGV[3])
local now = tonumber(redis.call("TIME")[1])
local entries = redis.call("HGETALL", key)
for index = 1, #entries, 2 do
  local ok, entry = pcall(cjson.decode, entries[index + 1])
  local expiresAt = ok and type(entry) == "table" and tonumber(entry.expiresAt) or nil
  local updatedAt = ok and type(entry) == "table" and entry.updatedAt or nil
  if (expiresAt and expiresAt <= now) or (not expiresAt and (type(updatedAt) ~= "string" or updatedAt < cutoff)) then
    redis.call("HDEL", key, entries[index])
  end
end
local ordered = {}
for index = 1, #entries, 2 do
  local ok, entry = pcall(cjson.decode, entries[index + 1])
  local updatedAt = ok and type(entry) == "table" and type(entry.updatedAt) == "string" and entry.updatedAt or ""
  table.insert(ordered, { field = entries[index], updatedAt = updatedAt })
end
table.sort(ordered, function(left, right)
  return left.updatedAt < right.updatedAt
end)
for index = 1, #ordered - maxEntries do
  redis.call("HDEL", key, ordered[index].field)
end
if redis.call("HLEN", key) > 0 then
  redis.call("EXPIRE", key, ttlSeconds)
end
return redis.call("HGETALL", key)
`;

function redisKey(spaceId: string): string {
  return `showcase:read-state:${spaceId}`;
}

function normalizeEntry(value: unknown): SyncedReadEntry | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  const candidate = value as Partial<SyncedReadEntry>;
  if ((candidate.status !== "read" && candidate.status !== "unread") ||
      typeof candidate.updatedAt !== "string" || !Number.isFinite(Date.parse(candidate.updatedAt))) {
    return null;
  }
  return {
    status: candidate.status,
    updatedAt: candidate.updatedAt,
  };
}

function normalizeHashResult(value: unknown): SyncedReadMap {
  const pairs: Array<[string, unknown]> = [];
  if (Array.isArray(value)) {
    for (let index = 0; index + 1 < value.length; index += 2) {
      if (typeof value[index] === "string") {
        pairs.push([value[index], value[index + 1]]);
      }
    }
  } else if (value && typeof value === "object") {
    pairs.push(...Object.entries(value));
  }

  const entries: SyncedReadMap = {};
  for (const [contentKey, rawEntry] of pairs) {
    try {
      const parsed = typeof rawEntry === "string" ? JSON.parse(rawEntry) : rawEntry;
      const entry = normalizeEntry(parsed);
      if (contentKey.trim() && entry) {
        entries[contentKey] = entry;
      }
    } catch {
      // Ignore malformed legacy fields instead of failing the entire snapshot.
    }
  }
  return entries;
}

async function executeCommand(config: UpstashConfig, command: unknown[]): Promise<unknown> {
  const response = await fetch(config.url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(command),
  });
  if (!response.ok) {
    throw new Error(`Upstash request failed with status ${response.status}.`);
  }
  const payload = await response.json() as UpstashResponse;
  if (payload.error) {
    throw new Error(payload.error);
  }
  return payload.result;
}

export async function getReadStateSnapshot(
  config: UpstashConfig,
  spaceId: string,
  ttlSeconds = DEFAULT_READ_STATE_SYNC_TTL_SECONDS,
): Promise<SyncedReadMap> {
  return normalizeHashResult(await executeCommand(config, [
    "EVAL",
    GET_SNAPSHOT_SCRIPT,
    "1",
    redisKey(spaceId),
    String(ttlSeconds),
    new Date(Date.now() - ttlSeconds * 1000).toISOString(),
    String(MAX_SYNC_ENTRIES),
  ]));
}

export async function applyReadStateMutations(
  config: UpstashConfig,
  spaceId: string,
  mutations: ReadStateMutation[],
  ttlSeconds = DEFAULT_READ_STATE_SYNC_TTL_SECONDS,
): Promise<SyncedReadMap> {
  if (mutations.length === 0) {
    return getReadStateSnapshot(config, spaceId, ttlSeconds);
  }
  const result = await executeCommand(config, [
    "EVAL",
    APPLY_MUTATIONS_SCRIPT,
    "1",
    redisKey(spaceId),
    JSON.stringify(mutations),
    String(ttlSeconds),
    new Date(Date.now() - ttlSeconds * 1000).toISOString(),
    String(MAX_SYNC_ENTRIES),
  ]);
  return normalizeHashResult(result);
}
