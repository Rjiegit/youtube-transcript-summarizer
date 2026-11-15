import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { loadTopicReadings } from '../scripts/topic-readings-content.mjs';
let directory: string;
afterEach(async () => { if (directory) await rm(directory, { recursive: true, force: true }); });
const categories = [{ id: 'agent-engineering', label: '工程' }];
const metadata = { topicId: 'agent-memory', categoryIds: ['agent-engineering'], revision: 1,
  analysisVersion: 'topic-synthesis-v1', updatedAt: '2026-11-15T20:03:45+08:00', coverageStart: '2026-11-01',
  coverageThrough: '2026-11-14', coverageMode: 'selected-sources', sourceCount: 1, title: '記憶如何維護？',
  summary: '保存後仍須更正。', relevance: '反覆交辦的工作。', limitation: '未獨立驗證。',
  changes: '首次整理，尚無前版可比較。', prioritySourceUrl: 'https://www.youtube.com/watch?v=test', privateBody: 'must not escape' };
async function fixture(meta = metadata, body = '## 整合做法\n\n核對來源。[來源][S1]\n\n## 想深入時怎麼選\n\n優先看來源。\n\n[S1]: https://www.youtube.com/watch?v=test') {
  directory = await mkdtemp(join(tmpdir(), 'topic-readings-'));
  await mkdir(join(directory, 'docs'));
  await writeFile(join(directory, 'manifest.json'), JSON.stringify({ schemaVersion: 1, topics: [{ id: 'agent-memory', published: true }] }));
  await writeFile(join(directory, 'docs/agent-memory.md'), `---\n${JSON.stringify(meta)}\n---\n\n# 記憶如何維護？\n\n[回入口](index.md)\n\n簡介。\n\n${body}`);
}
const load = () => loadTopicReadings(directory, join(directory, 'docs'), categories);
describe('reviewed topic readings', () => {
  it('bundles Markdown, resolves references per section and projects public fields', async () => {
    await fixture(); const [topic] = await load();
    expect(topic.id).toBe('agent-memory');
    expect(topic.sections[0].content).toContain('[S1]: https://www.youtube.com/watch?v=test');
    expect(topic.sources.heading).toBe('想深入時怎麼選');
    expect(JSON.stringify(topic)).not.toContain('must not escape');
    expect(JSON.stringify(topic)).not.toContain('index.md');
  });
  it('does not load drafts and rejects duplicate or unsafe manifest IDs', async () => {
    await fixture();
    for (const topics of [[{ id: 'agent-memory', published: false }], [{ id: '../private', published: true }],
      [{ id: 'agent-memory', published: true }, { id: 'agent-memory', published: true }]]) {
      await writeFile(join(directory, 'manifest.json'), JSON.stringify({ schemaVersion: 1, topics }));
      if (topics[0].published === false) expect(await load()).toEqual([]);
      else await expect(load()).rejects.toThrow();
    }
  });
  it.each([{ sourceCount: 2 }, { categoryIds: ['unknown'] }, { coverageThrough: '2026-02-30' },
    { prioritySourceUrl: 'https://youtu.be/unknown' }, { summary: 'https://notion.so/private' }, { updatedAt: '2026-11-01T00:00:00+08:00' }])('rejects inconsistent metadata: %j', async (change) => {
    await fixture({ ...metadata, ...change }); await expect(load()).rejects.toThrow();
  });
  it.each(['[bad][X]\n\n[X]: javascript:alert(1)', '[private](https://notion.so/private)',
    '[leak](../../data/private.json)'])('rejects unsafe or private links', async (link) => {
    await fixture(metadata, `## 整合做法\n\n${link}\n\n## 想深入時怎麼選\n\n參考。`);
    await expect(load()).rejects.toThrow();
  });
});
