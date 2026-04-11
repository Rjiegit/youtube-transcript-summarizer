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
});
</script>

<template>
  <NuxtPage />
</template>
