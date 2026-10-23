<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useAccountAuth } from '../composables/useAccountAuth';

const auth = useAccountAuth();
const accountConfigured = Boolean(useRuntimeConfig().public.accountSupabaseUrl &&
  useRuntimeConfig().public.accountSupabasePublishableKey);
const email = ref('');
const password = ref('');
const newPassword = ref('');
const busy = ref(false);
const message = ref('');

useHead({ title: '登入', meta: [{ name: 'robots', content: 'noindex, nofollow' }] });
onMounted(() => { void auth.initialize(); });

async function run(action: () => Promise<void>, success: string): Promise<void> {
  busy.value = true;
  message.value = '';
  try {
    await action();
    message.value = success;
  } catch {
    message.value = '操作未完成，請檢查輸入或稍後再試。';
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <main class="showcase-shell">
    <section class="account-panel">
      <p class="hero__eyebrow">Personal Access</p>
      <h1>登入影片筆記庫</h1>
      <p>文章可公開閱讀；受邀帳號登入後可以提交影片，並同步自己的已讀狀態。</p>
      <p v-if="!auth.enabled" role="status">帳號登入目前尚未啟用。</p>
      <p v-else-if="!accountConfigured" role="status">帳號登入尚未完成設定。</p>
      <template v-else>
        <p v-if="auth.error.value" role="alert">{{ auth.error.value }}</p>
        <form v-if="!auth.sessionUserId.value" @submit.prevent="run(() => auth.signInWithPassword(email, password), '登入成功。')">
          <label>Email <input v-model="email" type="email" autocomplete="username" required /></label>
          <label>密碼 <input v-model="password" type="password" autocomplete="current-password" required /></label>
          <button type="submit" :disabled="busy">登入</button>
          <button type="button" :disabled="busy || !email" @click="run(() => auth.requestPasswordReset(email), '若帳號存在，密碼重設信將寄到你的信箱。')">忘記密碼</button>
        </form>
        <div v-else>
          <p>{{ auth.userId.value ? '已登入。' : '已驗證登入，但尚未取得網站使用權限。' }}</p>
          <form @submit.prevent="run(() => auth.updatePassword(newPassword), '密碼已更新。')">
            <label>設定或更改密碼 <input v-model="newPassword" type="password" autocomplete="new-password" minlength="8" required /></label>
            <button type="submit" :disabled="busy">儲存密碼</button>
          </form>
          <button type="button" :disabled="busy" @click="run(auth.signOut, '已登出。')">登出</button>
        </div>
        <p role="status">{{ message }}</p>
      </template>
      <NuxtLink to="/">返回影片筆記庫</NuxtLink>
    </section>
  </main>
</template>
