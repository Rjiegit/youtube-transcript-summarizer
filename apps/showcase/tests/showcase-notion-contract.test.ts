import { describe, expect, it } from "vitest";

import completedPage from "../../../tests/fixtures/notion_completed_page.json";
import { mapNotionPageToResult } from "../server/utils/notion";


describe("shared Notion completed-page contract", () => {
  it("maps the Python writer property shape into a showcase result", () => {
    const result = mapNotionPageToResult(completedPage);

    expect(result).toMatchObject({
      id: "contract-page-id",
      title: "Contract title",
      summary: "Contract summary",
      source_url: "https://www.youtube.com/watch?v=contract",
      processing_duration: 12.5,
    });
  });
});
