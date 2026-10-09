import { getRequestURL, getResponseStatus, setHeader } from "h3";

// Nitro's SWR wrapper uses a separate response when a cached handler throws.
// Apply the error policy before Nitro renders the error response.
export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook("error", (error, { event }) => {
    if (!event || event.node.res.headersSent) {
      return;
    }
    const path = getRequestURL(event).pathname;
    const errorStatus = (error as { statusCode?: number }).statusCode ?? 0;
    if (
      (path === "/api/showcase/results" || path.startsWith("/api/showcase/results/") || path.startsWith("/results/") ||
        path === "/api/showcase/insights" || path.startsWith("/api/showcase/insights/") ||
        path === "/insights" || path.startsWith("/insights/"))
      && Math.max(getResponseStatus(event), errorStatus) >= 400
    ) {
      setHeader(event, "Cache-Control", "no-store");
    }
  });
});
