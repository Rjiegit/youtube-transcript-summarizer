<script setup lang="ts">
import { computed } from "vue";

import type { ShowcaseResult } from "../types/showcase";

const props = withDefaults(defineProps<{
  item: ShowcaseResult;
  isRead?: boolean;
}>(), {
  isRead: false,
});

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
</script>

<template>
  <article class="showcase-card" :class="{ 'showcase-card--read': isRead }">
    <NuxtLink :to="`/results/${item.id}`" class="showcase-card__main-link">
      <div class="showcase-card__meta">
        <span>{{ createdAtLabel }}</span>
        <span v-if="durationLabel">{{ durationLabel }}</span>
      </div>
      <div class="showcase-card__title-row">
        <h2 class="showcase-card__title">{{ item.title }}</h2>
        <span
          class="showcase-card__read-badge"
          :class="{ 'showcase-card__read-badge--visible': isRead }"
          :aria-hidden="isRead ? 'false' : 'true'"
        >
          Read
        </span>
      </div>
      <p v-if="item.summary" class="showcase-card__summary">{{ item.summary }}</p>
    </NuxtLink>
    <div v-if="item.source_url" class="showcase-card__links">
      <a
        :href="item.source_url"
        target="_blank"
        rel="noreferrer"
        class="showcase-card__link"
      >
        Original Video
      </a>
    </div>
  </article>
</template>
