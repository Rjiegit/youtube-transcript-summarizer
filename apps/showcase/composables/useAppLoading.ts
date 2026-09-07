import { computed } from "vue";

type LoadingSources = Record<string, number>;

export function useAppLoading() {
  const sources = useState<LoadingSources>("showcase-app-loading-sources", () => ({}));
  const isLoading = computed(() => Object.values(sources.value).some((count) => count > 0));

  function start(source: string): void {
    sources.value = {
      ...sources.value,
      [source]: (sources.value[source] || 0) + 1,
    };
  }

  function finish(source: string): void {
    const currentCount = sources.value[source] || 0;
    if (currentCount <= 1) {
      const nextSources = { ...sources.value };
      delete nextSources[source];
      sources.value = nextSources;
      return;
    }

    sources.value = {
      ...sources.value,
      [source]: currentCount - 1,
    };
  }

  return {
    isLoading,
    start,
    finish,
  };
}
