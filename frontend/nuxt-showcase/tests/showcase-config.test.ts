import { afterEach, describe, expect, it } from "vitest";

import { resolveShowcaseConfig } from "../server/api/showcase/results.get";

const ORIGINAL_ENV = { ...process.env };

describe("showcase env resolution", () => {
  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("resolves from direct NOTION_* process env", () => {
    process.env.NOTION_API_KEY = "api-key";
    process.env.NOTION_DATABASE_ID = "database-id";

    const resolved = resolveShowcaseConfig({});

    expect(resolved.notionApiKey).toBe("api-key");
    expect(resolved.notionDatabaseId).toBe("database-id");
    expect(resolved.cacheTtlSeconds).toBe(3600);
    expect(resolved.completedStatusValue).toBe("Completed");
  });

  it("falls back to NUXT_* env names", () => {
    delete process.env.NOTION_API_KEY;
    delete process.env.NOTION_DATABASE_ID;
    process.env.NUXT_NOTION_API_KEY = "nuxt-api-key";
    process.env.NUXT_NOTION_DATABASE_ID = "nuxt-database-id";
    process.env.NUXT_SHOWCASE_CACHE_TTL_SECONDS = "600";
    process.env.NUXT_NOTION_STATUS_PROPERTY = "狀態";
    process.env.NUXT_NOTION_COMPLETED_STATUS = "已完成";

    const resolved = resolveShowcaseConfig({});

    expect(resolved.notionApiKey).toBe("nuxt-api-key");
    expect(resolved.notionDatabaseId).toBe("nuxt-database-id");
    expect(resolved.cacheTtlSeconds).toBe(600);
    expect(resolved.statusPropertyName).toBe("狀態");
    expect(resolved.completedStatusValue).toBe("已完成");
  });
});
