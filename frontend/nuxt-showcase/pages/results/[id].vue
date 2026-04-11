<script setup lang="ts">
import { computed, watchEffect } from "vue";

import type { ShowcaseDetailResult } from "../../types/showcase";

const route = useRoute();
const resultId = String(route.params.id || "");

const { data, error, pending } = useFetch<ShowcaseDetailResult>(`/api/showcase/results/${resultId}`, {
  server: true,
  default: () => null,
});

const item = computed<ShowcaseDetailResult | null>(() => data.value ?? null);
const isLoading = computed(() => pending.value);
const fetchError = computed(() => error.value);
const isNotFound = computed(() => !isLoading.value && !fetchError.value && !item.value);

watchEffect(() => {
  if (isNotFound.value) {
    throw createError({
      statusCode: 404,
      statusMessage: "Showcase result not found.",
    });
  }
});

const errorMessage = computed(() => {
  if (!fetchError.value) {
    return "";
  }
  return fetchError.value.statusMessage || fetchError.value.message || "請稍後再試。";
});

const createdAtLabel = computed(() => {
  if (!item.value) {
    return "";
  }
  return new Date(item.value.created_at).toLocaleString("zh-TW", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
});

const durationLabel = computed(() => {
  if (item.value?.processing_duration == null) {
    return "";
  }
  return `${item.value.processing_duration.toFixed(1)}s`;
});
</script>

<template>
  <main class="showcase-shell">
    <section v-if="isLoading" class="state-panel">
      <p class="state-panel__title">載入展示資料中</p>
      <p class="state-panel__body">正在讀取詳細內容。</p>
    </section>

    <section v-else-if="fetchError" class="state-panel state-panel--error">
      <p class="state-panel__title">目前無法載入展示內容</p>
      <p class="state-panel__body">{{ errorMessage }}</p>
    </section>

    <article v-else-if="item" class="detail-panel">
      <div class="detail-panel__nav">
        <NuxtLink to="/" class="detail-panel__back-link">
          Back to Showcase
        </NuxtLink>
      </div>

      <div class="detail-panel__meta">
        <span>{{ createdAtLabel }}</span>
        <span v-if="durationLabel">{{ durationLabel }}</span>
      </div>

      <h1 class="detail-panel__title">{{ item?.title }}</h1>

      <div v-if="item?.source_url" class="detail-panel__actions">
        <a
          :href="item.source_url"
          target="_blank"
          rel="noreferrer"
          class="showcase-card__link"
        >
          Original Video
        </a>
      </div>

      <div class="detail-panel__summary">
        <p>{{ item?.content || item?.summary }}</p>
      </div>
    </article>
  </main>
</template>
