import type {
  ReadStateMutation,
  SyncedReadEntry,
  SyncedReadMap,
} from "../../types/read-sync";

interface UpstashConfig {
  url: string;
  token: string;
}

interface UpstashResponse {
  result?: unknown;
  error?: string;
}

const APPLY_MUTATIONS_SCRIPT = `
local key = KEYS[1]
local mutations = cjson.decode(ARGV[1])
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
      updatedAt = mutation.updatedAt
    }))
  end
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
): Promise<SyncedReadMap> {
  return normalizeHashResult(await executeCommand(config, ["HGETALL", redisKey(spaceId)]));
}

export async function applyReadStateMutations(
  config: UpstashConfig,
  spaceId: string,
  mutations: ReadStateMutation[],
): Promise<SyncedReadMap> {
  if (mutations.length === 0) {
    return getReadStateSnapshot(config, spaceId);
  }
  const result = await executeCommand(config, [
    "EVAL",
    APPLY_MUTATIONS_SCRIPT,
    "1",
    redisKey(spaceId),
    JSON.stringify(mutations),
  ]);
  return normalizeHashResult(result);
}
