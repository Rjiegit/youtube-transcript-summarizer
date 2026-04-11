<script setup lang="ts">
import { computed } from "vue";

import ShowcaseCard from "../components/ShowcaseCard.vue";
import { useReadResults } from "../composables/useReadResults";
import type { ShowcaseApiResponse } from "../types/showcase";
import { formatTaipeiDateTime } from "../utils/datetime";

const { data, pending, error } = await useFetch<ShowcaseApiResponse>("/api/showcase/results", {
  server: true,
  default: () => ({
    items: [],
    generated_at: "",
    cache_ttl_seconds: 3600,
  }),
});

useHead({
  title: "影片知識庫",
});

const items = computed(() => data.value?.items ?? []);
const { isRead, isReady, markAsRead } = useReadResults();
const skeletonItems = computed(() => Array.from({ length: Math.max(items.value.length, 3) }, (_, index) => index));
const errorMessage = computed(() => {
  if (!error.value) {
    return "";
  }
  return error.value.statusMessage || error.value.message || "請稍後再試。";
});
const lastUpdatedLabel = computed(() => {
  return formatTaipeiDateTime(data.value?.generated_at);
});
</script>

<template>
  <main class="showcase-shell">
    <section class="hero">
      <p class="hero__eyebrow">Video Knowledge Index</p>
      <h1 class="hero__title">影片知識庫</h1>
      <p class="hero__body">
        把影片內容整理成更容易理解、快速吸收、方便搜尋，並能隨時回顧與再利用的知識資料。
      </p>
      <div class="hero__stats">
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

    <ClientOnly v-else>
      <section v-if="!isReady" class="showcase-grid showcase-grid--skeleton" aria-label="同步已讀狀態中">
        <article
          v-for="index in skeletonItems"
          :key="`skeleton-${index}`"
          class="showcase-skeleton-card"
          aria-hidden="true"
        >
          <div class="showcase-skeleton-card__meta"></div>
          <div class="showcase-skeleton-card__title"></div>
          <div class="showcase-skeleton-card__summary"></div>
          <div class="showcase-skeleton-card__summary showcase-skeleton-card__summary--short"></div>
        </article>
      </section>

      <section v-else class="showcase-grid">
        <ShowcaseCard
          v-for="item in items"
          :key="item.id"
          :item="item"
          :is-read="isRead(item.id)"
          @mark-read="markAsRead(item.id)"
        />
      </section>

      <template #fallback>
        <section class="showcase-grid showcase-grid--skeleton" aria-label="同步已讀狀態中">
          <article
            v-for="index in skeletonItems"
            :key="`fallback-skeleton-${index}`"
            class="showcase-skeleton-card"
            aria-hidden="true"
          >
            <div class="showcase-skeleton-card__meta"></div>
            <div class="showcase-skeleton-card__title"></div>
            <div class="showcase-skeleton-card__summary"></div>
            <div class="showcase-skeleton-card__summary showcase-skeleton-card__summary--short"></div>
          </article>
        </section>
      </template>
    </ClientOnly>
  </main>
</template>
