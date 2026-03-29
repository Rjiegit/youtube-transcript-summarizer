const CACHE_TTL_SECONDS = 3600;
const CACHE_CONTROL_VALUE = `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate=${CACHE_TTL_SECONDS}`;

export default defineNuxtConfig({
  devtools: { enabled: false },
  css: ["./assets/css/main.css"],
  runtimeConfig: {
    notionApiKey: process.env.NOTION_API_KEY || "",
    notionDatabaseId: process.env.NOTION_DATABASE_ID || "",
    notionUrl: process.env.NOTION_URL || "",
    showcaseCacheTtlSeconds: Number(process.env.SHOWCASE_CACHE_TTL_SECONDS || CACHE_TTL_SECONDS),
  },
  routeRules: {
    "/": {
      swr: CACHE_TTL_SECONDS,
      headers: {
        "cache-control": CACHE_CONTROL_VALUE,
      },
    },
    "/api/showcase/results": {
      swr: CACHE_TTL_SECONDS,
      headers: {
        "cache-control": CACHE_CONTROL_VALUE,
      },
    },
  },
});
