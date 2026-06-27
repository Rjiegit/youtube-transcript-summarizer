<script setup lang="ts">
import { computed, watchEffect } from "vue";

import MarkdownContent from "../../components/MarkdownContent.vue";
import { useReadResults } from "../../composables/useReadResults";
import type { ShowcaseDetailResult } from "../../types/showcase";
import { formatTaipeiDateTime } from "../../utils/datetime";
import { getResultReadKey } from "../../utils/showcase";

const route = useRoute();
const resultId = String(route.params.id || "");

const { data, error, pending } = useFetch<ShowcaseDetailResult>(`/api/showcase/results/${resultId}`, {
  server: true,
  default: () => null,
});

const item = computed<ShowcaseDetailResult | null>(() => data.value ?? null);
const { markManyAsRead } = useReadResults();
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

watchEffect(() => {
  if (typeof window !== "undefined" && !isLoading.value && !fetchError.value && item.value?.id) {
    markManyAsRead([item.value.id, getResultReadKey(item.value)]);
  }
});

const errorMessage = computed(() => {
  if (!fetchError.value) {
    return "";
  }
  return fetchError.value.statusMessage || fetchError.value.message || "請稍後再試。";
});

const pageTitle = computed(() => {
  if (isLoading.value) {
    return "載入中…";
  }

  if (fetchError.value) {
    return "載入失敗";
  }

  if (item.value?.title) {
    return item.value.title;
  }

  return "找不到內容";
});

function compactMetaDescription(value: string | null | undefined): string {
  const compactedValue = stripMarkdownSyntax(value || "").replace(/\s+/g, " ").trim();
  if (!compactedValue) {
    return "把影片內容整理成更容易理解、快速吸收、方便搜尋，並能隨時回顧與再利用的知識資料。";
  }

  return compactedValue.length > 160 ? `${compactedValue.slice(0, 157)}...` : compactedValue;
}

function stripMarkdownSyntax(value: string): string {
  return value
    .replace(/```[a-z0-9_-]*\n([\s\S]*?)```/gi, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s{0,3}>\s?/gm, "")
    .replace(/^\s*[-*+]\s+\[[ xX]\]\s+/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/[*~]+/g, "")
    .replace(/\\([\\`*_{}[\]()#+.!|>-])/g, "$1");
}

const pageDescription = computed(() => compactMetaDescription(item.value?.summary || item.value?.content));

useHead({
  title: pageTitle,
  meta: [
    { name: "description", content: pageDescription.value },
    { property: "og:title", content: pageTitle.value },
    { property: "og:description", content: pageDescription.value },
    { property: "og:type", content: "article" },
    { name: "twitter:card", content: "summary" },
    { name: "twitter:title", content: pageTitle.value },
    { name: "twitter:description", content: pageDescription.value },
  ],
});

const createdAtLabel = computed(() => {
  return formatTaipeiDateTime(item.value?.created_at);
});

const durationLabel = computed(() => {
  if (item.value?.processing_duration == null) {
    return "";
  }
  return `${item.value.processing_duration.toFixed(1)}s`;
});

function getYoutubeVideoId(sourceUrl: string | null | undefined): string | null {
  if (!sourceUrl) {
    return null;
  }

  try {
    const url = new URL(sourceUrl);
    const hostname = url.hostname.toLowerCase();

    if (hostname === "youtu.be") {
      const videoId = url.pathname.split("/").filter(Boolean)[0];
      return videoId || null;
    }

    if (hostname === "www.youtube.com" || hostname === "youtube.com" || hostname === "m.youtube.com") {
      const videoId = url.searchParams.get("v");
      return videoId || null;
    }
  } catch {
    return null;
  }

  return null;
}

const youtubeVideoId = computed(() => getYoutubeVideoId(item.value?.source_url));
const youtubeEmbedUrl = computed(() => {
  if (!youtubeVideoId.value) {
    return "";
  }

  return `https://www.youtube-nocookie.com/embed/${youtubeVideoId.value}`;
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
          返回列表
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
          原始影片
        </a>
      </div>

      <div class="detail-panel__summary" data-testid="detail-summary">
        <MarkdownContent :source="item?.content || item?.summary || ''" />
      </div>

      <section
        v-if="youtubeEmbedUrl"
        class="detail-panel__video"
        data-testid="detail-video"
      >
        <h2 class="detail-panel__section-title">觀看原始影片</h2>
        <div class="detail-panel__video-frame">
          <iframe
            :src="youtubeEmbedUrl"
            :title="`${item?.title} YouTube video`"
            loading="lazy"
            referrerpolicy="strict-origin-when-cross-origin"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen
          />
        </div>
      </section>
    </article>
  </main>
</template>
