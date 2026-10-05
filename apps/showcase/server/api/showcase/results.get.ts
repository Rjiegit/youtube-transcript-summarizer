import { createError, defineEventHandler, getQuery, setHeader } from "h3";

import { logShowcaseQueryFailure } from "../../utils/showcase-errors";
import { fetchLatestCompletedResults } from "../../utils/notion";
import { createSWRCache } from "../../utils/swr-cache";
import type { ShowcaseApiResponse } from "../../../types/showcase";
import {
  DEFAULT_CACHE_TTL_SECONDS,
  getShowcaseCacheControlValue,
  resolveShowcaseConfig,
} from "../../utils/config";
let showcaseCache = createSWRCache<ShowcaseApiResponse>({
  ttlMs: DEFAULT_CACHE_TTL_SECONDS * 1000,
});
let showcaseCacheTtlMs = DEFAULT_CACHE_TTL_SECONDS * 1000;

function hasRefreshQuery(event: { node?: { req?: { url?: string } } }): boolean {
  const query = getQuery(event);
  if (query.refresh === "1") {
    return true;
  }

  const rawUrl = event.node?.req?.url;
  if (!rawUrl) {
    return false;
  }

  return new URL(rawUrl, "http://localhost").searchParams.get("refresh") === "1";
}

function getShowcaseCache(cacheTtlSeconds: number) {
  const ttlMs = cacheTtlSeconds * 1000;
  if (ttlMs !== showcaseCacheTtlMs) {
    showcaseCache = createSWRCache<ShowcaseApiResponse>({ ttlMs });
    showcaseCacheTtlMs = ttlMs;
  }
  return showcaseCache;
}

export default defineEventHandler(async (event) => {
  const runtimeConfig = useRuntimeConfig(event);
  const shouldForceRefresh = hasRefreshQuery(event);
  const {
    notionApiKey,
    notionDatabaseId,
    cacheTtlSeconds,
    statusPropertyName,
    completedStatusValue,
  } = resolveShowcaseConfig({ runtimeConfig });
  const cacheControlValue = getShowcaseCacheControlValue(cacheTtlSeconds);
  const cache = getShowcaseCache(cacheTtlSeconds);

  setHeader(event, "Cache-Control", shouldForceRefresh ? "no-store" : cacheControlValue);

  const missingEnvVars = [
    !notionApiKey ? "NOTION_API_KEY" : null,
    !notionDatabaseId ? "NOTION_DATABASE_ID" : null,
  ].filter(Boolean);

  if (missingEnvVars.length > 0) {
    console.error("[showcase] configuration unavailable", { route: "results", missingEnvVars });
    setHeader(event, "Cache-Control", "no-store");
    throw createError({
      statusCode: 500,
      statusMessage: "Showcase service is unavailable.",
    });
  }

  try {
    const fetchResults = () =>
      fetchLatestCompletedResults({
        apiKey: notionApiKey,
        databaseId: notionDatabaseId,
        cacheTtlSeconds,
        statusPropertyName,
        completedStatusValue,
      }).catch((error: unknown) => {
        logShowcaseQueryFailure("results", error);
        throw error;
      });

    return shouldForceRefresh ? await cache.refresh(fetchResults) : await cache.get(fetchResults);
  } catch {
    const fallback = cache.peek();
    if (fallback) {
      return fallback;
    }

    setHeader(event, "Cache-Control", "no-store");
    throw createError({
      statusCode: 502,
      statusMessage: "Failed to load showcase results.",
    });
  }
});
