const TAIPEI_TIME_ZONE = "Asia/Taipei";

export function formatTaipeiDateTime(value?: string | null): string {
  if (!value) {
    return "";
  }

  return new Date(value).toLocaleString("zh-TW", {
    timeZone: TAIPEI_TIME_ZONE,
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTaipeiDate(value?: string | null): string {
  if (!value) {
    return "";
  }

  return new Date(value).toLocaleDateString("zh-TW", {
    timeZone: TAIPEI_TIME_ZONE,
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
