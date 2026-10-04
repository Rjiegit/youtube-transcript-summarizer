// 執行：SHOWCASE_BENCHMARK=1 npx vitest run scripts/detail-parallel.experiment.test.ts --environment node
import { loadEnvFile } from "node:process";
import { performance } from "node:perf_hooks";
import { expect, it } from "vitest";
import {
  fetchLatestCompletedResults, fetchShowcaseDetail, fetchDatabaseSchema,
  fetchPage, fetchPageBlocks, resolveFieldMapping, mapNotionPageToResult, renderNotionBlocks,
} from "../server/utils/notion";
import { resolveShowcaseConfig } from "../server/utils/config";

it.skipIf(process.env.SHOWCASE_BENCHMARK !== "1")("比較真實 Notion 詳細頁串行與平行耗時", async () => {
  loadEnvFile(".env");
  const config = resolveShowcaseConfig();
  expect(Boolean(config.notionApiKey && config.notionDatabaseId)).toBe(true);
  const apiKey = config.notionApiKey;
  const databaseId = config.notionDatabaseId;
  const pageId = process.env.SHOWCASE_BENCHMARK_PAGE_ID?.trim()
    || (await fetchLatestCompletedResults({ apiKey, databaseId })).items[0]?.id;
  if (!pageId) throw new Error("No article available for the benchmark.");
  const rows: Array<{ round: number; mode: "serial" | "parallel"; totalMs: number }> = [];
  async function run(mode: "serial" | "parallel", round: number) {
    const requests: Array<{ path: string; ms: number; status: number }> = [];
    const fetchImpl: typeof fetch = async (input, init) => {
      const start = performance.now();
      const response = await fetch(input, init);
      const path = new URL(String(input)).pathname;
      requests.push({ path: path.includes("/blocks/") ? "blocks" : path.includes("/pages/") ? "page" : "schema",
        ms: Math.round(performance.now() - start), status: response.status });
      return response;
    };
    const start = performance.now();
    let result;
    if (mode === "serial") {
      // 保留原始串行流程，避免正式實作改動後比較到兩個平行版本。
      const schema = await fetchDatabaseSchema(apiKey, databaseId, fetchImpl);
      const page = await fetchPage(apiKey, pageId, fetchImpl);
      const blocks = await fetchPageBlocks(apiKey, pageId, fetchImpl);
      const base = mapNotionPageToResult(page, resolveFieldMapping(schema));
      result = { ...base, content: renderNotionBlocks(blocks) || base.summary };
    } else {
      result = await fetchShowcaseDetail({ apiKey, databaseId, pageId, fetchImpl });
    }
    const row = { round, mode, totalMs: Math.round(performance.now() - start), requests };
    rows.push(row);
    console.log(JSON.stringify(row));
    return result;
  }
  const baseline = await run("serial", 0);
  expect(await run("parallel", 0)).toEqual(baseline);
  for (let round = 1; round <= 4; round++) {
    for (const mode of round % 2 ? ["serial", "parallel"] as const : ["parallel", "serial"] as const) {
      // 將各輪分開，降低短時間累積請求對測量的干擾。
      await new Promise((resolve) => setTimeout(resolve, 1500));
      expect(await run(mode, round)).toEqual(baseline);
    }
  }
  const median = (values: number[]) => {
    const sorted = values.sort((a, b) => a - b);
    return (sorted[1] + sorted[2]) / 2;
  };
  const serial = median(rows.filter((r) => r.round !== 0 && r.mode === "serial").map((r) => r.totalMs));
  const parallel = median(rows.filter((r) => r.round !== 0 && r.mode === "parallel").map((r) => r.totalMs));
  console.log(JSON.stringify({ serialMedianMs: serial, parallelMedianMs: parallel,
    improvementPercent: Math.round((1 - parallel / serial) * 100), outputsEqual: true }));
}, 240000);
