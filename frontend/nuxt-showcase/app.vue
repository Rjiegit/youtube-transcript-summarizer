<script setup lang="ts">
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
  <NuxtPage />
</template>
