<script setup lang="ts">
import { computed } from "vue";
import type { InsightCategory, WeeklyInsightSummary } from "../types/weekly-insights";
import { categoryShare, formatWeekRange, insightWeekStatus } from "../utils/weekly-insights";

const props = defineProps<{ week: WeeklyInsightSummary; categories: InsightCategory[] }>();
const leadingCategories = computed(() => [...props.week.categories].sort((a, b) => b.count - a.count).filter((item) => item.count > 0).slice(0, 3));
const label = (id: string) => props.categories.find((category) => category.id === id)?.label ?? id;
</script>

<template>
  <NuxtLink :to="`/insights/${week.start}`" class="insight-week-card">
    <div class="insight-week-card__meta"><span>{{ formatWeekRange(week) }} · 日–六</span><span>{{ insightWeekStatus(week) }}</span></div>
    <h3>{{ week.title }}</h3>
    <p>{{ week.summary }}</p>
    <ul>
      <li v-for="category in leadingCategories" :key="category.id">
        <span>{{ label(category.id) }}</span><strong>{{ categoryShare(week, category.id)?.toFixed(1) }}%</strong>
      </li>
    </ul>
    <div class="insight-week-card__footer"><span>{{ week.metrics.sourceCount }} 個來源</span><span>閱讀本週回顧 ↗</span></div>
  </NuxtLink>
</template>
