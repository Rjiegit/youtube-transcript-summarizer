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

const snapshot = {
  loadedFrom,
  NOTION_API_KEY: Boolean(process.env.NOTION_API_KEY || process.env.NUXT_NOTION_API_KEY),
  NOTION_DATABASE_ID: Boolean(process.env.NOTION_DATABASE_ID || process.env.NUXT_NOTION_DATABASE_ID),
  NOTION_URL: Boolean(process.env.NOTION_URL || process.env.NUXT_NOTION_URL),
  SHOWCASE_CACHE_TTL_SECONDS:
    process.env.SHOWCASE_CACHE_TTL_SECONDS ||
    process.env.NUXT_SHOWCASE_CACHE_TTL_SECONDS ||
    "3600",
};

console.log(JSON.stringify(snapshot, null, 2));
