import { describe, expect, it } from "vitest";

import { resolveReadSyncConfig } from "../server/utils/read-sync-config";

describe("read sync config", () => {
  it("stays disabled by default", () => {
    expect(resolveReadSyncConfig({ env: {} })).toMatchObject({
      enabled: false,
      configured: false,
      spaceId: "personal",
    });
  });

  it("requires every secret before reporting the feature as configured", () => {
    const env = {
      READ_STATE_SYNC_ENABLED: "true",
      UPSTASH_REDIS_REST_URL: "https://example.upstash.io",
      UPSTASH_REDIS_REST_TOKEN: "redis-token",
      READ_STATE_SYNC_ACCESS_TOKEN: "personal-code",
      READ_STATE_SYNC_SESSION_SECRET: "session-secret-with-enough-entropy",
      READ_STATE_SYNC_SPACE_ID: "jie",
    };

    expect(resolveReadSyncConfig({ env })).toMatchObject({
      enabled: true,
      configured: true,
      spaceId: "jie",
    });
  });

  it("does not expose a partially configured integration as available", () => {
    expect(resolveReadSyncConfig({
      env: {
        READ_STATE_SYNC_ENABLED: "true",
        UPSTASH_REDIS_REST_URL: "https://example.upstash.io",
      },
    }).configured).toBe(false);
  });
});
