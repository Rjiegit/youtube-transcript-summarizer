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
});
</script>

<template>
  <NuxtPage />
</template>
