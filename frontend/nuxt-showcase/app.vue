<script setup lang="ts">
import { computed } from "vue";

const runtimeConfig = useRuntimeConfig();
const publicConfig = runtimeConfig.public || {};
const buildDate = computed(() => normalizeVersionPart(publicConfig.buildDate) || "local");
const commitSha = computed(() => normalizeVersionPart(publicConfig.commitSha));
const shortCommitSha = computed(() => commitSha.value.slice(0, 7) || "local");
const appVersionLabel = computed(() => `${buildDate.value} · ${shortCommitSha.value}`);
const appVersionTitle = computed(() => {
  if (!commitSha.value) {
    return `建置版本：${buildDate.value}，本機或未提供 commit`;
  }

  return `建置版本：${buildDate.value}，commit ${commitSha.value}`;
});

function normalizeVersionPart(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

useHead({
  titleTemplate: (titleChunk) => {
    if (!titleChunk) {
      return "影片知識庫";
    }

    if (titleChunk === "影片知識庫") {
      return titleChunk;
    }

    return `${titleChunk} | 影片知識庫`;
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
      content: "把影片內容整理成更容易理解、快速吸收、方便搜尋，並能隨時回顧與再利用的知識資料。",
    },
    { property: "og:site_name", content: "影片知識庫" },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary" },
  ],
});
</script>

<template>
  <div class="app-frame">
    <NuxtPage />
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
