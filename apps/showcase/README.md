# Nuxt Showcase

從 Notion 讀取完成摘要的 Nuxt 4 展示站，提供搜尋、跨影片專題與每週回顧、選用的跨裝置已讀同步，以及受保護的雲端影片提交入口。

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
| 專題與每週回顧 | `/insights`；[分析規則與更新步驟](../../docs/features/showcase-weekly-insights.md) | [內容建置流程](../../openwiki/workflows/weekly-insights.md) |
| 已讀同步 | `/settings/sync`；[安裝與維運](../../docs/operations/showcase-read-sync.md) | [Session 與資料合併](../../openwiki/frontend/read-state-sync.md) |
| 受邀帳號登入 | `/login`；[Feature Toggle 與啟用步驟](../../docs/operations/showcase-account-auth.md) | Supabase Auth；預設關閉 |
| 影片收件匣 | `/submit`；[安裝、輪替與復原](../../docs/video-inbox.md) | 見操作手冊的實作來源導覽；OpenWiki 尚無獨立收件匣頁面 |

近期重點在 `/insights` 優先展示，提供比較範圍、限制與來源；細節可於同頁展開。其後可依分類閱讀跨影片專題，點進 `/insights/topics/{id}` 查看整合理解、差異與預設收合的來源對照。完整週報與統計仍可查閱。

週報由 `content/weekly-insights/` 在啟動／建置時載入；定期整理使用 [週報 skill](../../.agents/skills/showcase-weekly-insights/SKILL.md)。
專題以 `content/topic-readings/{id}.md` 的 JSON frontmatter 與正文為單一來源，`content/topic-readings/manifest.json` 選入網站；與週報一起在啟動／建置時驗證及打包。更新已發佈稿件後須重新啟動或建置。
完整的文件分工見 [操作文件導覽](../../docs/README.md)。

### 首頁與回顧閱讀排版

首頁的每週回顧區塊試行一則人工選稿，選自 11/15–11/21 完整週。「閱讀本期週報」直接開啟該期週報，「查看全部週報」開啟 `/insights`。週報開頭也可接著閱讀 Agent 驗收專題。回顧頁在寬螢幕以雙欄呈現近期重點，900px 以下改為單欄。
