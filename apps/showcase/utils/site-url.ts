export const DEFAULT_SITE_URL = "https://video-knowledge.hellojie.me";

// Use a configured public origin rather than the request's untrusted Host header.
export function resolveSiteUrl(value: unknown): string {
  if (typeof value === "string" && value.trim()) {
    try {
      const url = new URL(value.trim());
      if (url.protocol === "https:" && !url.username && !url.password) {
        return url.origin;
      }
    } catch {
      // Invalid or missing configuration uses the production site's origin.
    }
  }
  return DEFAULT_SITE_URL;
}
