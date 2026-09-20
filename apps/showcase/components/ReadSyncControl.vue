<script setup lang="ts">
import { computed, ref } from "vue";

import { useReadResults } from "../composables/useReadResults";

const {
  authenticateRemoteSync,
  isRemoteSyncEnabled,
  remoteSyncStatus,
  setRemoteSyncEnabled,
} = useReadResults();

const accessToken = ref("");
const authenticationError = ref("");
const isSubmitting = ref(false);

const statusLabel = computed(() => {
  switch (remoteSyncStatus.value) {
    case "connecting":
      return "同步中…";
    case "authentication_required":
      return "需要同步碼";
    case "unavailable":
      return "尚未完成伺服器設定";
    case "synced":
      return "已同步";
    case "error":
      return "同步失敗，保留本機狀態";
    default:
      return "僅儲存在這台裝置";
  }
});

async function handleToggle(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  authenticationError.value = "";
  await setRemoteSyncEnabled(input.checked);
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
  } else {
    authenticationError.value = "同步碼無效，或同步服務暫時無法使用。";
  }
  isSubmitting.value = false;
}
</script>

<template>
  <div class="read-sync-control" data-testid="read-sync-control">
    <label class="read-sync-toggle">
      <input
        :checked="isRemoteSyncEnabled"
        data-testid="read-sync-toggle"
        type="checkbox"
        @change="handleToggle"
      />
      <span>跨裝置同步</span>
    </label>
    <span class="read-sync-control__status" aria-live="polite">{{ statusLabel }}</span>

    <form
      v-if="isRemoteSyncEnabled && remoteSyncStatus === 'authentication_required'"
      class="read-sync-auth"
      data-testid="read-sync-auth-form"
      @submit.prevent="submitAccessToken"
    >
      <label class="read-sync-auth__label" for="read-sync-access-token">個人同步碼</label>
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
          {{ isSubmitting ? "連線中…" : "連線" }}
        </button>
      </div>
      <p v-if="authenticationError" class="read-sync-auth__error" role="alert">
        {{ authenticationError }}
      </p>
    </form>
  </div>
</template>
