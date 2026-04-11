import { defineEventHandler } from "h3";

import {
  fetchDatabaseSchema,
  fetchLatestCompletedResults,
  resolveFieldMapping,
  resolveStatusConfig,
} from "../../utils/notion";
import { resolveShowcaseConfig } from "./results.get";

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event);
  const resolved = resolveShowcaseConfig(config);

  if (!resolved.notionApiKey || !resolved.notionDatabaseId) {
    return {
      ok: false,
      stage: "configuration",
      error: "Missing required Notion showcase configuration.",
      resolved: {
        notionApiKey: Boolean(resolved.notionApiKey),
        notionDatabaseId: Boolean(resolved.notionDatabaseId),
      },
    };
  }

  try {
    const schema = await fetchDatabaseSchema(
      resolved.notionApiKey,
      resolved.notionDatabaseId,
    );
    const statusConfig = resolveStatusConfig(
      schema,
      resolved.statusPropertyName,
      resolved.completedStatusValue,
    );
    const fieldMapping = resolveFieldMapping(schema);
    const response = await fetchLatestCompletedResults({
      apiKey: resolved.notionApiKey,
      databaseId: resolved.notionDatabaseId,
      cacheTtlSeconds: resolved.cacheTtlSeconds,
      statusPropertyName: resolved.statusPropertyName,
      completedStatusValue: resolved.completedStatusValue,
    });

    return {
      ok: true,
      stage: "notion-query",
      databaseTitle: (schema.title || []).map((item) => item.plain_text || item.text?.content || "").join(""),
      queryConfig: statusConfig,
      fieldMapping,
      itemCount: response.items.length,
      sampleTitle: response.items[0]?.title ?? null,
      generatedAt: response.generated_at,
    };
  } catch (error) {
    return {
      ok: false,
      stage: "notion-query",
      configuredStatusProperty: resolved.statusPropertyName || null,
      configuredCompletedStatus: resolved.completedStatusValue,
      error: error instanceof Error ? error.message : "Unknown Notion query error.",
    };
  }
});
