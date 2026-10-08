// Loaded only by the SSR test's child process, never by the application build.
import { setTimeout } from "node:timers/promises";

const originalFetch = globalThis.fetch;
globalThis.fetch = async (input, options) => {
  const url = new URL(typeof input === "string" ? input : input.url ?? input);
  if (url.hostname === "127.0.0.1" || url.hostname === "localhost") {
    return originalFetch(input, options);
  }
  if (url.hostname !== "api.notion.com") {
    throw new Error("SSR fixture forbids external requests.");
  }
  await setTimeout(120);
  const id = url.pathname.split("/")[3];
  if (id.startsWith("failed-")) {
    return Response.json({ message: "Private upstream failure" }, { status: 503 });
  }
  if (url.pathname.startsWith("/v1/databases/")) {
    return Response.json({ properties: {
      Name: { type: "title" }, Summary: { type: "rich_text" }, URL: { type: "url" },
    } });
  }
  if (url.pathname.startsWith("/v1/pages/")) {
    return Response.json({
      id,
      created_time: "2026-10-08T00:00:00.000Z",
      properties: {
        Name: { title: [{ plain_text: `影片「${id}」 & <筆記> "標題"` }] },
        Summary: { rich_text: [{ plain_text: id.startsWith("empty-") ? "" : "## 摘要\n\n分享 **重點** & <內容>" }] },
        URL: { url: "https://example.com/video" },
      },
    });
  }
  if (url.pathname.startsWith("/v1/blocks/")) {
    return Response.json({ results: [], has_more: false });
  }
  throw new Error("Unexpected Notion fixture request.");
};
