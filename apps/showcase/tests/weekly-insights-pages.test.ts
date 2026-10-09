import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { reactive, ref } from "vue";
import { mountAsyncPage } from "../test-data/mount-async-page";
import type { InsightListResponse, WeeklyInsight } from "../types/weekly-insights";

const useFetchMock = vi.fn();
const route = reactive({ query: {} as Record<string, string>, params: { start: "2026-08-30" } });
const replace = vi.fn(({ query }) => { route.query = query; });
const stubs = { NuxtLink: { props: ["to"], template: '<a :href="to"><slot /></a>' } };
const categories = [{ id: "agent-engineering", label: "Agent 工程" }, { id: "career", label: "職涯" }];
const week = (start: string, overrides = {}): WeeklyInsight => ({
  start, endExclusive: "2026-09-13", coverageStart: start, title: "本週回顧", summary: "本週重點",
  revision: 1, asOf: "2026-10-09T09:44:10Z", periodState: "closed", dataCompleteness: "complete",
  metrics: { rawCount: 10, sourceCount: 10, newSourceCount: 8, recurringSourceCount: 2 },
  categories: [{ id: "agent-engineering", count: 6 }, { id: "career", count: 4 }],
  content: "## 工程流程\n\n需要驗證成果。", sources: [], qualityNote: "資料說明", ...overrides,
});
const series: InsightListResponse["series"] = {
  collectionStart: "2026-09-01", asOf: "2026-10-09T09:44:10Z", timezone: "Asia/Taipei",
  weekConvention: "sunday-saturday", dedupPolicy: "within-week-source",
  analysisVersion: "topic-v1-sunday", uniqueSourceCount: 30, categories, overview: "## 整體摘要\n\n收錄題材有變化。",
  topicInsights: { fromWeek: "2026-09-06", toWeek: "2026-09-13", items: [
    { categoryId: "agent-engineering", change: "從工具試用到驗證成果", signal: "可靠交付持續出現", watch: "追蹤失敗處理" },
    { categoryId: "career", change: "從升遷到可轉移能力", signal: "單週集中", watch: "觀察長期能力" },
  ] },
};
const items = [
  week("2026-08-30", { coverageStart: "2026-09-01", endExclusive: "2026-09-06" }),
  week("2026-09-06"), week("2026-09-13", { endExclusive: "2026-09-20" }),
  week("2026-10-04", { endExclusive: "2026-10-11", periodState: "open" }),
];

beforeEach(() => {
  route.query = {};
  vi.stubGlobal("useRoute", () => route);
  vi.stubGlobal("useRouter", () => ({ replace }));
  vi.stubGlobal("useFetch", useFetchMock);
  vi.stubGlobal("useHead", vi.fn());
  vi.stubGlobal("useRuntimeConfig", () => ({ public: { siteUrl: "https://example.com" } }));
  vi.stubGlobal("createError", (error: object) => Object.assign(new Error("page error"), error));
});
afterEach(() => { vi.clearAllMocks(); });

describe("weekly insight pages", () => {
  it("renders reviews and compares only full Sunday–Saturday weeks by default", async () => {
    useFetchMock.mockReturnValue({ data: ref({ series, weeks: items }), error: ref(null) });
    const page = await import("../pages/insights/index.vue");
    const wrapper = await mountAsyncPage(page.default, { global: { stubs } });
    expect(wrapper.findAll(".insight-week-card")).toHaveLength(4);
    expect(wrapper.findAll(".insight-chart__column")).toHaveLength(2);
    expect(wrapper.get('[data-testid="topic-insight"]').text()).toContain("從工具試用到驗證成果");
    expect(wrapper.get('[data-testid="topic-evidence"]').attributes("open")).toBeUndefined();
    expect(wrapper.text()).toContain("首週部分資料");
    expect(wrapper.text()).toContain("本週進行中");
    await wrapper.get('[data-testid="include-partial"]').setValue(true);
    expect(replace).toHaveBeenCalledWith({ query: { partial: "1" } });
    expect(wrapper.findAll(".insight-chart__column")).toHaveLength(4);
    expect(wrapper.findAll(".insight-category-button")).toHaveLength(categories.length);
    await wrapper.get('button[data-category="career"]').trigger("click");
    expect(wrapper.get('button[data-category="career"]').attributes("aria-pressed")).toBe("true");
    expect(wrapper.get('[data-testid="topic-evidence"]').find('select[aria-label="起始週"]').exists()).toBe(true);
    expect(route.query.category).toBe("career");
    expect(wrapper.get('[data-testid="topic-insight"]').text()).toContain("從升遷到可轉移能力");
    await wrapper.get('select[aria-label="起始週"]').setValue("2026-09-13");
    expect(wrapper.findAll(".insight-week-card")).toHaveLength(2);
    expect(wrapper.get('[data-testid="topic-insight"]').text()).toContain("2026-09-06–2026-09-19");
    expect(wrapper.get(".insight-chart").attributes("aria-label")).toContain("職涯");
    wrapper.unmount();
  });

  it("restores filters from the URL and reports no matching weeks", async () => {
    route.query = { from: "2027-01-01", to: "2027-02-01", category: "career" };
    useFetchMock.mockReturnValue({ data: ref({ series, weeks: items }), error: ref(null) });
    const page = await import("../pages/insights/index.vue");
    const wrapper = await mountAsyncPage(page.default, { global: { stubs } });
    expect(wrapper.findAll(".insight-week-card")).toHaveLength(0);
    expect(wrapper.text()).toContain("沒有符合日期的週報");
    expect(wrapper.text()).toContain("週次來源合計");
    wrapper.unmount();
  });

  it("shows an empty state without creating a chart", async () => {
    useFetchMock.mockReturnValue({ data: ref({ series, weeks: [] }), error: ref(null) });
    const page = await import("../pages/insights/index.vue");
    const wrapper = await mountAsyncPage(page.default, { global: { stubs } });
    expect(wrapper.text()).toContain("尚未整理週報");
    expect(wrapper.find(".insight-chart").exists()).toBe(false);
    wrapper.unmount();
  });

  it("renders first-week coverage, Markdown and navigation without marking articles read", async () => {
    useFetchMock.mockReturnValue({ data: ref({ series, week: items[0], previous: null, next: items[1].start }), error: ref(null) });
    const page = await import("../pages/insights/[start].vue");
    const wrapper = await mountAsyncPage(page.default, { global: { stubs } });
    expect(wrapper.get('[data-testid="partial-week-notice"]').text()).toContain("2026-09-01");
    expect(wrapper.find(".markdown-content h2").text()).toBe("工程流程");
    expect(wrapper.find('a[href="/insights/2026-09-06"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/results/"]').exists()).toBe(false);
    wrapper.unmount();
  });

});
