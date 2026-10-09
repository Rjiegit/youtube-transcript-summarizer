import { readFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, URL } from "node:url";
import { join } from "node:path";

const getAppRoot = () => fileURLToPath(new URL("../", import.meta.url));
const datePattern = /^\d{4}-\d{2}-\d{2}$/;
function requireValue(condition, message) {
  if (!condition) throw new Error(`Weekly insights: ${message}`);
}
function date(value) {
  requireValue(typeof value === "string" && datePattern.test(value), "invalid date");
  const parsed = new Date(`${value}T00:00:00Z`);
  requireValue(Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value, "invalid date");
  return parsed;
}
function timestamp(value) {
  requireValue(typeof value === "string" && /T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value) &&
    Number.isFinite(Date.parse(value)), "invalid timestamp");
}
function text(value, name) {
  requireValue(typeof value === "string" && value.trim().length > 0, `missing ${name}`);
  return value;
}
function integer(value, name) {
  requireValue(Number.isInteger(value) && value >= 0, `invalid ${name} count`);
}
function safeMarkdown(value) {
  requireValue(!/\]\(\s*(?:javascript|data|vbscript):/i.test(value), "unsafe Markdown URL");
  requireValue(!/https?:\/\/[^\s)]*(?:notion\.so|notion\.com)/i.test(value), "private Notion URL in public Markdown");
  return value;
}

export async function loadInsightContent(directory = join(getAppRoot(), "content/weekly-insights")) {
  const raw = JSON.parse(await readFile(join(directory, "series.json"), "utf8"));
  requireValue(raw.schemaVersion === 1, "unsupported schema");
  requireValue(raw.timezone === "Asia/Taipei" && raw.weekConvention === "sunday-saturday", "invalid calendar");
  requireValue(raw.dateBasis === "record-created-time" && raw.dedupPolicy === "within-week-source", "invalid analysis policy");
  date(raw.collectionStart);
  timestamp(raw.asOf);
  text(raw.analysisVersion, "analysis version");
  integer(raw.uniqueSourceCount, "unique source");
  requireValue(Array.isArray(raw.categories) && raw.categories.length > 0, "missing categories");
  const ids = new Set();
  const categories = raw.categories.map(({ id, label }) => {
    requireValue(typeof id === "string" && /^[a-z]+(?:-[a-z]+)*$/.test(id) && !ids.has(id), "invalid category ID");
    ids.add(id);
    return { id, label: text(label, "category label") };
  });
  requireValue(Array.isArray(raw.reportStarts) && new Set(raw.reportStarts).size === raw.reportStarts.length,
    "invalid or duplicate report dates");
  const overview = safeMarkdown(await readFile(join(directory, "overview.md"), "utf8"));
  const weeks = [];
  for (const start of raw.reportStarts) {
    const startDate = date(start);
    requireValue(startDate.getUTCDay() === 0, "period must start on Sunday");
    const report = JSON.parse(await readFile(join(directory, start, "report.json"), "utf8"));
    if (report.published !== true) continue;
    requireValue(report.schemaVersion === 1 && report.analysisVersion === raw.analysisVersion, "inconsistent schema/version");
    requireValue(report.start === start, "inconsistent period start");
    const endDate = date(report.endExclusive);
    requireValue(endDate.getTime() - startDate.getTime() === 7 * 86400000, "invalid seven-day period");
    const expectedCoverage = start > raw.collectionStart ? start : raw.collectionStart;
    requireValue(report.coverageStart === expectedCoverage && date(report.coverageStart) < endDate, "invalid coverage date");
    timestamp(report.asOf);
    timestamp(report.publishedAt);
    requireValue(report.asOf === raw.asOf, "inconsistent snapshot time");
    requireValue(["open", "closed"].includes(report.periodState), "invalid period state");
    const endInstant = Date.parse(`${report.endExclusive}T00:00:00+08:00`);
    requireValue(report.periodState === (endInstant <= Date.parse(report.asOf) ? "closed" : "open"), "inconsistent period state");
    requireValue(["complete", "partial"].includes(report.dataCompleteness), "invalid data completeness");
    requireValue(Number.isInteger(report.revision) && report.revision > 0, "invalid revision");
    const metrics = {};
    for (const key of ["rawCount", "sourceCount", "newSourceCount", "recurringSourceCount"]) {
      integer(report.metrics?.[key], key);
      metrics[key] = report.metrics[key];
    }
    requireValue(metrics.sourceCount <= metrics.rawCount &&
      metrics.newSourceCount + metrics.recurringSourceCount === metrics.sourceCount, "inconsistent metric counts");
    requireValue(Array.isArray(report.categories) && report.categories.length === categories.length, "missing category counts");
    const reportIds = new Set();
    const counts = report.categories.map(({ id, count }) => {
      requireValue(ids.has(id) && !reportIds.has(id), "unknown/duplicate category");
      reportIds.add(id);
      integer(count, "category");
      return { id, count };
    });
    requireValue(counts.reduce((sum, category) => sum + category.count, 0) === metrics.sourceCount, "inconsistent category counts");
    requireValue(Array.isArray(report.sources), "missing sources");
    const urls = new Set();
    const sources = report.sources.map(({ title, categoryId, sourceUrl }) => {
      let url;
      try { url = new URL(sourceUrl); } catch { throw new Error("Weekly insights: invalid source URL"); }
      requireValue(url.protocol === "https:" && !url.username && !url.password &&
        ["www.youtube.com", "youtube.com", "youtu.be"].includes(url.hostname) && !urls.has(url.href), "unsafe/duplicate source URL");
      requireValue(ids.has(categoryId), "unknown source category");
      urls.add(url.href);
      return { title: text(title, "source title"), categoryId, sourceUrl: url.href };
    });
    const content = safeMarkdown(text(await readFile(join(directory, start, "report.md"), "utf8"), "report Markdown"));
    weeks.push({ start, endExclusive: report.endExclusive, coverageStart: report.coverageStart,
      periodState: report.periodState, dataCompleteness: report.dataCompleteness, revision: report.revision,
      asOf: report.asOf, title: text(report.title, "title"), summary: text(report.summary, "summary"), metrics,
      categories: counts, sources, content, qualityNote: report.qualityNote ?? "" });
  }
  weeks.sort((a, b) => a.start.localeCompare(b.start));
  const allPublished = weeks.length === raw.reportStarts.length && weeks.length > 0;
  let topicInsights = null;
  if (allPublished && raw.topicInsights) {
    const { fromWeek, toWeek, items } = raw.topicInsights;
    date(fromWeek);
    date(toWeek);
    const analysisWeeks = weeks.filter((week) => week.start >= fromWeek && week.start <= toWeek);
    requireValue(fromWeek <= toWeek && analysisWeeks[0]?.start === fromWeek &&
      analysisWeeks.at(-1)?.start === toWeek &&
      analysisWeeks.length === (date(toWeek) - date(fromWeek)) / (7 * 86400000) + 1 && analysisWeeks.every((week) =>
        week.periodState === "closed" && week.dataCompleteness === "complete" && week.coverageStart === week.start),
    "invalid topic insight period");
    requireValue(Array.isArray(items) && items.length === categories.length, "missing topic insights");
    const topicIds = new Set();
    topicInsights = { fromWeek, toWeek, items: items.map(({ categoryId, change, signal, watch }) => {
      requireValue(ids.has(categoryId) && !topicIds.has(categoryId), "unknown/duplicate topic insight category");
      topicIds.add(categoryId);
      return { categoryId, change: safeMarkdown(text(change, "topic change")),
        signal: safeMarkdown(text(signal, "topic signal")), watch: safeMarkdown(text(watch, "topic watch")) };
    }) };
  }
  requireValue(!allPublished || weeks.reduce((sum, week) => sum + week.metrics.newSourceCount, 0) === raw.uniqueSourceCount,
    "inconsistent series unique count");
  const trackIds = new Set();
  let topicTracks = [];
  if (allPublished && raw.topicTracks !== undefined) {
    requireValue(Array.isArray(raw.topicTracks), "invalid topic tracks");
    topicTracks = raw.topicTracks.map((track) => {
      requireValue(typeof track.id === "string" && /^[a-z]+(?:-[a-z]+)*$/.test(track.id) &&
        !trackIds.has(track.id), "invalid/duplicate topic track ID");
      trackIds.add(track.id);
      requireValue(Array.isArray(track.categoryIds) && track.categoryIds.length > 0 &&
        new Set(track.categoryIds).size === track.categoryIds.length && track.categoryIds.every((id) => ids.has(id)),
      "unknown/duplicate topic track category");
      requireValue(Array.isArray(track.observations) && track.observations.length > 0, "missing topic track evidence");
      const observedWeeks = new Set();
      const observations = track.observations.map(({ week, summary }) => {
        const evidence = weeks.find((item) => item.start === week);
        requireValue(evidence && evidence.periodState === "closed" && evidence.dataCompleteness === "complete" &&
          evidence.coverageStart === evidence.start && !observedWeeks.has(week), "invalid topic track evidence week");
        observedWeeks.add(week);
        return { week, summary: safeMarkdown(text(summary, "topic track observation")) };
      }).sort((a, b) => a.week.localeCompare(b.week));
      return { id: track.id, label: safeMarkdown(text(track.label, "topic track label")),
        categoryIds: [...track.categoryIds], change: safeMarkdown(text(track.change, "topic track change")),
        watch: safeMarkdown(text(track.watch, "topic track watch")), observations };
    });
  }
  return {
    series: { collectionStart: raw.collectionStart, asOf: raw.asOf, timezone: raw.timezone,
      weekConvention: raw.weekConvention, dedupPolicy: raw.dedupPolicy,
      analysisVersion: raw.analysisVersion, uniqueSourceCount: allPublished ? raw.uniqueSourceCount : null,
      categories, overview: allPublished ? overview : "", topicInsights, topicTracks },
    weeks,
  };
}

export async function buildInsightRegistry() {
  const content = await loadInsightContent();
  const directory = join(getAppRoot(), ".generated");
  await mkdir(directory, { recursive: true });
  await writeFile(join(directory, "weekly-insights.ts"),
    `// Generated from reviewed weekly insight documents.\nexport default ${JSON.stringify(content)};\n`);
  return content;
}
