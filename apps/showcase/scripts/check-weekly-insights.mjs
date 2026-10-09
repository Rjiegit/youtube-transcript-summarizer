import { loadInsightContent } from "./weekly-insights-content.mjs";
const content = await loadInsightContent();
console.log(`Weekly insights: ${content.weeks.length} reports validated.`);
