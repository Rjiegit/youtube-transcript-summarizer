import { readFile } from "node:fs/promises";
import { fileURLToPath, URL } from "node:url";
import { join } from "node:path";
import MarkdownIt from "markdown-it";

const getAppRoot = () => fileURLToPath(new URL("../", import.meta.url));
const markdown = new MarkdownIt({ html: false });
const slug = /^[a-z]+(?:-[a-z]+)*$/;
function check(ok, message) {
  if (!ok) throw new Error(`Topic readings: ${message}`);
}
function nonempty(value, name) {
  check(typeof value === "string" && value.trim(), `missing ${name}`);
  check(!/notion\.(?:so|com)|data\/reports\//i.test(value), "private metadata");
  return value.trim();
}
function day(value) {
  check(typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value), "invalid date");
  const parsed = new Date(`${value}T00:00:00Z`);
  check(Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value, "invalid date");
}
function youtube(value) {
  let url;
  try { url = new URL(value); } catch { throw new Error("Topic readings: invalid source URL"); }
  check(url.protocol === "https:" && !url.username && !url.password &&
    ["youtube.com", "www.youtube.com", "youtu.be"].includes(url.hostname), "unsafe source URL");
  return url.href;
}

export async function loadTopicReadings(
  manifestDirectory = join(getAppRoot(), "content/topic-readings"),
  documentDirectory = manifestDirectory,
  categories = [],
) {
  const manifest = JSON.parse(await readFile(join(manifestDirectory, "manifest.json"), "utf8"));
  check(manifest.schemaVersion === 1 && Array.isArray(manifest.topics), "invalid manifest");
  const ids = new Set();
  const allowedCategories = new Set(categories.map((category) => category.id));
  const topics = [];
  for (const entry of manifest.topics) {
    check(typeof entry.id === "string" && slug.test(entry.id) && !ids.has(entry.id), "invalid/duplicate topic ID");
    ids.add(entry.id);
    check(typeof entry.published === "boolean", "invalid publication state");
    if (!entry.published) continue;
    const document = await readFile(join(documentDirectory, `${entry.id}.md`), "utf8");
    const frontmatter = document.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
    check(frontmatter, "missing JSON frontmatter");
    const meta = JSON.parse(frontmatter[1]);
    check(meta.topicId === entry.id && meta.analysisVersion === "topic-synthesis-v1", "inconsistent topic/version");
    check(Array.isArray(meta.categoryIds) && meta.categoryIds.length &&
      new Set(meta.categoryIds).size === meta.categoryIds.length && meta.categoryIds.every((id) => allowedCategories.has(id)),
    "unknown/duplicate category");
    check(Number.isInteger(meta.revision) && meta.revision > 0, "invalid revision");
    day(meta.coverageStart); day(meta.coverageThrough);
    check(meta.coverageStart <= meta.coverageThrough, "invalid coverage range");
    check(typeof meta.updatedAt === "string" && /T.*(?:Z|[+-]\d{2}:\d{2})$/.test(meta.updatedAt) &&
      Number.isFinite(Date.parse(meta.updatedAt)) &&
      Date.parse(meta.updatedAt) >= Date.parse(`${meta.coverageThrough}T23:59:59+08:00`), "invalid update time");
    check(["selected-sources", "full-scope"].includes(meta.coverageMode), "invalid coverage mode");
    check(Number.isInteger(meta.sourceCount) && meta.sourceCount > 0, "invalid source count");
    // The document remains the single source of truth; omit its repository navigation on the website.
    const body = document.slice(frontmatter[0].length).trim().replace(/^# [^\n]+\n+/, "")
      .replace(/^\[回[^\]]+\]\([^\n)]+\)[^\n]*\n+/, "");
    check(!/notion\.(?:so|com)|data\/reports\//i.test(body), "private content");
    check(!/\]\s*:\s*(?:javascript|data|vbscript):|\]\(\s*(?:javascript|data|vbscript):/i.test(body), "unsafe Markdown URL");
    const tokens = markdown.parse(body, {});
    const urls = new Set();
    for (const token of tokens) {
      for (const child of token.children ?? []) {
        if (child.type === "link_open") urls.add(youtube(child.attrGet("href")));
        check(child.type !== "image", "images are not supported in topic readings");
      }
    }
    check(urls.size === meta.sourceCount, "inconsistent source count");
    const prioritySourceUrl = youtube(meta.prioritySourceUrl);
    check(urls.has(prioritySourceUrl), "unknown priority source");
    const references = body.split("\n").filter((line) => /^\[[^\]]+\]:\s*https:\/\//.test(line)).join("\n");
    const withReferences = (value) => `${value.trim()}\n\n${references}`;
    const headings = [...body.matchAll(/^## (.+)$/gm)];
    check(headings.length > 1 && headings.at(-1)[1] === "想深入時怎麼選", "missing reading/source sections");
    const intro = withReferences(body.slice(0, headings[0].index));
    const sections = headings.map((heading, index) => ({
      heading: heading[1], content: withReferences(body.slice(heading.index + heading[0].length,
        headings[index + 1]?.index ?? body.length).replace(/^\[[^\]]+\]:\s*https:\/\/.*$/gm, "")),
    }));
    const sources = sections.pop();
    topics.push({ id: entry.id, title: nonempty(meta.title, "title"), summary: nonempty(meta.summary, "summary"),
      relevance: nonempty(meta.relevance, "relevance"), limitation: nonempty(meta.limitation, "limitation"),
      changes: nonempty(meta.changes, "changes"), categoryIds: [...meta.categoryIds], revision: meta.revision,
      analysisVersion: meta.analysisVersion, updatedAt: meta.updatedAt, coverageStart: meta.coverageStart,
      coverageThrough: meta.coverageThrough, coverageMode: meta.coverageMode, sourceCount: meta.sourceCount,
      prioritySourceUrl, intro, sections, sources });
  }
  return topics.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt) || a.id.localeCompare(b.id));
}
