import { getRequestURL, getResponseStatus, setHeader } from "h3";

// Nitro's SWR wrapper uses a separate response when a cached handler throws.
// Apply the error policy before Nitro renders the error response.
export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook("error", (_error, { event }) => {
    if (!event || event.node.res.headersSent) {
      return;
    }
    const path = getRequestURL(event).pathname;
    if (
      (path === "/api/showcase/results" || path.startsWith("/api/showcase/results/") || path.startsWith("/results/"))
      && getResponseStatus(event) >= 400
    ) {
      setHeader(event, "Cache-Control", "no-store");
    }
  });
});
