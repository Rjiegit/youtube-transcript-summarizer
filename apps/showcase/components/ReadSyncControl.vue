<script setup lang="ts">
import { computed, ref } from "vue";

import { useReadResults } from "../composables/useReadResults";

const {
  authenticateRemoteSync,
  isRemoteSyncEnabled,
  remoteSyncStatus,
  setRemoteSyncEnabled,
  syncRemoteState,
} = useReadResults();

const accessToken = ref("");
const authenticationError = ref("");
const isSubmitting = ref(false);
const isEnteringAccessToken = ref(false);

const statusLabel = computed(() => {
  switch (remoteSyncStatus.value) {
    case "connecting":
      return "同步中…";
    case "authentication_required":
      return "這台裝置尚未連結";
    case "unavailable":
      return "同步服務尚未設定";
    case "synced":
      return "已同步到你的裝置";
    case "error":
      return "同步暫時失敗，資料保存在本機";
    default:
      return "尚未連結這台裝置";
  }
});

async function connectOrRetry(): Promise<void> {
  authenticationError.value = "";
  if (isRemoteSyncEnabled.value) {
    await syncRemoteState();
    return;
  }
  isEnteringAccessToken.value = true;
  await setRemoteSyncEnabled(true);
}

async function submitAccessToken(): Promise<void> {
  const candidate = accessToken.value.trim();
  if (!candidate || isSubmitting.value) {
    return;
  }
  isSubmitting.value = true;
  authenticationError.value = "";
  const authenticated = await authenticateRemoteSync(candidate);
  if (authenticated) {
    accessToken.value = "";
    isEnteringAccessToken.value = false;
  } else {
    authenticationError.value = "同步碼無效，或同步服務暫時無法使用。";
  }
  isSubmitting.value = false;
}
</script>

<template>
  <div class="read-sync-control" data-testid="read-sync-control">
    <div class="read-sync-control__heading">
      <span class="read-sync-control__label">個人同步</span>
      <span class="read-sync-control__status" role="status" aria-live="polite">{{ statusLabel }}</span>
    </div>

    <button
      v-if="remoteSyncStatus === 'local' || remoteSyncStatus === 'error' || remoteSyncStatus === 'authentication_required'"
      class="read-sync-control__connect"
      data-testid="read-sync-connect-button"
      type="button"
      @click="connectOrRetry"
    >
      {{ remoteSyncStatus === "error" ? "重新連線" : remoteSyncStatus === "authentication_required" ? "輸入同步碼" : "連結這台裝置" }}
    </button>

    <form
      v-if="isEnteringAccessToken && remoteSyncStatus !== 'unavailable'"
      class="read-sync-auth"
      data-testid="read-sync-auth-form"
      @submit.prevent="submitAccessToken"
    >
      <label class="read-sync-auth__label" for="read-sync-access-token">
        輸入個人同步碼以連結這台裝置
      </label>
      <div class="read-sync-auth__fields">
        <input
          id="read-sync-access-token"
          v-model="accessToken"
          class="read-sync-auth__input"
          type="password"
          autocomplete="current-password"
          required
        />
        <button class="read-sync-auth__button" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? "連結中…" : "連結裝置" }}
        </button>
      </div>
      <p v-if="authenticationError" class="read-sync-auth__error" role="alert">
        {{ authenticationError }}
      </p>
    </form>
  </div>
</template>
