import { buildInsightRegistry } from "./weekly-insights-content.mjs";
const content = await buildInsightRegistry();
console.log(`Weekly insights: validated and bundled ${content.weeks.length} reports.`);
