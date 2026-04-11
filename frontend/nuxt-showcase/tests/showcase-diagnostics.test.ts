import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const runtimeConfigMock = vi.fn();
const fetchDatabaseSchemaMock = vi.fn();
const fetchLatestCompletedResultsMock = vi.fn();
const resolveFieldMappingMock = vi.fn();
const resolveStatusConfigMock = vi.fn();

vi.mock("../server/utils/notion", () => ({
  fetchDatabaseSchema: fetchDatabaseSchemaMock,
  fetchLatestCompletedResults: fetchLatestCompletedResultsMock,
  resolveFieldMapping: resolveFieldMappingMock,
  resolveStatusConfig: resolveStatusConfigMock,
}));

vi.stubGlobal("useRuntimeConfig", runtimeConfigMock);

describe("showcase diagnostics and health routes", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
    runtimeConfigMock.mockReset();
    fetchDatabaseSchemaMock.mockReset();
    fetchLatestCompletedResultsMock.mockReset();
    resolveFieldMappingMock.mockReset();
    resolveStatusConfigMock.mockReset();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("returns diagnostics using the same config resolver snapshot", async () => {
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "",
      notionDatabaseId: "runtime-database-id",
      showcaseCacheTtlSeconds: 900,
    });
    process.env.NOTION_API_KEY = "env-api-key";

    const handler = (await import("../server/api/showcase/diagnostics.get")).default;
    const result = handler({});

    expect(result).toMatchObject({
      ok: true,
      resolved: {
        notionApiKey: true,
        notionDatabaseId: true,
        cacheTtlSeconds: 900,
      },
      diagnostic: {
        runtimeConfig: {
          notionApiKey: false,
          notionDatabaseId: true,
          showcaseCacheTtlSeconds: 900,
        },
        processEnv: {
          NOTION_API_KEY: true,
        },
      },
    });
  });

  it("returns health data using the same resolved config", async () => {
    runtimeConfigMock.mockReturnValue({
      notionApiKey: "runtime-api-key",
      notionDatabaseId: "",
      statusPropertyName: "狀態",
      completedStatusValue: "已完成",
      showcaseCacheTtlSeconds: 600,
    });
    process.env.NOTION_DATABASE_ID = "env-database-id";
    fetchDatabaseSchemaMock.mockResolvedValue({
      title: [{ plain_text: "Knowledge DB" }],
      properties: {
        狀態: { type: "status" },
      },
    });
    resolveStatusConfigMock.mockReturnValue({
      filter: {
        kind: "status",
        propertyName: "狀態",
        propertyType: "status",
        completedValue: "已完成",
      },
    });
    resolveFieldMappingMock.mockReturnValue({
      titlePropertyName: "Title",
    });
    fetchLatestCompletedResultsMock.mockResolvedValue({
      items: [{ title: "Latest result" }],
      generated_at: "2026-04-11T12:00:00.000Z",
    });

    const handler = (await import("../server/api/showcase/health.get")).default;
    const result = await handler({});

    expect(fetchDatabaseSchemaMock).toHaveBeenCalledWith("runtime-api-key", "env-database-id");
    expect(fetchLatestCompletedResultsMock).toHaveBeenCalledWith(expect.objectContaining({
      apiKey: "runtime-api-key",
      databaseId: "env-database-id",
      cacheTtlSeconds: 600,
      statusPropertyName: "狀態",
      completedStatusValue: "已完成",
    }));
    expect(result).toMatchObject({
      ok: true,
      itemCount: 1,
      sampleTitle: "Latest result",
      generatedAt: "2026-04-11T12:00:00.000Z",
    });
  });
});
