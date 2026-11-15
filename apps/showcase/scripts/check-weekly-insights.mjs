import { loadInsightContent } from "./weekly-insights-content.mjs";
import { loadTopicReadings } from "./topic-readings-content.mjs";
const content = await loadInsightContent();
const topics = await loadTopicReadings(undefined, undefined, content.series.categories);
console.log(`Weekly insights: ${content.weeks.length} reports and ${topics.length} topics validated.`);
