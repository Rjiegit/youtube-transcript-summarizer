<script setup lang="ts">
import { onMounted, ref } from 'vue';
const url = ref('');
const token = ref('');
const pending = ref(false);
const submission = ref<{ submission_id: string; url: string } | null>(null);
const message = ref('');
const storageKey = 'showcase-video-inbox-pending';
onMounted(() => {
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) || 'null');
    if (stored && typeof stored.submission_id === 'string' && typeof stored.url === 'string') {
      submission.value = stored;
      url.value = stored.url;
    }
  } catch { /* Form remains usable if storage is unavailable. */ }
});
async function submit() {
  pending.value = true;
  try {
    if (!submission.value) {
      submission.value = { submission_id: crypto.randomUUID(), url: url.value };
    }
    // Every attempt must be durable, including retries after a storage failure.
    localStorage.setItem(storageKey, JSON.stringify(submission.value));
    await $fetch('/api/video-inbox', {
      method: 'POST', retry: 0, timeout: 20000, headers: { 'x-video-inbox-token': token.value }, body: submission.value,
    });
    localStorage.removeItem(storageKey);
    submission.value = null;
    url.value = '';
    message.value = '已送入收件匣，本機上線後會接收處理。';
  } catch {
    message.value = '尚未確認收件，請確認網址與提交碼後重試；重試會沿用相同識別碼。';
  } finally { pending.value = false; }
}
function cancel() {
  localStorage.removeItem(storageKey);
  submission.value = null;
  message.value = '已清除本機待確認提交；已送出的訊息仍可能被接收。';
}
</script>

<template>
  <main class="showcase-shell">
    <h1>提交 YouTube 影片</h1>
    <p>影片會先存入雲端收件匣，待本機上線接收。</p>
    <form @submit.prevent="submit">
      <p><label>影片網址 <input v-model="url" type="url" required :disabled="pending || !!submission" /></label></p>
      <p><label>提交碼 <input v-model="token" type="password" required autocomplete="off" /></label></p>
      <button :disabled="pending" type="submit">{{ pending ? '提交中…' : submission ? '重試提交' : '提交影片' }}</button>
      <button v-if="submission" :disabled="pending" type="button" @click="cancel">清除待確認提交</button>
    </form>
    <p role="status">{{ message }}</p>
    <NuxtLink to="/">返回影片筆記庫</NuxtLink>
  </main>
</template>

<style scoped>
form {
  max-width: 42rem;
  padding: 1.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
}
label { display: grid; gap: 0.5rem; }
input { width: 100%; padding: 0.65rem; box-sizing: border-box; }
button { padding: 0.6rem 1rem; margin: 0.25rem 0.5rem 0.25rem 0; cursor: pointer; }
button:disabled { cursor: wait; }
</style>
