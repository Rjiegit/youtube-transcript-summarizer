import { createError, defineEventHandler, setHeader } from "h3";

import { fetchLatestCompletedResults } from "../../utils/notion";
import { createSWRCache } from "../../utils/swr-cache";
import type { ShowcaseApiResponse } from "../../../types/showcase";

const DEFAULT_CACHE_TTL_SECONDS = 3600;
let showcaseCache = createSWRCache<ShowcaseApiResponse>({
  ttlMs: DEFAULT_CACHE_TTL_SECONDS * 1000,
});
let showcaseCacheTtlMs = DEFAULT_CACHE_TTL_SECONDS * 1000;

function getShowcaseCache(cacheTtlSeconds: number) {
  const ttlMs = cacheTtlSeconds * 1000;
  if (ttlMs !== showcaseCacheTtlMs) {
    showcaseCache = createSWRCache<ShowcaseApiResponse>({ ttlMs });
    showcaseCacheTtlMs = ttlMs;
  }
  return showcaseCache;
}

function firstNonEmptyValue(...values: Array<unknown>): string {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function hasNonEmptyValue(value: unknown): boolean {
  return typeof value === "string" && value.trim().length > 0;
}

export function getShowcaseRuntimeSnapshot(config: Record<string, unknown>) {
  return {
    runtimeConfig: {
      notionApiKey: hasNonEmptyValue(config.notionApiKey),
      notionDatabaseId: hasNonEmptyValue(config.notionDatabaseId),
      notionUrl: hasNonEmptyValue(config.notionUrl),
      showcaseCacheTtlSeconds: config.showcaseCacheTtlSeconds ?? null,
    },
    processEnv: {
      NOTION_API_KEY: hasNonEmptyValue(process.env.NOTION_API_KEY),
      NOTION_DATABASE_ID: hasNonEmptyValue(process.env.NOTION_DATABASE_ID),
      NOTION_URL: hasNonEmptyValue(process.env.NOTION_URL),
      NUXT_NOTION_API_KEY: hasNonEmptyValue(process.env.NUXT_NOTION_API_KEY),
      NUXT_NOTION_DATABASE_ID: hasNonEmptyValue(process.env.NUXT_NOTION_DATABASE_ID),
      NUXT_NOTION_URL: hasNonEmptyValue(process.env.NUXT_NOTION_URL),
      SHOWCASE_CACHE_TTL_SECONDS: hasNonEmptyValue(process.env.SHOWCASE_CACHE_TTL_SECONDS),
      NUXT_SHOWCASE_CACHE_TTL_SECONDS: hasNonEmptyValue(process.env.NUXT_SHOWCASE_CACHE_TTL_SECONDS),
    },
  };
}

export function resolveShowcaseConfig(config: Record<string, unknown>) {
  const notionApiKey = firstNonEmptyValue(
    config.notionApiKey,
    process.env.NOTION_API_KEY,
    process.env.NUXT_NOTION_API_KEY,
  );
  const notionDatabaseId = firstNonEmptyValue(
    config.notionDatabaseId,
    process.env.NOTION_DATABASE_ID,
    process.env.NUXT_NOTION_DATABASE_ID,
  );
  const notionUrl = firstNonEmptyValue(
    config.notionUrl,
    process.env.NOTION_URL,
    process.env.NUXT_NOTION_URL,
  );
  const cacheTtlSeconds = Number(
    firstNonEmptyValue(
      config.showcaseCacheTtlSeconds,
      process.env.SHOWCASE_CACHE_TTL_SECONDS,
      process.env.NUXT_SHOWCASE_CACHE_TTL_SECONDS,
    ) || DEFAULT_CACHE_TTL_SECONDS,
  );
  const statusPropertyName = firstNonEmptyValue(
    config.statusPropertyName,
    process.env.NOTION_STATUS_PROPERTY,
    process.env.NUXT_NOTION_STATUS_PROPERTY,
  );
  const completedStatusValue = firstNonEmptyValue(
    config.completedStatusValue,
    process.env.NOTION_COMPLETED_STATUS,
    process.env.NUXT_NOTION_COMPLETED_STATUS,
  ) || "Completed";

  return {
    notionApiKey,
    notionDatabaseId,
    notionUrl,
    cacheTtlSeconds,
    statusPropertyName,
    completedStatusValue,
    diagnostic: getShowcaseRuntimeSnapshot(config),
  };
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event);
  const {
    notionApiKey,
    notionDatabaseId,
    notionUrl,
    cacheTtlSeconds,
    statusPropertyName,
    completedStatusValue,
    diagnostic,
  } = resolveShowcaseConfig(config);
  const cacheControlValue = `public, s-maxage=${cacheTtlSeconds}, stale-while-revalidate=${cacheTtlSeconds}`;
  const cache = getShowcaseCache(cacheTtlSeconds);

  setHeader(event, "Cache-Control", cacheControlValue);

  const missingEnvVars = [
    !notionApiKey ? "NOTION_API_KEY" : null,
    !notionDatabaseId ? "NOTION_DATABASE_ID" : null,
    !notionUrl ? "NOTION_URL" : null,
  ].filter(Boolean);

  if (missingEnvVars.length > 0) {
    throw createError({
      statusCode: 500,
      statusMessage: `Missing Notion showcase configuration: ${missingEnvVars.join(", ")} | ${JSON.stringify(diagnostic)}`,
    });
  }

  try {
    return await cache.get(() =>
      fetchLatestCompletedResults({
        apiKey: notionApiKey,
        databaseId: notionDatabaseId,
        notionBaseUrl: notionUrl,
        cacheTtlSeconds,
        statusPropertyName,
        completedStatusValue,
      }),
    );
  } catch (error) {
    const fallback = cache.peek();
    if (fallback) {
      return fallback;
    }

    throw createError({
      statusCode: 502,
      statusMessage: error instanceof Error ? error.message : "Failed to load showcase results.",
    });
  }
});
