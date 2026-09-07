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

const workspaceRoot = path.resolve(process.cwd(), "..", "..");
const localEnv = path.join(process.cwd(), ".env");
const rootEnv = path.join(workspaceRoot, ".env");
const loadedFrom = loadDotEnv(localEnv) ?? loadDotEnv(rootEnv);
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
  },
};

console.log(JSON.stringify(snapshot, null, 2));
