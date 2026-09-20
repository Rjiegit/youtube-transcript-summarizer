import { describe, expect, it } from "vitest";

import {
  createReadSyncSessionToken,
  isReadSyncAccessTokenValid,
  verifyReadSyncSessionToken,
} from "../server/utils/read-sync-auth";

const config = {
  accessToken: "a-long-personal-access-code",
  sessionSecret: "a-separate-long-session-signing-secret",
  spaceId: "personal",
};

describe("read sync auth", () => {
  it("validates the configured personal access token", () => {
    expect(isReadSyncAccessTokenValid("a-long-personal-access-code", config.accessToken)).toBe(true);
    expect(isReadSyncAccessTokenValid("wrong", config.accessToken)).toBe(false);
  });

  it("creates and verifies an expiring signed session", () => {
    const now = new Date("2026-09-20T00:00:00.000Z");
    const token = createReadSyncSessionToken(config, now);

    expect(verifyReadSyncSessionToken(token, config, now)).toEqual({
      syncSpaceId: "personal",
      authType: "personal_token",
    });
  });

  it("rejects tampered and expired sessions", () => {
    const now = new Date("2026-09-20T00:00:00.000Z");
    const token = createReadSyncSessionToken(config, now, 60);

    expect(verifyReadSyncSessionToken(`${token}tampered`, config, now)).toBeNull();
    expect(verifyReadSyncSessionToken(token, config, new Date("2026-09-20T00:02:00.000Z"))).toBeNull();
  });
});
