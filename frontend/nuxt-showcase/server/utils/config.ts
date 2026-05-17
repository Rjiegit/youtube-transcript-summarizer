export const DEFAULT_CACHE_TTL_SECONDS = 3600;
export const DEFAULT_COMPLETED_STATUS_VALUE = "Completed";
export const SHOWCASE_RESULTS_ROUTE = "/api/showcase/results";

export interface ShowcaseConfig {
  notionApiKey: string;
  notionDatabaseId: string;
  statusPropertyName: string;
  completedStatusValue: string;
  cacheTtlSeconds: number;
}

export interface ShowcaseConfigDiagnostic {
  runtimeConfig: {
    notionApiKey: boolean;
    notionDatabaseId: boolean;
    statusPropertyName: boolean;
    completedStatusValue: boolean;
    showcaseCacheTtlSeconds: number | null;
  };
  processEnv: Record<string, boolean>;
}

interface ShowcaseConfigSource {
  runtimeConfig?: Record<string, unknown>;
  env?: Record<string, string | undefined>;
}

const SHOWCASE_ENV_KEYS = {
  notionApiKey: ["NOTION_API_KEY", "NUXT_NOTION_API_KEY"],
  notionDatabaseId: ["NOTION_DATABASE_ID", "NUXT_NOTION_DATABASE_ID"],
  statusPropertyName: ["NOTION_STATUS_PROPERTY", "NUXT_NOTION_STATUS_PROPERTY"],
  completedStatusValue: ["NOTION_COMPLETED_STATUS", "NUXT_NOTION_COMPLETED_STATUS"],
  cacheTtlSeconds: ["SHOWCASE_CACHE_TTL_SECONDS", "NUXT_SHOWCASE_CACHE_TTL_SECONDS"],
} as const;

function readRuntimeString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function readRuntimeNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value) && value > 0) {
    return value;
  }
  return null;
}

function firstNonEmptyEnvValue(env: Record<string, string | undefined>, keys: readonly string[]): string {
  for (const key of keys) {
    const value = env[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function parseCacheTtlSeconds(value: string | number | null | undefined): number {
  if (typeof value === "number" && Number.isFinite(value) && value > 0) {
    return value;
  }

  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value.trim());
    if (Number.isFinite(parsed) && parsed > 0) {
      return parsed;
    }
  }

  return DEFAULT_CACHE_TTL_SECONDS;
}

export function getShowcaseRuntimeSnapshot(
  runtimeConfig: Record<string, unknown> = {},
  env: Record<string, string | undefined> = process.env,
): ShowcaseConfigDiagnostic {
  return {
    runtimeConfig: {
      notionApiKey: readRuntimeString(runtimeConfig.notionApiKey).length > 0,
      notionDatabaseId: readRuntimeString(runtimeConfig.notionDatabaseId).length > 0,
      statusPropertyName: readRuntimeString(runtimeConfig.statusPropertyName).length > 0,
      completedStatusValue: readRuntimeString(runtimeConfig.completedStatusValue).length > 0,
      showcaseCacheTtlSeconds: readRuntimeNumber(runtimeConfig.showcaseCacheTtlSeconds),
    },
    processEnv: Object.fromEntries(
      Object.values(SHOWCASE_ENV_KEYS)
        .flat()
        .map((key) => [key, typeof env[key] === "string" && env[key]!.trim().length > 0]),
    ),
  };
}

export function resolveShowcaseConfig(source: ShowcaseConfigSource = {}): ShowcaseConfig {
  const runtimeConfig = source.runtimeConfig ?? {};
  const env = source.env ?? process.env;
  const runtimeCacheTtlSeconds = readRuntimeNumber(runtimeConfig.showcaseCacheTtlSeconds);
  const envCacheTtlRaw = firstNonEmptyEnvValue(env, SHOWCASE_ENV_KEYS.cacheTtlSeconds);

  return {
    notionApiKey: readRuntimeString(runtimeConfig.notionApiKey) ||
      firstNonEmptyEnvValue(env, SHOWCASE_ENV_KEYS.notionApiKey),
    notionDatabaseId: readRuntimeString(runtimeConfig.notionDatabaseId) ||
      firstNonEmptyEnvValue(env, SHOWCASE_ENV_KEYS.notionDatabaseId),
    statusPropertyName: readRuntimeString(runtimeConfig.statusPropertyName) ||
      firstNonEmptyEnvValue(env, SHOWCASE_ENV_KEYS.statusPropertyName),
    completedStatusValue: readRuntimeString(runtimeConfig.completedStatusValue) ||
      firstNonEmptyEnvValue(env, SHOWCASE_ENV_KEYS.completedStatusValue) ||
      DEFAULT_COMPLETED_STATUS_VALUE,
    cacheTtlSeconds: parseCacheTtlSeconds(runtimeCacheTtlSeconds ?? envCacheTtlRaw),
  };
}

export function getShowcaseCacheControlValue(cacheTtlSeconds: number): string {
  const ttl = parseCacheTtlSeconds(cacheTtlSeconds);
  return `public, s-maxage=${ttl}, stale-while-revalidate=${ttl}`;
}

export function getShowcaseRouteRules(cacheTtlSeconds: number, isProduction: boolean) {
  if (!isProduction) {
    return {};
  }

  const ttl = parseCacheTtlSeconds(cacheTtlSeconds);
  const headers = {
    "cache-control": getShowcaseCacheControlValue(ttl),
  };

  return {
    [SHOWCASE_RESULTS_ROUTE]: {
      swr: ttl,
      headers,
    },
  };
}
