<script setup lang="ts">
import { computed, onBeforeUnmount } from "vue";

import { useAppLoading } from "./composables/useAppLoading";

const runtimeConfig = useRuntimeConfig();
const publicConfig = runtimeConfig.public || {};
const buildDate = computed(() => normalizeVersionPart(publicConfig.buildDate) || "local");
const commitSha = computed(() => normalizeVersionPart(publicConfig.commitSha));
const shortCommitSha = computed(() => commitSha.value.slice(0, 7) || "local");
const appVersionLabel = computed(() => `${buildDate.value} · ${shortCommitSha.value}`);
const { finish: finishLoading, isLoading, start: startLoading } = useAppLoading();
const nuxtApp = useNuxtApp();
const stopLoadingStartHook = nuxtApp.hook("page:loading:start", () => {
  startLoading("route-navigation");
});
const stopLoadingEndHook = nuxtApp.hook("page:loading:end", () => {
  finishLoading("route-navigation");
});
const appVersionTitle = computed(() => {
  if (!commitSha.value) {
    return `建置版本：${buildDate.value}，本機或未提供 commit`;
  }

  return `建置版本：${buildDate.value}，commit ${commitSha.value}`;
});

function normalizeVersionPart(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

onBeforeUnmount(() => {
  stopLoadingStartHook();
  stopLoadingEndHook();
  finishLoading("route-navigation");
});

useHead({
  titleTemplate: (titleChunk) => {
    if (!titleChunk) {
      return "影片筆記庫";
    }

    if (titleChunk === "影片筆記庫") {
      return titleChunk;
    }

    return `${titleChunk} | 影片筆記庫`;
  },
  link: [
    { rel: "stylesheet", href: "/showcase.css" },
    { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
    { rel: "shortcut icon", type: "image/x-icon", href: "/favicon.ico" },
    { rel: "apple-touch-icon", sizes: "180x180", href: "/apple-touch-icon.png" },
    { rel: "manifest", href: "/site.webmanifest" },
  ],
  meta: [
    {
      name: "description",
      content: "收藏從影片整理出的重點筆記",
    },
    { property: "og:site_name", content: "影片筆記庫" },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary" },
  ],
});
</script>

<template>
  <div class="app-frame">
    <div
      v-show="isLoading"
      class="app-loading-progress"
      data-testid="app-loading-progress"
      role="progressbar"
      aria-label="頁面載入中"
    ></div>
    <div
      class="app-frame__content"
      :class="{ 'app-frame__content--loading': isLoading }"
      :aria-busy="isLoading ? 'true' : 'false'"
      data-testid="app-content"
    >
      <NuxtPage />
    </div>
    <footer class="site-footer" aria-label="版本資訊">
      <span
        class="site-footer__version"
        data-testid="app-version"
        :title="appVersionTitle"
      >
        {{ appVersionLabel }}
      </span>
    </footer>
  </div>
</template>
