import {
  getShowcaseRouteRules,
  resolveShowcaseConfig,
} from "./server/utils/config";

const showcaseConfig = resolveShowcaseConfig({ env: process.env });
const CACHE_TTL_SECONDS = showcaseConfig.cacheTtlSeconds;
const isProduction = process.env.NODE_ENV === "production";
const buildDate = firstNonEmptyEnvValue("SHOWCASE_BUILD_DATE", "NUXT_SHOWCASE_BUILD_DATE") || formatTaipeiBuildDate();
const commitSha = firstNonEmptyEnvValue(
  "VERCEL_GIT_COMMIT_SHA",
  "SHOWCASE_COMMIT_SHA",
  "NUXT_SHOWCASE_COMMIT_SHA",
  "GITHUB_SHA",
  "COMMIT_SHA",
);

function firstNonEmptyEnvValue(...names: string[]): string {
  for (const name of names) {
    const value = process.env[name]?.trim();
    if (value) {
      return value;
    }
  }

  return "";
}

function formatTaipeiBuildDate(date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date).replace(/-/g, ".");
}

export default defineNuxtConfig({
  devtools: { enabled: false },
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    notionApiKey: showcaseConfig.notionApiKey,
    notionDatabaseId: showcaseConfig.notionDatabaseId,
    statusPropertyName: showcaseConfig.statusPropertyName,
    completedStatusValue: showcaseConfig.completedStatusValue,
    showcaseCacheTtlSeconds: CACHE_TTL_SECONDS,
    public: {
      buildDate,
      commitSha,
    },
  },
  routeRules: getShowcaseRouteRules(CACHE_TTL_SECONDS, isProduction),
});
