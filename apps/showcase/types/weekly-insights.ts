export interface InsightCategory {
  id: string;
  label: string;
}

export interface InsightTopicTrack {
  id: string;
  label: string;
  categoryIds: string[];
  change: string;
  watch: string;
  observations: Array<{ week: string; summary: string }>;
}

export interface WeeklyInsightSummary {
  start: string;
  endExclusive: string;
  coverageStart: string;
  periodState: "open" | "closed";
  dataCompleteness: "complete" | "partial";
  title: string;
  summary: string;
  revision: number;
  asOf: string;
  metrics: {
    rawCount: number;
    sourceCount: number;
    newSourceCount: number;
    recurringSourceCount: number;
  };
  categories: Array<{ id: string; count: number }>;
}

export interface WeeklyInsight extends WeeklyInsightSummary {
  content: string;
  qualityNote: string;
  sources: Array<{ title: string; categoryId: string; sourceUrl: string }>;
}

export interface InsightSeries {
  topicTracks?: InsightTopicTrack[];
  topicInsights?: {
    fromWeek: string;
    toWeek: string;
    items: Array<{ categoryId: string; change: string; signal: string; watch: string }>;
  } | null;
  collectionStart: string;
  asOf: string;
  timezone: string;
  weekConvention: string;
  dedupPolicy: string;
  analysisVersion: string;
  uniqueSourceCount: number | null;
  categories: InsightCategory[];
  overview: string;
}

export interface InsightListResponse {
  series: InsightSeries;
  weeks: WeeklyInsightSummary[];
}

export interface InsightDetailResponse {
  series: InsightSeries;
  week: WeeklyInsight;
  previous: string | null;
  next: string | null;
}
