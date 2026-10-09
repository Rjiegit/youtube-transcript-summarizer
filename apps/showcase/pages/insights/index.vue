<script setup lang="ts">
import { computed } from "vue";
import MarkdownContent from "../../components/MarkdownContent.vue";
import WeeklyInsightCard from "../../components/WeeklyInsightCard.vue";
import InsightCategoryTrend from "../../components/InsightCategoryTrend.vue";
import type { InsightListResponse } from "../../types/weekly-insights";
import { categoryShare, comparableWeeks, filterInsightWeeks, filterInsightWeeksByRange, formatWeekRange, insightWeekStatus, weekEndDate } from "../../utils/weekly-insights";
import { formatTaipeiDateTime } from "../../utils/datetime";
import { resolveSiteUrl } from "../../utils/site-url";

const route = useRoute();
const router = useRouter();
const { data, error } = await useFetch<InsightListResponse>("/api/showcase/insights", { server: true });
if (error.value) throw createError({ statusCode: error.value.statusCode || 502, statusMessage: "無法載入每週回顧" });
const series = computed(() => data.value?.series);
const weeks = computed(() => data.value?.weeks ?? []);
const queryValue = (key: string) => typeof route.query[key] === "string" ? String(route.query[key]) : "";
function setQuery(key: string, value: string) {
  const query = { ...route.query };
  if (value) query[key] = value; else delete query[key];
  void router.replace({ query });
}
function weekForDate(value: string, edge: "first" | "last") {
  if (!value) return "";
  const matches = filterInsightWeeks(weeks.value, value, value);
  return edge === "first" ? matches[0]?.start ?? "" : matches.at(-1)?.start ?? "";
}
function setWeekQuery(key: "fromWeek" | "toWeek", value: string) {
  const query = { ...route.query };
  if (!query.fromWeek && queryValue("from")) query.fromWeek = weekForDate(queryValue("from"), "first");
  if (!query.toWeek && queryValue("to")) query.toWeek = weekForDate(queryValue("to"), "last");
  delete query.from;
  delete query.to;
  if (value) query[key] = value; else delete query[key];
  void router.replace({ query });
}
const fromWeek = computed({ get: () => queryValue("fromWeek") || weekForDate(queryValue("from"), "first"),
  set: (value) => setWeekQuery("fromWeek", value) });
const toWeek = computed({ get: () => queryValue("toWeek") || weekForDate(queryValue("to"), "last"),
  set: (value) => setWeekQuery("toWeek", value) });
const hasUnmappedLegacyDates = computed(() =>
  (queryValue("from") && !weekForDate(queryValue("from"), "first")) ||
  (queryValue("to") && !weekForDate(queryValue("to"), "last")));
const categoryId = computed({ get: () => queryValue("category") || series.value?.categories[0]?.id || "",
  set: (value) => setQuery("category", value) });
const includePartial = computed({ get: () => queryValue("partial") === "1", set: (value) => setQuery("partial", value ? "1" : "") });
const selectedCategory = computed(() => series.value?.categories.find((category) => category.id === categoryId.value) ?? series.value?.categories[0]);
const visibleWeeks = computed(() => hasUnmappedLegacyDates.value
  ? filterInsightWeeks(weeks.value, queryValue("from"), queryValue("to"))
  : filterInsightWeeksByRange(weeks.value, fromWeek.value, toWeek.value));
const selectedTopic = computed(() => series.value?.topicInsights?.items.find((item) => item.categoryId === selectedCategory.value?.id));
const topicPeriod = computed(() => {
  const insight = series.value?.topicInsights;
  const last = weeks.value.find((week) => week.start === insight?.toWeek);
  return insight && last ? `${insight.fromWeek}–${weekEndDate(last.endExclusive)}` : "";
});
const newestFirstWeeks = computed(() => [...visibleWeeks.value].reverse());
const completeWeeks = computed(() => comparableWeeks(visibleWeeks.value));
const chartWeeks = computed(() => includePartial.value ? visibleWeeks.value : completeWeeks.value);
const latest = computed(() => completeWeeks.value.at(-1));
const previous = computed(() => completeWeeks.value.at(-2));
const changes = computed(() => {
  if (!latest.value || !previous.value) return [];
  return (series.value?.categories ?? []).map((category) => {
    const current = categoryShare(latest.value!, category.id);
    const prior = categoryShare(previous.value!, category.id);
    return { ...category, change: current === null || prior === null ? null : current - prior };
  }).filter((category) => category.change !== null).sort((a, b) => Math.abs(b.change!) - Math.abs(a.change!)).slice(0, 3);
});
const filtered = computed(() => Boolean(fromWeek.value || toWeek.value || queryValue("from") || queryValue("to")));
const totalSources = computed(() => visibleWeeks.value.reduce((sum, week) => sum + week.metrics.sourceCount, 0));
const totalRaw = computed(() => visibleWeeks.value.reduce((sum, week) => sum + week.metrics.rawCount, 0));
const siteUrl = resolveSiteUrl(useRuntimeConfig().public.siteUrl);
useHead({
  title: "每週回顧",
  link: [{ rel: "canonical", href: `${siteUrl}/insights` }],
  meta: [
    { name: "description", content: "按週日到週六回顧影片筆記，理解主題內容的轉變、值得注意的訊號與後續觀察重點。" },
    { property: "og:title", content: "每週回顧 | 影片筆記庫" },
    { property: "og:description", content: "每週內容摘要、分類趨勢與代表來源。" },
    { property: "og:url", content: `${siteUrl}/insights` },
    { property: "og:image", content: `${siteUrl}/share-preview.png` },
    { name: "twitter:card", content: "summary_large_image" },
    { name: "twitter:title", content: "每週回顧 | 影片筆記庫" },
    { name: "twitter:image", content: `${siteUrl}/share-preview.png` },
  ],
});
</script>

<template>
  <main class="insight-shell">
    <nav class="insight-nav"><NuxtLink to="/">← 影片筆記庫</NuxtLink><span>週日 — 週六 · 每週回顧</span></nav>
    <header class="insight-hero">
      <p class="hero__eyebrow">Weekly Knowledge Review</p><h1>把一週的內容，<br />串成看得見的變化。</h1>
      <p>回顧收錄了什麼，也看看關注的重心如何移動。</p>
      <p v-if="series" class="insight-caption">{{ series.collectionStart }} 起 · 資料截至 {{ formatTaipeiDateTime(series.asOf) }}</p>
    </header>
    <section v-if="!weeks.length" class="state-panel"><h2>尚未整理週報</h2><p>下一份每週回顧完成後會顯示在這裡。</p></section>
    <template v-else>
      <section class="insight-panel insight-editorial">
        <div class="insight-section-heading"><p class="hero__eyebrow">The Bigger Picture</p><h2>整體觀察</h2></div>
        <MarkdownContent v-if="series?.overview" :source="series.overview" />
        <p v-else>目前展示已整理的單週回顧，整體分析尚未完成。</p>
        <p v-if="filtered" class="insight-caption">整體觀察描述完整系列；下方統計與週報依所選週次範圍篩選。</p>
      </section>
      <section class="insight-panel">
        <div class="insight-section-heading"><p class="hero__eyebrow">Topic Trends</p><h2>主題變化與洞見</h2><p>看看內容如何轉向、哪些訊號值得留意，以及接下來可以觀察什麼。</p></div>
        <div class="insight-filters">
          <label>觀察分類<select v-model="categoryId" data-testid="insight-category"><option v-for="category in series?.categories" :key="category.id" :value="category.id">{{ category.label }}</option></select></label>
          <label>起始週<select v-model="fromWeek" aria-label="起始週"><option value="">最早週</option><option v-for="week in weeks" :key="week.start" :value="week.start">{{ formatWeekRange(week) }} · {{ insightWeekStatus(week) }}</option></select></label>
          <label>結束週<select v-model="toWeek" aria-label="結束週"><option value="">最新週</option><option v-for="week in weeks" :key="week.start" :value="week.start">{{ formatWeekRange(week) }} · {{ insightWeekStatus(week) }}</option></select></label>
          <button v-if="filtered" type="button" class="showcase-toolbar__button" @click="router.replace({ query: { category: categoryId } })">清除週次</button>
        </div>
        <article v-if="selectedTopic" class="insight-topic" data-testid="topic-insight">
          <h3>{{ selectedCategory?.label }}</h3>
          <p class="insight-caption">分析期間：{{ topicPeriod }} · 週次選單篩選下方統計與週報；此洞見保留上述分析期間。</p>
          <dl>
            <dt>內容轉變</dt><dd>{{ selectedTopic.change }}</dd>
            <dt>值得注意的訊號</dt><dd>{{ selectedTopic.signal }}</dd>
            <dt>後續觀察重點</dt><dd>{{ selectedTopic.watch }}</dd>
          </dl>
        </article>
        <p v-else class="state-panel">這個主題的跨週洞見尚未整理，可先查看單週回顧與統計依據。</p>
        <details class="insight-evidence" data-testid="topic-evidence">
          <summary>統計依據：來源數與每週占比</summary>
          <p class="insight-caption">占比以當週來源數為分母，用來輔助理解收錄組成與樣本量；數量不代表外部議題的重要性。</p>
          <section class="insight-stats" aria-label="收錄統計">
            <div><span>{{ filtered || series?.uniqueSourceCount === null ? '週次來源合計' : '全期不同來源' }}</span><strong>{{ filtered || series?.uniqueSourceCount === null ? totalSources : series?.uniqueSourceCount }}</strong><small>{{ filtered || series?.uniqueSourceCount === null ? '所選整週合計，包含跨週重現' : '同一影片在全期只計一次' }}</small></div>
            <div><span>摘要紀錄</span><strong>{{ totalRaw }}</strong><small>含同一來源的重複收錄</small></div>
            <div><span>可比較的完整週</span><strong>{{ completeWeeks.length }}<em> / {{ visibleWeeks.length }} 週</em></strong><small>排除首週部分資料與進行中週</small></div>
          </section>
          <label class="insight-toggle"><input v-model="includePartial" type="checkbox" data-testid="include-partial" />也顯示首週部分資料與進行中週</label>
          <template v-if="chartWeeks.length && selectedCategory">
            <InsightCategoryTrend :weeks="chartWeeks" :category="selectedCategory" />
            <div class="insight-table-wrap"><table class="insight-table"><caption>所有分類的每週占比</caption><thead><tr><th scope="col">分類</th><th v-for="week in chartWeeks" :key="week.start" scope="col">{{ formatWeekRange(week) }}</th></tr></thead><tbody><tr v-for="category in series?.categories" :key="category.id"><th scope="row">{{ category.label }}</th><td v-for="week in chartWeeks" :key="week.start">{{ categoryShare(week, category.id) === null ? '—' : `${categoryShare(week, category.id)?.toFixed(1)}%` }}</td></tr></tbody></table></div>
          </template>
          <p v-else class="state-panel">所選範圍沒有可比較的完整週。可勾選顯示部分週，或調整週次範圍。</p>
          <div v-if="changes.length && latest && previous" class="insight-changes">
            <p>{{ formatWeekRange(latest) }} 相較 {{ formatWeekRange(previous) }} · 占比變化</p>
            <div><span v-for="category in changes" :key="category.id">{{ category.label }}<strong>{{ category.change! > 0 ? '+' : '' }}{{ category.change?.toFixed(1) }} 個百分點</strong></span></div>
          </div>
        </details>
      </section>
      <section class="insight-week-section"><div class="insight-section-heading"><p class="hero__eyebrow">Week by Week</p><h2>每週內容回顧</h2></div>
        <div v-if="newestFirstWeeks.length" class="insight-week-grid"><WeeklyInsightCard v-for="week in newestFirstWeeks" :key="week.start" :week="week" :categories="series?.categories ?? []" /></div>
        <p v-else class="state-panel">沒有符合日期的週報，請調整篩選。</p>
      </section>
      <details class="insight-method"><summary>資料說明與更新方式</summary><p>每週從週日到週六，日期依資料收錄時間並按台灣時間分週。資料從 9/1 起，首週缺少 8/30、8/31；最後一週以查詢時間為準。</p><p>同週同一來源只計一次，跨週再次收錄仍計入該週。占比反映個人收錄題材，不能直接代表市場或產業趨勢。每週回顧經整理後更新，僅展示部分代表來源。</p></details>
    </template>
  </main>
</template>
