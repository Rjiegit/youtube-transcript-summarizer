import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";

import { loadInsightContent } from "../scripts/weekly-insights-content.mjs";

let directory: string;
afterEach(async () => { if (directory) await rm(directory, { recursive: true, force: true }); });

async function fixture(overrides = {}) {
  if (directory) await rm(directory, { recursive: true, force: true });
  directory = await mkdtemp(join(tmpdir(), "weekly-insights-test-"));
  const series = {
    schemaVersion: 1, analysisVersion: "topic-v1", timezone: "Asia/Taipei", weekConvention: "sunday-saturday",
    dateBasis: "notion-created-time", dedupPolicy: "within-week-source", collectionStart: "2026-09-01",
    asOf: "2026-10-09T09:44:10Z", uniqueSourceCount: 1, reportStarts: ["2026-09-06"],
    categories: [{ id: "agent-engineering", label: "Agent 工程" }],
  };
  const report = {
    schemaVersion: 1, analysisVersion: "topic-v1", published: true, publishedAt: "2026-10-09T09:44:10Z",
    revision: 1, start: "2026-09-06", endExclusive: "2026-09-13", coverageStart: "2026-09-06",
    asOf: series.asOf, periodState: "closed", dataCompleteness: "complete", title: "測試週報", summary: "摘要",
    metrics: { rawCount: 1, sourceCount: 1, newSourceCount: 1, recurringSourceCount: 0 },
    categories: [{ id: "agent-engineering", count: 1 }], sources: [], ...overrides,
  };
  await mkdir(join(directory, "2026-09-06"));
  await writeFile(join(directory, "series.json"), JSON.stringify(series));
  await writeFile(join(directory, "overview.md"), "# 整體觀察");
  await writeFile(join(directory, "2026-09-06/report.json"), JSON.stringify(report));
  await writeFile(join(directory, "2026-09-06/report.md"), "# 本週內容\n\n測試正文");
  return series;
}

describe("weekly insight publication content", () => {
  it("loads reviewed content without forwarding unknown private fields", async () => {
    await fixture({ privateBody: "must not escape" });
    const result = await loadInsightContent(directory);
    expect(result.weeks).toHaveLength(1);
    expect(result.weeks[0].content).toContain("測試正文");
    expect(JSON.stringify(result)).not.toContain("must not escape");
  });

  it("excludes drafts entirely and derives totals from the visible manifest", async () => {
    await fixture({ published: false, publishedAt: null });
    const result = await loadInsightContent(directory);
    expect(result.weeks).toEqual([]);
    expect(result.series.uniqueSourceCount).toBeNull();
    expect(result.series.overview).toBe("");
  });

  it("rejects inconsistent counts, unsafe links and a non-Sunday period", async () => {
    await fixture({ categories: [{ id: "agent-engineering", count: 2 }] });
    await expect(loadInsightContent(directory)).rejects.toThrow(/count/i);
    await fixture({ sources: [{ title: "危險", categoryId: "agent-engineering", sourceUrl: "javascript:alert(1)" }] });
    await expect(loadInsightContent(directory)).rejects.toThrow(/URL/i);
    await fixture({ endExclusive: "2026-09-14" });
    await expect(loadInsightContent(directory)).rejects.toThrow(/period/i);
  });

  it("rejects path traversal before loading files", async () => {
    const series = await fixture();
    await writeFile(join(directory, "series.json"), JSON.stringify({ ...series, reportStarts: ["../private"] }));
    await expect(loadInsightContent(directory)).rejects.toThrow(/date/i);
  });
});
