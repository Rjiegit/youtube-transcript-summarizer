import {
  getShowcaseRouteRules,
  resolveShowcaseConfig,
} from "./server/utils/config";
import { resolveSiteUrl } from "./utils/site-url";
import { resolveReadSyncConfig } from "./server/utils/read-sync-config";
import { resolveAccountFeatures } from "./server/utils/account-features";

const showcaseConfig = resolveShowcaseConfig({ env: process.env });
const readSyncConfig = resolveReadSyncConfig({ env: process.env });
const accountFeatures = resolveAccountFeatures(process.env);
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
    accountAuthEnabled: accountFeatures.authEnabled,
    accountSupabaseUrl: process.env.SHOWCASE_SUPABASE_URL || '',
    accountSupabasePublishableKey: process.env.SHOWCASE_SUPABASE_PUBLISHABLE_KEY || '',
    accountAllowedUserIds: process.env.SHOWCASE_ALLOWED_USER_IDS || '',
    videoInboxAccessToken: process.env.VIDEO_INBOX_ACCESS_TOKEN || '',
    videoInboxOrigin: process.env.VIDEO_INBOX_ORIGIN || '',
    videoInboxSupabaseUrl: process.env.VIDEO_INBOX_SUPABASE_URL || '',
    videoInboxPublishableKey: process.env.VIDEO_INBOX_PUBLISHABLE_KEY || '',
    videoInboxSubmitToken: process.env.VIDEO_INBOX_SUBMIT_TOKEN || '',
    notionApiKey: showcaseConfig.notionApiKey,
    notionDatabaseId: showcaseConfig.notionDatabaseId,
    statusPropertyName: showcaseConfig.statusPropertyName,
    completedStatusValue: showcaseConfig.completedStatusValue,
    showcaseCacheTtlSeconds: CACHE_TTL_SECONDS,
    readStateSyncEnabled: readSyncConfig.enabled,
    upstashRedisRestUrl: readSyncConfig.upstashUrl,
    upstashRedisRestToken: readSyncConfig.upstashToken,
    readStateSyncAccessToken: readSyncConfig.accessToken,
    readStateSyncSessionSecret: readSyncConfig.sessionSecret,
    readStateSyncSpaceId: readSyncConfig.spaceId,
    readStateSyncTtlSeconds: readSyncConfig.ttlSeconds,
    public: {
      accountAuthEnabled: accountFeatures.authEnabled,
      accountSupabaseUrl: accountFeatures.authEnabled ? process.env.SHOWCASE_SUPABASE_URL || '' : '',
      accountSupabasePublishableKey: accountFeatures.authEnabled ? process.env.SHOWCASE_SUPABASE_PUBLISHABLE_KEY || '' : '',
      siteUrl: resolveSiteUrl(process.env.NUXT_PUBLIC_SITE_URL),
      buildDate,
      commitSha,
    },
  },
  routeRules: getShowcaseRouteRules(CACHE_TTL_SECONDS, isProduction),
});
