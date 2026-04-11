const CACHE_TTL_SECONDS = Number(process.env.SHOWCASE_CACHE_TTL_SECONDS || 3600);
const CACHE_CONTROL_VALUE = `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate=${CACHE_TTL_SECONDS}`;
const isProduction = process.env.NODE_ENV === "production";

export default defineNuxtConfig({
  devtools: { enabled: false },
  css: ["./assets/css/main.css"],
  runtimeConfig: {
    notionApiKey: process.env.NOTION_API_KEY || "",
    notionDatabaseId: process.env.NOTION_DATABASE_ID || "",
    statusPropertyName: process.env.NOTION_STATUS_PROPERTY || "",
    completedStatusValue: process.env.NOTION_COMPLETED_STATUS || "Completed",
    showcaseCacheTtlSeconds: Number(process.env.SHOWCASE_CACHE_TTL_SECONDS || CACHE_TTL_SECONDS),
  },
  routeRules: isProduction
    ? {
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
      }
    : {},
});
