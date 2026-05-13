<script setup lang="ts">
import { computed } from "vue";

import type { ShowcaseResult } from "../types/showcase";
import { formatTaipeiDate } from "../utils/datetime";

const props = withDefaults(defineProps<{
  item: ShowcaseResult;
  isRead?: boolean;
}>(), {
  isRead: false,
});

const emit = defineEmits<{
  (event: "mark-read"): void;
}>();

function handleMainClick(navigate: (event?: MouseEvent) => Promise<void> | void, event: MouseEvent) {
  emit("mark-read");
  void navigate(event);
}

const createdAtLabel = computed(() => formatTaipeiDate(props.item.created_at));

const durationLabel = computed(() => {
  if (props.item.processing_duration == null) {
    return null;
  }
  return `${props.item.processing_duration.toFixed(1)}s`;
});
</script>

<template>
  <article class="showcase-card" :class="{ 'showcase-card--read': isRead }">
    <NuxtLink
      :to="`/results/${item.id}`"
      custom
      v-slot="{ href, navigate }"
    >
      <a
        :href="href"
        class="showcase-card__main-link"
        @click="handleMainClick(navigate, $event)"
      >
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
            已讀
          </span>
        </div>
        <p v-if="item.summary" class="showcase-card__summary">{{ item.summary }}</p>
      </a>
    </NuxtLink>
    <div v-if="item.source_url" class="showcase-card__links">
      <a
        :href="item.source_url"
        target="_blank"
        rel="noreferrer"
        class="showcase-card__link"
      >
        原始影片
      </a>
    </div>
  </article>
</template>
