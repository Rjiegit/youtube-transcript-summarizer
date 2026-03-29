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
      <h1 class="hero__title">最近 100 筆完成的轉錄與摘要成果</h1>
      <p class="hero__body">
        這個頁面從 Notion 讀取已完成的處理結果，展示這個 side project 如何把 YouTube 影片轉成可快速瀏覽的摘要知識庫。
      </p>
      <div class="hero__stats">
        <div>
          <span class="hero__stat-label">Results</span>
          <strong class="hero__stat-value">{{ items.length }}</strong>
        </div>
        <div>
          <span class="hero__stat-label">Cache</span>
          <strong class="hero__stat-value">{{ data?.cache_ttl_seconds ?? 3600 }}s</strong>
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
        {{ error.statusMessage || "請稍後再試，或檢查 Vercel / Notion 環境變數設定。" }}
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
