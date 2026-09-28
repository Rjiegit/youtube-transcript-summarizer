import fs from "node:fs";
import path from "node:path";

function loadDotEnv(filePath) {
  if (!fs.existsSync(filePath)) {
    return null;
  }

  const content = fs.readFileSync(filePath, "utf8");
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    const separatorIndex = line.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }
    const key = line.slice(0, separatorIndex).trim();
    const value = line.slice(separatorIndex + 1);
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
  return filePath;
}

const localEnv = path.join(process.cwd(), ".env");
const loadedFrom = loadDotEnv(localEnv);
const firstNonEmptyEnvValue = (...keys) => {
  for (const key of keys) {
    const value = process.env[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
};

const snapshot = {
  loadedFrom,
  resolved: {
    notionApiKey: Boolean(firstNonEmptyEnvValue("NOTION_API_KEY", "NUXT_NOTION_API_KEY")),
    notionDatabaseId: Boolean(firstNonEmptyEnvValue("NOTION_DATABASE_ID", "NUXT_NOTION_DATABASE_ID")),
    statusPropertyName: Boolean(firstNonEmptyEnvValue("NOTION_STATUS_PROPERTY", "NUXT_NOTION_STATUS_PROPERTY")),
    completedStatusValue: firstNonEmptyEnvValue("NOTION_COMPLETED_STATUS", "NUXT_NOTION_COMPLETED_STATUS") || "Completed",
    cacheTtlSeconds: firstNonEmptyEnvValue("SHOWCASE_CACHE_TTL_SECONDS", "NUXT_SHOWCASE_CACHE_TTL_SECONDS") || "3600",
    readStateSync: {
      enabled: ["1", "true", "yes", "on"].includes(
        firstNonEmptyEnvValue("READ_STATE_SYNC_ENABLED").toLowerCase(),
      ),
      upstashUrl: Boolean(firstNonEmptyEnvValue("UPSTASH_REDIS_REST_URL")),
      upstashToken: Boolean(firstNonEmptyEnvValue("UPSTASH_REDIS_REST_TOKEN")),
      accessToken: Boolean(firstNonEmptyEnvValue("READ_STATE_SYNC_ACCESS_TOKEN")),
      sessionSecret: Boolean(firstNonEmptyEnvValue("READ_STATE_SYNC_SESSION_SECRET")),
      spaceId: firstNonEmptyEnvValue("READ_STATE_SYNC_SPACE_ID") || "personal",
      ttlSeconds: firstNonEmptyEnvValue("READ_STATE_SYNC_TTL_SECONDS") || "2592000",
    },
  },
  processEnv: {
    NOTION_API_KEY: Boolean(firstNonEmptyEnvValue("NOTION_API_KEY")),
    NOTION_DATABASE_ID: Boolean(firstNonEmptyEnvValue("NOTION_DATABASE_ID")),
    NOTION_STATUS_PROPERTY: Boolean(firstNonEmptyEnvValue("NOTION_STATUS_PROPERTY")),
    NOTION_COMPLETED_STATUS: Boolean(firstNonEmptyEnvValue("NOTION_COMPLETED_STATUS")),
    SHOWCASE_CACHE_TTL_SECONDS: Boolean(firstNonEmptyEnvValue("SHOWCASE_CACHE_TTL_SECONDS")),
    NUXT_NOTION_API_KEY: Boolean(firstNonEmptyEnvValue("NUXT_NOTION_API_KEY")),
    NUXT_NOTION_DATABASE_ID: Boolean(firstNonEmptyEnvValue("NUXT_NOTION_DATABASE_ID")),
    NUXT_NOTION_STATUS_PROPERTY: Boolean(firstNonEmptyEnvValue("NUXT_NOTION_STATUS_PROPERTY")),
    NUXT_NOTION_COMPLETED_STATUS: Boolean(firstNonEmptyEnvValue("NUXT_NOTION_COMPLETED_STATUS")),
    NUXT_SHOWCASE_CACHE_TTL_SECONDS: Boolean(firstNonEmptyEnvValue("NUXT_SHOWCASE_CACHE_TTL_SECONDS")),
    READ_STATE_SYNC_ENABLED: Boolean(firstNonEmptyEnvValue("READ_STATE_SYNC_ENABLED")),
    UPSTASH_REDIS_REST_URL: Boolean(firstNonEmptyEnvValue("UPSTASH_REDIS_REST_URL")),
    UPSTASH_REDIS_REST_TOKEN: Boolean(firstNonEmptyEnvValue("UPSTASH_REDIS_REST_TOKEN")),
    READ_STATE_SYNC_ACCESS_TOKEN: Boolean(firstNonEmptyEnvValue("READ_STATE_SYNC_ACCESS_TOKEN")),
    READ_STATE_SYNC_SESSION_SECRET: Boolean(firstNonEmptyEnvValue("READ_STATE_SYNC_SESSION_SECRET")),
    READ_STATE_SYNC_SPACE_ID: Boolean(firstNonEmptyEnvValue("READ_STATE_SYNC_SPACE_ID")),
    READ_STATE_SYNC_TTL_SECONDS: Boolean(firstNonEmptyEnvValue("READ_STATE_SYNC_TTL_SECONDS")),
  },
};

console.log(JSON.stringify(snapshot, null, 2));
