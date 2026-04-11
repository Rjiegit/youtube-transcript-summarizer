<script setup lang="ts">
useHead({
  titleTemplate: (titleChunk) => {
    if (!titleChunk) {
      return "YouTube 知識摘要 | nuxt-showcase";
    }

    if (titleChunk === "YouTube 知識摘要") {
      return `${titleChunk} | nuxt-showcase`;
    }

    return `${titleChunk} | YouTube 知識摘要`;
  },
});
</script>

<template>
  <NuxtPage />
</template>
