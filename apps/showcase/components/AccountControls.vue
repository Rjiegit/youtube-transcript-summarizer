<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useAccountAuth } from '../composables/useAccountAuth';

const auth = useAccountAuth();
const error = ref('');
onMounted(() => { void auth.initialize(); });

async function signOut(): Promise<void> {
  error.value = '';
  try { await auth.signOut(); }
  catch { error.value = '登出未完成，請稍後再試。'; }
}
</script>

<template>
  <nav v-if="auth.enabled" class="account-controls" aria-label="帳號">
    <template v-if="auth.userId.value">
      <NuxtLink to="/settings/sync">我的已讀</NuxtLink>
      <NuxtLink to="/login">帳號設定</NuxtLink>
      <button type="button" @click="signOut">登出</button>
    </template>
    <NuxtLink v-else to="/login">登入</NuxtLink>
    <span v-if="error" role="alert">{{ error }}</span>
  </nav>
</template>
