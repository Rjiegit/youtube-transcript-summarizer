import { defineEventHandler } from "h3";

import { getShowcaseRuntimeSnapshot, resolveShowcaseConfig } from "./results.get";

export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event);
  const resolved = resolveShowcaseConfig(config);

  return {
    ok: Boolean(
      resolved.notionApiKey && resolved.notionDatabaseId && resolved.notionUrl,
    ),
    resolved: {
      notionApiKey: Boolean(resolved.notionApiKey),
      notionDatabaseId: Boolean(resolved.notionDatabaseId),
      notionUrl: Boolean(resolved.notionUrl),
      cacheTtlSeconds: resolved.cacheTtlSeconds,
    },
    diagnostic: getShowcaseRuntimeSnapshot(config),
  };
});
