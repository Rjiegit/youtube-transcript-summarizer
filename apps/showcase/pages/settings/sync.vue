<script setup lang="ts">
import ReadSyncControl from "../../components/ReadSyncControl.vue";

useHead({
  title: "裝置同步設定",
  meta: [
    { name: "robots", content: "noindex, nofollow" },
    { name: "description", content: "管理這台裝置的個人已讀狀態同步" },
  ],
});
</script>

<template>
  <main class="showcase-shell">
    <section class="sync-settings" aria-labelledby="sync-settings-title">
      <p class="hero__eyebrow">Personal Settings</p>
      <h1 id="sync-settings-title" class="sync-settings__title">裝置同步設定</h1>
      <p class="sync-settings__description">
        已連結的裝置會自動同步已讀狀態。首次使用新裝置時，在此輸入個人同步碼；完成連結後不需要再次設定。
      </p>

      <ReadSyncControl />

      <NuxtLink class="sync-settings__back" to="/">返回影片筆記庫</NuxtLink>
    </section>
  </main>
</template>
