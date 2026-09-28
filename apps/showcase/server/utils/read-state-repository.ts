import type {
  ReadStateMutation,
  SyncedReadMap,
} from "../../types/read-sync";
import type { ReadSyncConfig } from "./read-sync-config";
import {
  applyReadStateMutations,
  getReadStateSnapshot,
} from "./upstash-read-state";

export interface ReadStateRepository {
  getSnapshot(syncSpaceId: string): Promise<SyncedReadMap>;
  applyMutations(syncSpaceId: string, mutations: ReadStateMutation[]): Promise<SyncedReadMap>;
}

export function createReadStateRepository(config: ReadSyncConfig): ReadStateRepository {
  const upstashConfig = {
    url: config.upstashUrl,
    token: config.upstashToken,
  };

  return {
    getSnapshot(syncSpaceId) {
      return getReadStateSnapshot(upstashConfig, syncSpaceId, config.ttlSeconds);
    },
    applyMutations(syncSpaceId, mutations) {
      return applyReadStateMutations(upstashConfig, syncSpaceId, mutations, config.ttlSeconds);
    },
  };
}
