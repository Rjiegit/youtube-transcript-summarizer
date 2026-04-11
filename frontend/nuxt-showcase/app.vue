<script setup lang="ts">
useHead({
  titleTemplate: (titleChunk) => {
    if (!titleChunk) {
      return "影片知識庫 | nuxt-showcase";
    }

    if (titleChunk === "影片知識庫") {
      return `${titleChunk} | nuxt-showcase`;
    }

    return `${titleChunk} | 影片知識庫`;
  },
});
</script>

<template>
  <NuxtPage />
</template>
