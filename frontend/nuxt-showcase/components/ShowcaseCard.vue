<script setup lang="ts">
import { computed } from "vue";

import type { ShowcaseResult } from "../types/showcase";

const props = defineProps<{
  item: ShowcaseResult;
}>();

const createdAtLabel = computed(() => new Date(props.item.created_at).toLocaleDateString("zh-TW", {
  year: "numeric",
  month: "short",
  day: "numeric",
}));

const durationLabel = computed(() => {
  if (props.item.processing_duration == null) {
    return null;
  }
  return `${props.item.processing_duration.toFixed(1)}s`;
});

const summaryPreview = computed(() => {
  const summary = (props.item.summary || "").trim();
  if (!summary) {
    return "這筆結果尚未提供摘要內容。";
  }
  if (summary.length <= 180) {
    return summary;
  }
  return `${summary.slice(0, 180).trim()}...`;
});
</script>

<template>
  <article class="showcase-card">
    <div class="showcase-card__meta">
      <span>{{ createdAtLabel }}</span>
      <span v-if="durationLabel">{{ durationLabel }}</span>
    </div>
    <h2 class="showcase-card__title">{{ item.title }}</h2>
    <p class="showcase-card__summary">{{ summaryPreview }}</p>
    <div class="showcase-card__links">
      <a
        v-if="item.source_url"
        :href="item.source_url"
        target="_blank"
        rel="noreferrer"
        class="showcase-card__link"
      >
        Original Video
      </a>
      <a
        v-if="item.notion_url"
        :href="item.notion_url"
        target="_blank"
        rel="noreferrer"
        class="showcase-card__link"
      >
        Open in Notion
      </a>
    </div>
  </article>
</template>
