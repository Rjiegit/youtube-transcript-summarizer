<script setup lang="ts">
import { computed } from "vue";

import { splitTitleSearch } from "../utils/title-search";

const props = defineProps<{ title: string; query: string }>();
const parts = computed(() => splitTitleSearch(props.title, props.query));
</script>

<template>
  <span><template v-for="(part, index) in parts" :key="index"><mark
    v-if="part.matched"
    class="showcase-title-highlight"
  >{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></span>
</template>
