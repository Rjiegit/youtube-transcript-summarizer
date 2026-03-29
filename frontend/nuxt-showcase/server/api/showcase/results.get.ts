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

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event);
  const cacheTtlSeconds = Number(config.showcaseCacheTtlSeconds || DEFAULT_CACHE_TTL_SECONDS);
  const cacheControlValue = `public, s-maxage=${cacheTtlSeconds}, stale-while-revalidate=${cacheTtlSeconds}`;
  const cache = getShowcaseCache(cacheTtlSeconds);

  setHeader(event, "Cache-Control", cacheControlValue);

  if (!config.notionApiKey || !config.notionDatabaseId || !config.notionUrl) {
    throw createError({
      statusCode: 500,
      statusMessage: "Missing Notion showcase configuration.",
    });
  }

  try {
    return await cache.get(() =>
      fetchLatestCompletedResults({
        apiKey: config.notionApiKey,
        databaseId: config.notionDatabaseId,
        notionBaseUrl: config.notionUrl,
        cacheTtlSeconds,
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
