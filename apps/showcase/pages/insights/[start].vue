<script setup lang="ts">
import { computed } from "vue";
import MarkdownContent from "../../components/MarkdownContent.vue";
import type { InsightDetailResponse } from "../../types/weekly-insights";
import { categoryShare, comparableWeeks, formatWeekRange, insightWeekStatus } from "../../utils/weekly-insights";
import { formatTaipeiDateTime } from "../../utils/datetime";
import { resolveSiteUrl } from "../../utils/site-url";

const route = useRoute();
const start = computed(() => String(route.params.start || ""));
const { data, error } = await useFetch<InsightDetailResponse>(() => `/api/showcase/insights/${encodeURIComponent(start.value)}`, { server: true });
if (error.value || !data.value) throw createError({ statusCode: error.value?.statusCode || 404, statusMessage: "找不到這週的回顧" });
const week = computed(() => data.value!.week);
const series = computed(() => data.value!.series);
const siteUrl = resolveSiteUrl(useRuntimeConfig().public.siteUrl);
const categoryLabel = (id: string) => series.value.categories.find((category) => category.id === id)?.label ?? id;
const counts = computed(() => [...week.value.categories].sort((a, b) => b.count - a.count));
useHead(() => ({
  title: `${formatWeekRange(week.value)} 每週回顧：${week.value.title}`,
  link: [{ rel: "canonical", href: `${siteUrl}/insights/${week.value.start}` }],
  meta: [
    { name: "description", content: week.value.summary },
    { property: "og:title", content: `${formatWeekRange(week.value)}｜${week.value.title}` },
    { property: "og:description", content: week.value.summary },
    { property: "og:type", content: "article" },
    { property: "og:url", content: `${siteUrl}/insights/${week.value.start}` },
    { property: "og:image", content: `${siteUrl}/share-preview.png` },
    { name: "twitter:card", content: "summary_large_image" },
    { name: "twitter:title", content: week.value.title },
    { name: "twitter:description", content: week.value.summary },
    { name: "twitter:image", content: `${siteUrl}/share-preview.png` },
  ],
}));
</script>

<template>
  <main class="insight-shell insight-shell--detail">
    <nav class="insight-nav"><NuxtLink to="/insights">← 每週回顧</NuxtLink><span>週日 — 週六</span></nav>
    <header class="insight-hero insight-hero--detail">
      <p class="hero__eyebrow">{{ formatWeekRange(week) }} · {{ insightWeekStatus(week) }}</p>
      <h1>{{ week.title }}</h1><p>{{ week.summary }}</p>
      <p class="insight-caption">資料截至 {{ formatTaipeiDateTime(week.asOf) }} · 第 {{ week.revision }} 版</p>
    </header>
    <aside v-if="!comparableWeeks([week]).length" class="insight-notice" data-testid="partial-week-notice">
      {{ week.coverageStart !== week.start ? `本週資料從 ${week.coverageStart} 開始，未涵蓋完整七天。` : '' }}
      {{ week.periodState === 'open' ? '這週尚未結束，目前數量不能與完整週直接比較。' : '' }}
      {{ week.dataCompleteness === 'partial' ? '資料尚未全部取得，本週暫不納入趨勢比較。' : '' }}
    </aside>
    <section class="insight-stats" aria-label="本週收錄統計">
      <div><span>不同來源</span><strong>{{ week.metrics.sourceCount }}</strong><small>{{ week.metrics.rawCount }} 筆原始摘要紀錄</small></div>
      <div><span>系列內首次收錄</span><strong>{{ week.metrics.newSourceCount }}</strong><small>從 {{ series.collectionStart }} 起首次出現</small></div>
      <div><span>跨週再次出現</span><strong>{{ week.metrics.recurringSourceCount }}</strong><small>同週重複已去除</small></div>
    </section>
    <section class="insight-panel insight-editorial"><MarkdownContent :source="week.content" /></section>
    <section class="insight-panel"><div class="insight-section-heading"><p class="hero__eyebrow">Topic Breakdown</p><h2>本週分類</h2></div>
      <div class="insight-breakdown"><div v-for="category in counts" :key="category.id"><span>{{ categoryLabel(category.id) }}</span><div class="insight-breakdown__track"><span :style="{ width: `${categoryShare(week, category.id) ?? 0}%` }"></span></div><strong>{{ category.count }} 個 · {{ categoryShare(week, category.id) === null ? '—' : `${categoryShare(week, category.id)?.toFixed(1)}%` }}</strong></div></div>
    </section>
    <section v-if="week.sources.length" class="insight-week-section"><div class="insight-section-heading"><p class="hero__eyebrow">Source Notes</p><h2>代表來源</h2><p>本週的部分文章，點選可查看原始影片。</p></div><div class="insight-source-grid"><a v-for="source in week.sources" :key="source.sourceUrl" :href="source.sourceUrl" target="_blank" rel="noopener noreferrer"><span>{{ categoryLabel(source.categoryId) }}</span><h3>{{ source.title }}</h3><small>查看影片 ↗</small></a></div></section>
    <details class="insight-method"><summary>資料說明</summary><p>{{ week.qualityNote }}</p><p>一週從週日到週六；同週來源去重，跨週重現保留。不完整觀察週暫不納入完整週比較。</p></details>
    <nav class="insight-pagination" aria-label="其他週報"><NuxtLink v-if="data?.previous" :to="`/insights/${data.previous}`">← 上一週</NuxtLink><NuxtLink to="/insights">全部週報</NuxtLink><NuxtLink v-if="data?.next" :to="`/insights/${data.next}`">下一週 →</NuxtLink></nav>
  </main>
</template>
