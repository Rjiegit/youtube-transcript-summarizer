import { createError, defineEventHandler, setHeader } from "h3";

import { logShowcaseQueryFailure } from "../../../utils/showcase-errors";
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
    console.error("[showcase] configuration unavailable", {
      route: "detail",
      notionApiKey: Boolean(notionApiKey),
      notionDatabaseId: Boolean(notionDatabaseId),
    });
    setHeader(event, "Cache-Control", "no-store");
    throw createError({
      statusCode: 500,
      statusMessage: "Showcase service is unavailable.",
    });
  }

  if (!pageId) {
    setHeader(event, "Cache-Control", "no-store");
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
      }).catch((error: unknown) => {
        logShowcaseQueryFailure("detail", error);
        throw error;
      }),
    );
  } catch {
    const fallback = cache.peek();
    if (fallback) {
      return fallback;
    }

    setHeader(event, "Cache-Control", "no-store");
    throw createError({
      statusCode: 502,
      statusMessage: "Failed to load showcase detail.",
    });
  }
});
