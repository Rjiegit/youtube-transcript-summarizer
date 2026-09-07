import type { NotionPage } from "../server/utils/notion";
import type { NotionBlock } from "../server/utils/notion";

export const sampleNotionPages: NotionPage[] = [
  {
    id: "result-2-page-id",
    created_time: "2026-03-28T12:00:00.000Z",
    properties: {
      Name: {
        title: [{ plain_text: "Second result" }],
      },
      Summary: {
        rich_text: [{ plain_text: "A concise summary of the second result." }],
      },
      URL: {
        url: "https://www.youtube.com/watch?v=second",
      },
      "Processing Duration": {
        number: 12.4,
      },
      Status: {
        select: {
          name: "Completed",
        },
      },
    },
  },
  {
    id: "result-1-page-id",
    created_time: "2026-03-27T12:00:00.000Z",
    properties: {
      Name: {
        title: [{ plain_text: "First result" }],
      },
      Summary: {
        rich_text: [{ plain_text: "First result summary." }],
      },
      URL: {
        url: "https://www.youtube.com/watch?v=first",
      },
      "Processing Duration": {
        number: 8.6,
      },
      Status: {
        select: {
          name: "Completed",
        },
      },
    },
  },
];

export const sampleNotionBlocks: NotionBlock[] = [
  {
    id: "block-1",
    type: "paragraph",
    paragraph: {
      rich_text: [{ plain_text: "Detailed paragraph one." }],
    },
  },
  {
    id: "block-2",
    type: "paragraph",
    paragraph: {
      rich_text: [{ plain_text: "Detailed paragraph two." }],
    },
  },
];
