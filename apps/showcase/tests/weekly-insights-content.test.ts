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
    dateBasis: "record-created-time", dedupPolicy: "within-week-source", collectionStart: "2026-09-01",
    asOf: "2026-10-09T09:44:10Z", uniqueSourceCount: 1, reportStarts: ["2026-09-06"],
    categories: [{ id: "agent-engineering", label: "Agent 工程" }],
    topicInsights: { fromWeek: "2026-09-06", toWeek: "2026-09-06", items: [
      { categoryId: "agent-engineering", change: "內容轉變", signal: "待觀察訊號", watch: "後續追蹤", privateBody: "must not escape" },
    ] },
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
  it("publishes topic tracks with reviewed week evidence and strips private fields", async () => {
    const series = await fixture();
    const topicTracks = [{ id: "delivery", label: "可靠交付", categoryIds: ["agent-engineering"],
      change: "仍需觀察", watch: "追蹤驗證", privateBody: "must not escape",
      observations: [{ week: "2026-09-06", summary: "討論工作流程", privateBody: "must not escape" }] }];
    await writeFile(join(directory, "series.json"), JSON.stringify({ ...series, topicTracks }));
    const result = await loadInsightContent(directory);
    expect(result.series.topicTracks[0].observations[0].week).toBe("2026-09-06");
    expect(JSON.stringify(result)).not.toContain("must not escape");
    await fixture({ published: false });
    await writeFile(join(directory, "series.json"), JSON.stringify({ ...series, topicTracks }));
    expect((await loadInsightContent(directory)).series.topicTracks).toEqual([]);
  });

  it("rejects topic tracks with unknown categories, unsupported weeks or duplicate IDs", async () => {
    const series = await fixture();
    const track = { id: "delivery", label: "可靠交付", categoryIds: ["agent-engineering"],
      change: "仍需觀察", watch: "追蹤驗證", observations: [{ week: "2026-09-06", summary: "工作流程" }] };
    for (const topicTracks of [[{ ...track, categoryIds: ["unknown"] }],
      [{ ...track, observations: [{ week: "2026-10-04", summary: "未核對" }] }], [track, track]]) {
      await writeFile(join(directory, "series.json"), JSON.stringify({ ...series, topicTracks }));
      await expect(loadInsightContent(directory)).rejects.toThrow(/topic track/);
    }
  });

  it("loads reviewed content without forwarding unknown private fields", async () => {
    await fixture({ privateBody: "must not escape" });
    const result = await loadInsightContent(directory);
    expect(result.weeks).toHaveLength(1);
    expect(result.series.topicTracks).toEqual([]);
    expect(result.weeks[0].content).toContain("測試正文");
    expect(JSON.stringify(result)).not.toContain("must not escape");
  });

  it("excludes drafts entirely and derives totals from the visible manifest", async () => {
    await fixture({ published: false, publishedAt: null });
    const result = await loadInsightContent(directory);
    expect(result.weeks).toEqual([]);
    expect(result.series.uniqueSourceCount).toBeNull();
    expect(result.series.overview).toBe("");
    expect(result.series.topicInsights).toBeNull();
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

  it("rejects topic insights outside complete published weeks or with unknown categories", async () => {
    const series = await fixture();
    series.topicInsights.toWeek = "2026-09-13";
    await writeFile(join(directory, "series.json"), JSON.stringify(series));
    await expect(loadInsightContent(directory)).rejects.toThrow(/topic insight period/);
    const valid = await fixture();
    valid.topicInsights.items[0].categoryId = "private-category";
    await writeFile(join(directory, "series.json"), JSON.stringify(valid));
    await expect(loadInsightContent(directory)).rejects.toThrow(/topic insight category/);
  });
});
