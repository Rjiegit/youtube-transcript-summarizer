<script setup lang="ts">
import { computed } from "vue";
import type { InsightCategory, WeeklyInsightSummary } from "../types/weekly-insights";
import { categoryShare, formatWeekRange, insightWeekStatus } from "../utils/weekly-insights";

const props = defineProps<{ weeks: WeeklyInsightSummary[]; category: InsightCategory }>();
const values = computed(() => props.weeks.map((week) => ({ week, share: categoryShare(week, props.category.id) })));
</script>

<template>
  <div class="insight-chart" :aria-label="`${category.label}每週占比，數值表如下`" role="img">
    <div class="insight-chart__axis" aria-hidden="true"><span>100%</span><span>50%</span><span>0%</span></div>
    <div class="insight-chart__plot">
      <div v-for="item in values" :key="item.week.start" class="insight-chart__column">
        <div class="insight-chart__track">
          <div class="insight-chart__bar" :class="{ 'insight-chart__bar--partial': insightWeekStatus(item.week) !== '完整週' }"
            :style="{ height: `${item.share ?? 0}%` }">
            <span>{{ item.share === null ? '—' : `${item.share.toFixed(1)}%` }}</span>
          </div>
        </div>
        <span class="insight-chart__label">{{ formatWeekRange(item.week) }}</span>
        <span class="insight-chart__status">{{ insightWeekStatus(item.week) === '完整週' ? '完整週' : insightWeekStatus(item.week) }}</span>
      </div>
    </div>
  </div>
</template>
