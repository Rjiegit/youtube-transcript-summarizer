import {
  getShowcaseRouteRules,
  resolveShowcaseConfig,
} from "./server/utils/config";

const showcaseConfig = resolveShowcaseConfig({ env: process.env });
const CACHE_TTL_SECONDS = showcaseConfig.cacheTtlSeconds;
const isProduction = process.env.NODE_ENV === "production";

export default defineNuxtConfig({
  devtools: { enabled: false },
  css: ["./assets/css/main.css"],
  runtimeConfig: {
    notionApiKey: showcaseConfig.notionApiKey,
    notionDatabaseId: showcaseConfig.notionDatabaseId,
    statusPropertyName: showcaseConfig.statusPropertyName,
    completedStatusValue: showcaseConfig.completedStatusValue,
    showcaseCacheTtlSeconds: CACHE_TTL_SECONDS,
  },
  routeRules: getShowcaseRouteRules(CACHE_TTL_SECONDS, isProduction),
});
