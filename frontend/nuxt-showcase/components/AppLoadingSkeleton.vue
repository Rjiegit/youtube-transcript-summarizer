<script setup lang="ts">
defineProps<{
  variant: "list" | "detail";
}>();
</script>

<template>
  <div
    class="app-loading-skeleton"
    :class="`app-loading-skeleton--${variant}`"
    data-testid="app-loading-overlay"
    role="status"
    aria-live="polite"
  >
    <span class="app-loading-skeleton__sr-only">頁面載入中</span>

    <div v-if="variant === 'list'" class="app-loading-skeleton__frame" aria-hidden="true">
      <section class="app-loading-skeleton__list-hero">
        <span class="app-loading-skeleton__line app-loading-skeleton__line--eyebrow"></span>
        <span class="app-loading-skeleton__line app-loading-skeleton__line--hero-title"></span>
        <span class="app-loading-skeleton__line app-loading-skeleton__line--hero-body"></span>
      </section>
      <section class="app-loading-skeleton__list-toolbar">
        <span class="app-loading-skeleton__control"></span>
        <span class="app-loading-skeleton__search"></span>
      </section>
      <section class="app-loading-skeleton__grid">
        <article v-for="index in 3" :key="index" class="app-loading-skeleton__card">
          <span class="app-loading-skeleton__line app-loading-skeleton__line--meta"></span>
          <span class="app-loading-skeleton__line app-loading-skeleton__line--card-title"></span>
          <span class="app-loading-skeleton__line app-loading-skeleton__line--body"></span>
          <span class="app-loading-skeleton__line app-loading-skeleton__line--body-short"></span>
        </article>
      </section>
    </div>

    <div v-else class="app-loading-skeleton__frame app-loading-skeleton__detail" aria-hidden="true">
      <span class="app-loading-skeleton__detail-nav"></span>
      <span class="app-loading-skeleton__line app-loading-skeleton__line--meta"></span>
      <span class="app-loading-skeleton__detail-title"></span>
      <div class="app-loading-skeleton__detail-copy">
        <span
          v-for="index in 6"
          :key="index"
          class="app-loading-skeleton__detail-line"
          :class="{ 'app-loading-skeleton__detail-line--short': index === 3 || index === 6 }"
        ></span>
      </div>
      <span class="app-loading-skeleton__detail-media"></span>
    </div>
  </div>
</template>
