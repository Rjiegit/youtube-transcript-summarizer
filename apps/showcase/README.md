# Nuxt Showcase

從 Notion 讀取完成摘要的 Nuxt 3 展示站，提供搜尋、每週回顧、選用的跨裝置已讀同步，以及受保護的雲端影片提交入口。

## 啟動與驗證

在 `apps/showcase/` 執行；先在 server environment 或本機 `.env` 設定 `NOTION_API_KEY`、`NOTION_DATABASE_ID`：

```bash
npm install
npm run check-env
npm run dev
```

開發站預設 `http://localhost:3000`。環境變數與部署核對見 [Showcase 操作手冊](../../docs/operations/showcase.md)。

```bash
npm run test
npm run build
npm run test:ssr
```

SSR 檢查需先完成 build。各項測試與 CI 責任見 [開發與測試](../../openwiki/operations/development-and-testing.md)。

## 功能與文件

| 功能 | 操作入口 | 實作說明 |
| --- | --- | --- |
| 文章瀏覽、搜尋、分享 | 首頁與 `/results/{id}`；[設定與排錯](../../docs/operations/showcase.md) | [Showcase 體驗與快取](../../openwiki/frontend/showcase-experience.md) |
| 每週回顧 | `/insights`；[分析規則與更新步驟](../../docs/features/showcase-weekly-insights.md) | [內容建置流程](../../openwiki/workflows/weekly-insights.md) |
| 已讀同步 | `/settings/sync`；[安裝與維運](../../docs/operations/showcase-read-sync.md) | [Session 與資料合併](../../openwiki/frontend/read-state-sync.md) |
| 影片收件匣 | `/submit`；[安裝、輪替與復原](../../docs/video-inbox.md) | 見操作手冊的實作來源導覽；OpenWiki 尚無獨立收件匣頁面 |

週報由 `content/weekly-insights/` 在啟動／建置時載入；定期整理使用 [週報 skill](../../.agents/skills/showcase-weekly-insights/SKILL.md)。
完整的文件分工見 [操作文件導覽](../../docs/README.md)。
