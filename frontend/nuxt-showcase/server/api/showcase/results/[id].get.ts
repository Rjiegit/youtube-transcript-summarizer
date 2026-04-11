import { createError, defineEventHandler } from "h3";

import { fetchShowcaseDetail } from "../../../utils/notion";
import { resolveShowcaseConfig } from "../results.get";

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event);
  const { notionApiKey, notionDatabaseId } = resolveShowcaseConfig(config);
  const pageId = String(event.context.params?.id || "").trim();

  if (!notionApiKey || !notionDatabaseId) {
    throw createError({
      statusCode: 500,
      statusMessage: "Missing Notion showcase configuration.",
    });
  }

  if (!pageId) {
    throw createError({
      statusCode: 400,
      statusMessage: "Missing showcase result id.",
    });
  }

  try {
    return await fetchShowcaseDetail({
      apiKey: notionApiKey,
      databaseId: notionDatabaseId,
      pageId,
    });
  } catch (error) {
    throw createError({
      statusCode: 502,
      statusMessage: error instanceof Error ? error.message : "Failed to load showcase detail.",
    });
  }
});
