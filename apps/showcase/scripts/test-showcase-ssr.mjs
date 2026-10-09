import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { createServer } from "node:net";
import { fileURLToPath } from "node:url";
import { setTimeout } from "node:timers/promises";
import { test } from "node:test";
import { JSDOM } from "jsdom";

const projectDir = fileURLToPath(new URL("../", import.meta.url));
const siteUrl = "https://video-knowledge.hellojie.me";
const userAgents = [
  "Mozilla/5.0",
  "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)",
  "facebookexternalhit/1.1",
  "Slackbot-LinkExpanding 1.0",
  "Line/1.0",
];

function headValue(document, key) {
  const matches = document.head.querySelectorAll(`meta[property="${key}"],meta[name="${key}"]`);
  assert.equal(matches.length, 1, `Exactly one ${key} tag must be present`);
  return matches[0].getAttribute("content");
}

async function startServer() {
  const reservation = createServer();
  reservation.listen(0, "127.0.0.1");
  await once(reservation, "listening");
  const port = reservation.address().port;
  await new Promise((resolve) => reservation.close(resolve));
  const child = spawn(process.execPath, [
    "--import", "./test-data/notion-fetch-fixture.mjs", ".output/server/index.mjs",
  ], {
    cwd: projectDir,
    env: {
      ...process.env,
      NODE_ENV: "production", HOST: "127.0.0.1", PORT: String(port),
      NOTION_API_KEY: "ssr-fixture", NUXT_NOTION_API_KEY: "ssr-fixture",
      NOTION_DATABASE_ID: "fixture-db", NUXT_NOTION_DATABASE_ID: "fixture-db",
      NUXT_PUBLIC_SITE_URL: siteUrl,
      READ_STATE_SYNC_ENABLED: "false", NUXT_READ_STATE_SYNC_ENABLED: "false",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  let logs = "";
  child.stdout.on("data", (chunk) => { logs += chunk; });
  child.stderr.on("data", (chunk) => { logs += chunk; });
  const baseUrl = `http://127.0.0.1:${port}`;
  async function stop() {
    if (child.exitCode !== null || child.signalCode !== null) return;
    const exited = once(child, "exit");
    child.kill("SIGTERM");
    const forceStop = globalThis.setTimeout(() => child.kill("SIGKILL"), 3000);
    await exited;
    clearTimeout(forceStop);
  }
  try {
    for (let attempt = 0; attempt < 100; attempt++) {
      if (child.exitCode !== null) throw new Error(`SSR server exited: ${logs}`);
      try {
        const response = await fetch(`${baseUrl}/favicon.svg`, { signal: AbortSignal.timeout(500) });
        if (response.ok) return { baseUrl, stop };
      } catch {
        // Wait for the production server to bind its port.
      }
      await setTimeout(100);
    }
    throw new Error(`SSR server did not start: ${logs}`);
  } catch (error) {
    await stop();
    throw error;
  }
}

test("production SSR emits complete article metadata before hydration", { timeout: 30000 }, async (t) => {
  const server = await startServer();
  t.after(server.stop);
  for (const [index, userAgent] of userAgents.entries()) {
    await t.test(`cold article response for ${userAgent}`, async () => {
      const id = `cold-${index}`;
      const response = await fetch(`${server.baseUrl}/results/${id}?og_test=version#fragment`, {
        headers: { "User-Agent": userAgent },
      });
      assert.equal(response.status, 200);
      assert.match(response.headers.get("content-type"), /text\/html/);
      const dom = new JSDOM(await response.text());
      const document = dom.window.document;
      const title = `影片「${id}」 & <筆記> "標題"`;
      assert.equal(document.title, `${title} | 影片筆記庫`);
      assert.equal(headValue(document, "og:title"), title);
      assert.equal(headValue(document, "og:description"), "摘要 分享 重點 & <內容>");
      assert.equal(headValue(document, "description"), headValue(document, "og:description"));
      assert.equal(headValue(document, "og:type"), "article");
      assert.equal(headValue(document, "og:site_name"), "影片筆記庫");
      assert.equal(headValue(document, "og:url"), `${siteUrl}/results/${id}`);
      const canonical = document.head.querySelectorAll('link[rel="canonical"]');
      assert.equal(canonical.length, 1);
      assert.equal(canonical[0].getAttribute("href"), `${siteUrl}/results/${id}`);
      assert.equal(headValue(document, "og:image"), `${siteUrl}/share-preview.png`);
      assert.equal(headValue(document, "og:image:type"), "image/png");
      assert.equal(headValue(document, "og:image:width"), "1200");
      assert.equal(headValue(document, "og:image:height"), "630");
      assert.ok(headValue(document, "og:image:alt"));
      assert.equal(headValue(document, "twitter:card"), "summary_large_image");
      assert.equal(headValue(document, "twitter:title"), title);
      assert.equal(headValue(document, "twitter:description"), headValue(document, "og:description"));
      assert.equal(headValue(document, "twitter:image"), headValue(document, "og:image"));
      dom.window.close();
    });
  }
  await t.test("empty summary uses the site description", async () => {
    const response = await fetch(`${server.baseUrl}/results/empty-summary`);
    assert.equal(response.status, 200);
    const dom = new JSDOM(await response.text());
    assert.equal(headValue(dom.window.document, "og:description"), "收藏從影片整理出的重點筆記");
    dom.window.close();
  });
  await t.test("share image is publicly served as a 1200 by 630 PNG", async () => {
    const response = await fetch(`${server.baseUrl}/share-preview.png`);
    assert.equal(response.status, 200);
    assert.match(response.headers.get("content-type"), /image\/png/);
    const bytes = Buffer.from(await response.arrayBuffer());
    assert.deepEqual([...bytes.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10]);
    assert.equal(bytes.readUInt32BE(16), 1200);
    assert.equal(bytes.readUInt32BE(20), 630);
  });
  await t.test("upstream failure produces a non-cacheable error response", async () => {
    const response = await fetch(`${server.baseUrl}/results/failed-upstream`);
    assert.equal(response.status, 502);
    assert.equal(response.headers.get("cache-control"), "no-store");
    const html = await response.text();
    assert.ok(!html.includes("Private upstream failure"));
  });
});

test("weekly insights are bundled, calendar-aligned and rendered before hydration", { timeout: 30000 }, async (t) => {
  const server = await startServer();
  t.after(server.stop);
  const response = await fetch(`${server.baseUrl}/api/showcase/insights`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("cache-control"), /s-maxage=300/);
  assert.ok(response.headers.get("etag"));
  const { series, weeks } = await response.json();
  assert.equal(series.weekConvention, "sunday-saturday");
  for (const week of weeks) {
    assert.equal(new Date(`${week.start}T00:00:00Z`).getUTCDay(), 0);
    assert.ok(!("content" in week));
    assert.ok(!("sources" in week));
  }
  const index = await fetch(`${server.baseUrl}/insights`);
  assert.equal(index.status, 200);
  const indexDom = new JSDOM(await index.text());
  assert.match(indexDom.window.document.body.textContent, /週日 — 週六/);
  assert.equal(indexDom.window.document.querySelectorAll(".insight-week-card").length, weeks.length);
  assert.equal(indexDom.window.document.querySelectorAll(".insight-chart__column").length,
    weeks.filter((week) => week.periodState === "closed" && week.coverageStart === week.start &&
      week.dataCompleteness === "complete").length);
  indexDom.window.close();
  if (weeks.length) {
    const week = weeks[0];
    const detail = await fetch(`${server.baseUrl}/insights/${week.start}`);
    assert.equal(detail.status, 200);
    const dom = new JSDOM(await detail.text());
    assert.match(dom.window.document.title, new RegExp(week.title));
    assert.equal(headValue(dom.window.document, "description"), week.summary);
    assert.equal(headValue(dom.window.document, "og:url"), `${siteUrl}/insights/${week.start}`);
    assert.ok(dom.window.document.querySelector(".markdown-content h2"));
    assert.ok(!dom.window.document.body.textContent.includes("snapshot.private"));
    dom.window.close();
  }
  const missing = await fetch(`${server.baseUrl}/api/showcase/insights/1900-01-01`);
  assert.equal(missing.status, 404);
  assert.equal(missing.headers.get("cache-control"), "no-store");
  const missingPage = await fetch(`${server.baseUrl}/insights/1900-01-01`);
  assert.equal(missingPage.status, 404);
});
