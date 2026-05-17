import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getShowcaseRuntimeSnapshot,
  resolveShowcaseConfig,
} from "../server/utils/config";

const ORIGINAL_ENV = { ...process.env };

describe("showcase env resolution", () => {
  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("resolves from direct NOTION_* process env", () => {
    process.env.NOTION_API_KEY = "api-key";
    process.env.NOTION_DATABASE_ID = "database-id";

    const resolved = resolveShowcaseConfig({ env: process.env });

    expect(resolved.notionApiKey).toBe("api-key");
    expect(resolved.notionDatabaseId).toBe("database-id");
    expect(resolved.cacheTtlSeconds).toBe(3600);
    expect(resolved.completedStatusValue).toBe("Completed");
  });

  it("prefers runtimeConfig over process env", () => {
    process.env.NOTION_API_KEY = "env-api-key";
    process.env.NOTION_DATABASE_ID = "env-database-id";
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "1200";

    const resolved = resolveShowcaseConfig({
      runtimeConfig: {
        notionApiKey: "runtime-api-key",
        notionDatabaseId: "runtime-database-id",
        showcaseCacheTtlSeconds: 900,
      },
      env: process.env,
    });

    expect(resolved.notionApiKey).toBe("runtime-api-key");
    expect(resolved.notionDatabaseId).toBe("runtime-database-id");
    expect(resolved.cacheTtlSeconds).toBe(900);
  });

  it("falls back to NUXT_* env names", () => {
    delete process.env.NOTION_API_KEY;
    delete process.env.NOTION_DATABASE_ID;
    process.env.NUXT_NOTION_API_KEY = "nuxt-api-key";
    process.env.NUXT_NOTION_DATABASE_ID = "nuxt-database-id";
    process.env.NUXT_SHOWCASE_CACHE_TTL_SECONDS = "600";
    process.env.NUXT_NOTION_STATUS_PROPERTY = "狀態";
    process.env.NUXT_NOTION_COMPLETED_STATUS = "已完成";

    const resolved = resolveShowcaseConfig({ env: process.env });

    expect(resolved.notionApiKey).toBe("nuxt-api-key");
    expect(resolved.notionDatabaseId).toBe("nuxt-database-id");
    expect(resolved.cacheTtlSeconds).toBe(600);
    expect(resolved.statusPropertyName).toBe("狀態");
    expect(resolved.completedStatusValue).toBe("已完成");
  });

  it("treats empty values as missing and falls back", () => {
    process.env.NOTION_API_KEY = "  ";
    process.env.NOTION_DATABASE_ID = "";
    process.env.NUXT_NOTION_API_KEY = "nuxt-api-key";
    process.env.NUXT_NOTION_DATABASE_ID = "nuxt-database-id";

    const resolved = resolveShowcaseConfig({
      runtimeConfig: {
        notionApiKey: " ",
        notionDatabaseId: "",
      },
      env: process.env,
    });

    expect(resolved.notionApiKey).toBe("nuxt-api-key");
    expect(resolved.notionDatabaseId).toBe("nuxt-database-id");
  });

  it("falls back to the default TTL when the configured value is invalid", () => {
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "not-a-number";

    const resolved = resolveShowcaseConfig({ env: process.env });

    expect(resolved.cacheTtlSeconds).toBe(3600);
  });

  it("builds a diagnostic snapshot from the same config sources", () => {
    process.env.NOTION_API_KEY = "api-key";
    process.env.NUXT_NOTION_DATABASE_ID = "nuxt-database-id";

    const snapshot = getShowcaseRuntimeSnapshot({
      notionApiKey: "",
      notionDatabaseId: "runtime-database-id",
      showcaseCacheTtlSeconds: 600,
    }, process.env);

    expect(snapshot.runtimeConfig).toEqual({
      notionApiKey: false,
      notionDatabaseId: true,
      statusPropertyName: false,
      completedStatusValue: false,
      showcaseCacheTtlSeconds: 600,
    });
    expect(snapshot.processEnv.NOTION_API_KEY).toBe(true);
    expect(snapshot.processEnv.NUXT_NOTION_DATABASE_ID).toBe(true);
  });

  it("uses SHOWCASE_CACHE_TTL_SECONDS for API route rules without caching the home page", async () => {
    process.env.SHOWCASE_CACHE_TTL_SECONDS = "900";
    process.env.NODE_ENV = "production";

    const defineNuxtConfig = vi.fn((config) => config);
    vi.stubGlobal("defineNuxtConfig", defineNuxtConfig);

    const module = await import("../nuxt.config.ts?t=" + Date.now());
    const config = module.default;

    expect(config.runtimeConfig.showcaseCacheTtlSeconds).toBe(900);
    expect(config.routeRules["/"]).toBeUndefined();
    expect(config.routeRules["/api/showcase/results"].swr).toBe(900);
    expect(config.routeRules["/api/showcase/results"].headers["cache-control"]).toBe(
      "public, s-maxage=900, stale-while-revalidate=900",
    );
  });
});
