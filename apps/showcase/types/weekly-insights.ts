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

export interface InsightHighlights {
  fromWeek: string;
  toWeek: string;
  updatedAt: string;
  emptyReason?: string;
  items: Array<{
    id: string;
    title: string;
    change: string;
    relevance: string;
    limitation: string;
    nextStep: string;
    evidence: Array<{ week: string; sourceUrl: string; title: string; observation: string }>;
  }>;
}

export interface InsightSeries {
  highlights?: InsightHighlights | null;
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
  topics?: TopicReadingSummary[];
}

export interface InsightDetailResponse {
  series: InsightSeries;
  week: WeeklyInsight;
  previous: string | null;
  next: string | null;
}

export interface TopicReadingSummary {
  id: string;
  title: string;
  summary: string;
  relevance: string;
  limitation: string;
  changes: string;
  categoryIds: string[];
  revision: number;
  analysisVersion: string;
  updatedAt: string;
  coverageStart: string;
  coverageThrough: string;
  coverageMode: "selected-sources" | "full-scope";
  sourceCount: number;
  prioritySourceUrl: string;
}

export interface TopicReading extends TopicReadingSummary {
  intro: string;
  sections: Array<{ heading: string; content: string }>;
  sources: { heading: string; content: string };
}

export interface TopicReadingResponse {
  topic: TopicReading;
  categories: InsightCategory[];
}
