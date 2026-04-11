import { createError, defineEventHandler, setHeader } from "h3";

import { fetchShowcaseDetail } from "../../../utils/notion";
import { createSWRCache } from "../../../utils/swr-cache";
import type { ShowcaseDetailResult } from "../../../types/showcase";
import {
  DEFAULT_CACHE_TTL_SECONDS,
  getShowcaseCacheControlValue,
  resolveShowcaseConfig,
} from "../../../utils/config";
let detailCaches = new Map<string, ReturnType<typeof createSWRCache<ShowcaseDetailResult>>>();
let detailCacheTtlMs = DEFAULT_CACHE_TTL_SECONDS * 1000;

function getDetailCache(pageId: string, cacheTtlSeconds: number) {
  const ttlMs = cacheTtlSeconds * 1000;
  if (ttlMs !== detailCacheTtlMs) {
    detailCaches = new Map();
    detailCacheTtlMs = ttlMs;
  }

  const existing = detailCaches.get(pageId);
  if (existing) {
    return existing;
  }

  const nextCache = createSWRCache<ShowcaseDetailResult>({ ttlMs });
  detailCaches.set(pageId, nextCache);
  return nextCache;
}

export default defineEventHandler(async (event) => {
  const runtimeConfig = useRuntimeConfig(event);
  const { notionApiKey, notionDatabaseId, cacheTtlSeconds } = resolveShowcaseConfig({ runtimeConfig });
  const pageId = String(event.context.params?.id || "").trim();
  const cacheControlValue = getShowcaseCacheControlValue(cacheTtlSeconds);

  if (!notionApiKey || !notionDatabaseId) {
    throw createError({
      statusCode: 500,
      statusMessage: "Missing Notion showcase configuration.",
    });
  }

  if (!pageId) {
    throw createError({
      statusCode: 400,
      statusMessage: "Missing showcase result id.",
    });
  }

  setHeader(event, "Cache-Control", cacheControlValue);
  const cache = getDetailCache(pageId, cacheTtlSeconds);

  try {
    return await cache.get(() =>
      fetchShowcaseDetail({
        apiKey: notionApiKey,
        databaseId: notionDatabaseId,
        pageId,
      }),
    );
  } catch (error) {
    const fallback = cache.peek();
    if (fallback) {
      return fallback;
    }

    throw createError({
      statusCode: 502,
      statusMessage: error instanceof Error ? error.message : "Failed to load showcase detail.",
    });
  }
});
