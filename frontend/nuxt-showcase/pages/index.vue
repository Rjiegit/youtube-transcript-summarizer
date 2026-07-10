<script setup lang="ts">
import { computed, onActivated, onBeforeUnmount, onMounted, ref, watch } from "vue";

import ShowcaseCard from "../components/ShowcaseCard.vue";
import { useReadResults } from "../composables/useReadResults";
import type { ShowcaseApiResponse } from "../types/showcase";
import { formatTaipeiDateTime } from "../utils/datetime";
import {
  dedupeShowcaseResults,
  getResultReadKeys,
  isResultRead,
  isShowcaseResponseStale,
  sortUnreadResultsFirst,
} from "../utils/showcase";

const route = useRoute();
const { data, pending, error } = await useFetch<ShowcaseApiResponse>("/api/showcase/results", {
  server: true,
  default: () => ({
    items: [],
    generated_at: "",
    cache_ttl_seconds: 3600,
  }),
});

useHead({
  title: "影片筆記庫",
  meta: [
    {
      name: "description",
      content: "收藏從影片整理出的重點筆記",
    },
    { property: "og:title", content: "影片筆記庫" },
    {
      property: "og:description",
      content: "收藏從影片整理出的重點筆記",
    },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary" },
    { name: "twitter:title", content: "影片筆記庫" },
    {
      name: "twitter:description",
      content: "收藏從影片整理出的重點筆記",
    },
  ],
});

const items = computed(() => data.value?.items ?? []);
const dedupedItems = computed(() => dedupeShowcaseResults(items.value));
const { isReady, markManyAsRead, readMap, refreshReadState } = useReadResults();
const titleSearchQuery = ref("");
const isRefreshingList = ref(false);
const listRenderRevision = ref(0);
const normalizedTitleSearchQuery = computed(() => titleSearchQuery.value.trim().toLowerCase());
const filteredItems = computed(() => {
  if (!normalizedTitleSearchQuery.value) {
    return dedupedItems.value;
  }

  return dedupedItems.value.filter((item) => item.title.toLowerCase().includes(normalizedTitleSearchQuery.value));
});
const displayItems = computed(() =>
  sortUnreadResultsFirst(filteredItems.value, (item) => isResultRead(item, readMap.value)));
const unreadDisplayItems = computed(() => filteredItems.value.filter((item) => !isResultRead(item, readMap.value)));
const unreadDisplayReadKeys = computed(() => unreadDisplayItems.value.flatMap((item) => getResultReadKeys(item)));
const canMarkAllRead = computed(() => isReady.value && unreadDisplayReadKeys.value.length > 0);
const skeletonItems = computed(() => Array.from({ length: Math.max(items.value.length, 3) }, (_, index) => index));
const hasTitleSearchQuery = computed(() => normalizedTitleSearchQuery.value.length > 0);
let listRefreshPromise: Promise<void> | null = null;
const errorMessage = computed(() => {
  if (!error.value) {
    return "";
  }
  return error.value.statusMessage || error.value.message || "請稍後再試。";
});

async function forceRefreshListData(): Promise<void> {
  try {
    const freshData = await $fetch<ShowcaseApiResponse>("/api/showcase/results", {
      query: {
        refresh: "1",
        ts: String(Date.now()),
      },
    });
    if (isListRoute(route.fullPath) && freshData && Array.isArray(freshData.items)) {
      data.value = freshData;
    }
  } catch {
    // Keep the current list visible if a forced refresh fails.
  }
}

function refreshListDataIfStale(): Promise<void> {
  if (!isShowcaseResponseStale(data.value)) {
    return Promise.resolve();
  }

  if (listRefreshPromise) {
    return listRefreshPromise;
  }

  isRefreshingList.value = true;
  listRefreshPromise = forceRefreshListData()
    .finally(() => {
      listRefreshPromise = null;
      isRefreshingList.value = false;
    });
  return listRefreshPromise;
}

function markCurrentListAsRead(): void {
  if (!canMarkAllRead.value) {
    return;
  }

  markManyAsRead(unreadDisplayReadKeys.value);
}

function handleVisibilityChange(): void {
  if (document.visibilityState === "visible") {
    refreshVisibleList();
  }
}

function handlePageShow(event: PageTransitionEvent): void {
  refreshReadState({
    forceRender: event.persisted,
  });
  if (event.persisted && isListRoute(route.fullPath)) {
    listRenderRevision.value += 1;
    void refreshListDataIfStale();
  }
}

function isListRoute(path: string): boolean {
  return path.split(/[?#]/, 1)[0] === "/";
}

function refreshVisibleListReadState(): void {
  refreshReadState();
}

function refreshVisibleList(): void {
  refreshVisibleListReadState();
  void refreshListDataIfStale();
}

watch(
  () => route.fullPath,
  (nextPath, previousPath) => {
    if (previousPath && nextPath !== previousPath && isListRoute(nextPath)) {
      refreshVisibleList();
    }
  },
);

onActivated(() => {
  if (isListRoute(route.fullPath)) {
    refreshVisibleList();
  }
});

onMounted(() => {
  refreshVisibleList();
  window.addEventListener("pageshow", handlePageShow);
  window.addEventListener("focus", refreshVisibleList);
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onBeforeUnmount(() => {
  window.removeEventListener("pageshow", handlePageShow);
  window.removeEventListener("focus", refreshVisibleList);
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});
</script>

<template>
  <main class="showcase-shell">
    <section class="hero">
      <div class="hero__content">
        <p class="hero__eyebrow">Video Knowledge Index</p>
        <h1 class="hero__title">影片筆記庫</h1>
        <p class="hero__body">
          收藏從影片整理出的重點筆記
        </p>
      </div>
    </section>

    <section v-if="!pending && !error && items.length > 0" class="showcase-toolbar" aria-label="展示內容工具列">
      <div class="showcase-toolbar__actions">
        <ClientOnly>
          <button
            type="button"
            class="showcase-toolbar__button"
            data-testid="mark-all-read-button"
            :disabled="!canMarkAllRead"
            @click="markCurrentListAsRead"
          >
            全部標記已讀
          </button>

          <template #fallback>
            <button type="button" class="showcase-toolbar__button" disabled>全部標記已讀</button>
          </template>
        </ClientOnly>
      </div>
      <label class="showcase-search">
        <span class="showcase-search__label">搜尋標題</span>
        <input
          v-model="titleSearchQuery"
          data-testid="title-search-input"
          class="showcase-search__input"
          type="search"
          placeholder="搜尋標題"
          autocomplete="off"
        />
      </label>
      <span
        v-if="isRefreshingList"
        class="showcase-toolbar__refresh-progress"
        data-testid="showcase-refresh-progress"
        role="status"
        aria-label="更新中"
      ></span>
    </section>

    <section v-if="pending" class="state-panel">
      <p class="state-panel__title">載入展示資料中</p>
      <p class="state-panel__body">正在讀取最近的完成結果。</p>
    </section>

    <section v-else-if="error" class="state-panel state-panel--error">
      <p class="state-panel__title">目前無法載入展示資料</p>
      <p class="state-panel__body">
        {{ errorMessage }}
      </p>
      <p class="state-panel__body">
        可直接檢查
        <a href="/api/showcase/diagnostics" target="_blank" rel="noreferrer">/api/showcase/diagnostics</a>
        確認 server 端實際讀到哪些 env，或打開
        <a href="/api/showcase/health" target="_blank" rel="noreferrer">/api/showcase/health</a>
        直接驗證 Notion 查詢。
      </p>
    </section>

    <section v-else-if="items.length === 0" class="state-panel">
      <p class="state-panel__title">還沒有可展示的結果</p>
      <p class="state-panel__body">Notion database 目前沒有 `Completed` 項目。</p>
    </section>

    <section v-else-if="hasTitleSearchQuery && displayItems.length === 0" class="state-panel">
      <p class="state-panel__title">找不到符合的標題</p>
      <p class="state-panel__body">請調整搜尋關鍵字後再試一次。</p>
    </section>

    <ClientOnly v-else>
      <section v-if="!isReady" class="showcase-grid showcase-grid--skeleton" aria-label="同步已讀狀態中">
        <article
          v-for="index in skeletonItems"
          :key="`skeleton-${index}`"
          class="showcase-skeleton-card"
          aria-hidden="true"
        >
          <div class="showcase-skeleton-card__meta"></div>
          <div class="showcase-skeleton-card__title"></div>
          <div class="showcase-skeleton-card__summary"></div>
          <div class="showcase-skeleton-card__summary showcase-skeleton-card__summary--short"></div>
        </article>
      </section>

      <TransitionGroup
        v-else
        :key="`showcase-grid-${listRenderRevision}`"
        name="showcase-grid"
        tag="section"
        class="showcase-grid"
      >
        <ShowcaseCard
          v-for="item in displayItems"
          :key="item.id"
          :item="item"
          :is-read="isResultRead(item, readMap)"
          @mark-read="markManyAsRead(getResultReadKeys(item))"
        />
      </TransitionGroup>

      <template #fallback>
        <section class="showcase-grid" aria-label="展示內容列表">
          <article
            v-for="item in displayItems"
            :key="`fallback-${item.id}`"
            class="showcase-card showcase-card--fallback"
          >
            <a :href="`/results/${item.id}`" class="showcase-card__main-link">
              <div class="showcase-card__meta">
                <span>{{ formatTaipeiDateTime(item.created_at) }}</span>
                <span v-if="item.processing_duration != null">{{ item.processing_duration.toFixed(1) }}s</span>
              </div>
              <div class="showcase-card__title-row">
                <h2 class="showcase-card__title">{{ item.title }}</h2>
              </div>
              <p v-if="item.summary" class="showcase-card__summary">{{ item.summary }}</p>
            </a>

            <div v-if="item.source_url" class="showcase-card__links">
              <a
                :href="item.source_url"
                target="_blank"
                rel="noreferrer"
                class="showcase-card__link"
              >
                原始影片
              </a>
            </div>
          </article>
        </section>
      </template>
    </ClientOnly>
  </main>
</template>
