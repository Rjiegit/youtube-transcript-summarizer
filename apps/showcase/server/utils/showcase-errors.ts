// Never log upstream messages, response bodies, credentials, or user-controlled identifiers.
export function logShowcaseQueryFailure(route: "results" | "detail", error: unknown): void {
  const kind = error instanceof DOMException && error.name === "TimeoutError"
    ? "timeout"
    : error instanceof TypeError
      ? "network-or-type-error"
      : "upstream-error";

  console.error("[showcase] Notion query failed", { route, kind });
}
