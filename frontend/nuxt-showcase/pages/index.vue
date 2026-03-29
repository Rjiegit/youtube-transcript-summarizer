<script setup lang="ts">
import ShowcaseCard from "../components/ShowcaseCard.vue";
import type { ShowcaseApiResponse } from "../types/showcase";

const { data, pending, error } = await useFetch<ShowcaseApiResponse>("/api/showcase/results", {
  server: true,
  default: () => ({
    items: [],
    generated_at: "",
    cache_ttl_seconds: 3600,
  }),
});

const items = computed(() => data.value?.items ?? []);
const errorMessage = computed(() => {
  if (!error.value) {
    return "";
  }
  return error.value.statusMessage || error.value.message || "請稍後再試。";
});
const lastUpdatedLabel = computed(() => {
  if (!data.value?.generated_at) {
    return "";
  }
  return new Date(data.value.generated_at).toLocaleString("zh-TW", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
});
</script>

<template>
  <main class="showcase-shell">
    <section class="hero">
      <p class="hero__eyebrow">YouTube Whisper Showcase</p>
      <h1 class="hero__title">最新的 YouTube 重點摘要</h1>
      <p class="hero__body">
        這裡收錄最近公開的 YouTube 摘要內容，展示我如何把長影片整理成可快速閱讀、分享與回頭查找的知識資產。
      </p>
      <div class="hero__stats">
        <div>
          <span class="hero__stat-label">Results</span>
          <strong class="hero__stat-value">{{ items.length }}</strong>
        </div>
        <div v-if="lastUpdatedLabel">
          <span class="hero__stat-label">Updated</span>
          <strong class="hero__stat-value">{{ lastUpdatedLabel }}</strong>
        </div>
      </div>
    </section>

    <section v-if="pending" class="state-panel">
      <p class="state-panel__title">載入展示資料中</p>
      <p class="state-panel__body">正在讀取最近的完成結果。</p>
    </section>

    <section v-else-if="error" class="state-panel state-panel--error">
      <p class="state-panel__title">目前無法載入展示資料</p>
      <p class="state-panel__body">
        {{ errorMessage }}
      </p>
      <p class="state-panel__body">
        可直接檢查
        <a href="/api/showcase/diagnostics" target="_blank" rel="noreferrer">/api/showcase/diagnostics</a>
        確認 server 端實際讀到哪些 env，或打開
        <a href="/api/showcase/health" target="_blank" rel="noreferrer">/api/showcase/health</a>
        直接驗證 Notion 查詢。
      </p>
    </section>

    <section v-else-if="items.length === 0" class="state-panel">
      <p class="state-panel__title">還沒有可展示的結果</p>
      <p class="state-panel__body">Notion database 目前沒有 `Completed` 項目。</p>
    </section>

    <section v-else class="showcase-grid">
      <ShowcaseCard
        v-for="item in items"
        :key="item.id"
        :item="item"
      />
    </section>
  </main>
</template>
