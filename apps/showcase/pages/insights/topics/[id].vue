<script setup lang="ts">
import { computed } from "vue";
import MarkdownContent from "../../../components/MarkdownContent.vue";
import type { TopicReadingResponse } from "../../../types/weekly-insights";
import { formatTaipeiDateTime } from "../../../utils/datetime";
import { resolveSiteUrl } from "../../../utils/site-url";

const route = useRoute();
const id = computed(() => String(route.params.id || ""));
const { data, error } = await useFetch<TopicReadingResponse>(() => `/api/showcase/topics/${encodeURIComponent(id.value)}`, { server: true });
if (error.value || !data.value) throw createError({ statusCode: error.value?.statusCode || 404, statusMessage: "找不到這份專題" });
const topic = computed(() => data.value!.topic);
const labels = computed(() => data.value!.categories.filter((category) => topic.value.categoryIds.includes(category.id)));
const siteUrl = resolveSiteUrl(useRuntimeConfig().public.siteUrl);
useHead(() => ({
  title: topic.value.title,
  link: [{ rel: "canonical", href: `${siteUrl}/insights/topics/${topic.value.id}` }],
  meta: [
    { name: "description", content: topic.value.summary },
    { property: "og:title", content: topic.value.title },
    { property: "og:description", content: topic.value.summary },
    { property: "og:type", content: "article" },
    { property: "og:url", content: `${siteUrl}/insights/topics/${topic.value.id}` },
    { property: "og:image", content: `${siteUrl}/share-preview.png` },
    { name: "twitter:card", content: "summary_large_image" },
    { name: "twitter:title", content: topic.value.title },
    { name: "twitter:image", content: `${siteUrl}/share-preview.png` },
  ],
}));
</script>

<template>
  <main v-if="data" class="insight-shell insight-shell--detail topic-reading-detail">
    <nav class="insight-nav"><NuxtLink to="/insights">← 專題與每週回顧</NuxtLink><span>跨影片整合閱讀</span></nav>
    <header class="insight-hero insight-hero--detail">
      <p class="hero__eyebrow">{{ labels.map(category => category.label).join(' · ') }}</p>
      <h1>{{ topic.title }}</h1><p>{{ topic.summary }}</p>
      <div class="topic-reading-card__meta"><span class="topic-reading-badge">{{ topic.revision === 1 ? '首次整理' : '內容更新' }}</span>
        <span>{{ formatTaipeiDateTime(topic.updatedAt) }} · 第 {{ topic.revision }} 版</span></div>
    </header>
    <aside class="topic-reading-context" aria-label="閱讀範圍與限制">
      <p><strong>適合：</strong>{{ topic.relevance }}</p>
      <p><strong>判讀限制：</strong>{{ topic.limitation }}</p>
      <p class="insight-caption">{{ topic.coverageStart }}–{{ topic.coverageThrough }} · {{ topic.coverageMode === 'selected-sources' ? '選定來源試作' : '範圍內完整整理' }} · {{ topic.sourceCount }} 個影片參考</p>
      <p class="insight-caption">日期依收錄時間；影片數不代表獨立驗證數，閱讀本頁不會將相關影片標成已讀。</p>
    </aside>
    <section class="insight-panel topic-reading-update" aria-labelledby="topic-update-heading">
      <h2 id="topic-update-heading">{{ topic.revision === 1 ? '這份內容的整理基準' : '相較前版新增什麼' }}</h2>
      <p>{{ topic.changes }}</p>
      <a :href="topic.prioritySourceUrl" target="_blank" rel="noopener noreferrer" class="topic-reading-link">想深入時，優先看這支影片 ↗</a>
    </section>
    <section class="insight-panel insight-editorial" aria-label="整合理解"><MarkdownContent :source="topic.intro" /></section>
    <section v-for="(section, index) in topic.sections" :key="index" class="insight-panel insight-editorial">
      <h2>{{ section.heading }}</h2><MarkdownContent :source="section.content" />
    </section>
    <details class="insight-panel insight-editorial topic-reading-sources" data-testid="topic-sources">
      <summary>{{ topic.sources.heading }} · 優先來源與可略過的重複介紹</summary>
      <MarkdownContent :source="topic.sources.content" />
    </details>
    <nav class="insight-pagination" aria-label="其他閱讀"><NuxtLink to="/insights">← 回到分類專題與每週回顧</NuxtLink></nav>
  </main>
</template>
