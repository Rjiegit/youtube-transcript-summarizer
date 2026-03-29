# Nuxt Showcase

這是一個部署到 Vercel 的 Nuxt 3 展示頁，會直接從 Notion database 讀取最近 100 筆 `Completed` 結果並顯示在首頁。

## Commands

```bash
npm install
npm run dev
npm run test
npm run build
```

## Environment Variables

- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- `NOTION_URL`
- `SHOWCASE_CACHE_TTL_SECONDS`（選填，預設 `3600`）

## Cache

Server API route 會回傳：

```txt
Cache-Control: public, s-maxage=3600, stale-while-revalidate=3600
```

搭配 Vercel CDN 做簡易 SWR 快取；server process 內也保留最後成功的資料快照，當 Notion 暫時失敗時可優先回退。
