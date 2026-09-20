import { defineEventHandler } from "h3";

import { createReadStateRepository } from "../../utils/read-state-repository";
import {
  getRequestReadSyncConfig,
  requireReadSyncPrincipal,
  setPrivateNoStore,
} from "../../utils/read-sync-server";

export default defineEventHandler(async (event) => {
  setPrivateNoStore(event);
  const config = getRequestReadSyncConfig(event);
  const principal = requireReadSyncPrincipal(event, config);
  const repository = createReadStateRepository(config);
  return {
    entries: await repository.getSnapshot(principal.syncSpaceId),
  };
});
