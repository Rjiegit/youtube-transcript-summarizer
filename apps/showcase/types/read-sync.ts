export type ReadStateStatus = "read" | "unread";

export interface SyncedReadEntry {
  status: ReadStateStatus;
  updatedAt: string;
}

export type SyncedReadMap = Record<string, SyncedReadEntry>;

export interface ReadStateMutation extends SyncedReadEntry {
  contentKey: string;
}

export interface ReadStateSnapshotResponse {
  entries: SyncedReadMap;
}

export interface ReadSyncSessionResponse {
  available: boolean;
  authenticated: boolean;
}
