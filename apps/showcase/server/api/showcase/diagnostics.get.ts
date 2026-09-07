import { defineEventHandler } from "h3";

import { getShowcaseRuntimeSnapshot, resolveShowcaseConfig } from "../../utils/config";

export default defineEventHandler((event) => {
  const runtimeConfig = useRuntimeConfig(event);
  const resolved = resolveShowcaseConfig({ runtimeConfig });

  return {
    ok: Boolean(
      resolved.notionApiKey && resolved.notionDatabaseId,
    ),
    resolved: {
      notionApiKey: Boolean(resolved.notionApiKey),
      notionDatabaseId: Boolean(resolved.notionDatabaseId),
      cacheTtlSeconds: resolved.cacheTtlSeconds,
    },
    diagnostic: getShowcaseRuntimeSnapshot(runtimeConfig),
  };
});
