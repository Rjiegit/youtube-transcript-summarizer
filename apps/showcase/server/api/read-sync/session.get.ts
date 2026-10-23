import { defineEventHandler } from "h3";

import {
  getRequestReadSyncConfig,
  resolveReadSyncPrincipal,
  setPrivateNoStore,
} from "../../utils/read-sync-server";

export default defineEventHandler((event) => {
  setPrivateNoStore(event);
  const config = getRequestReadSyncConfig(event);
  return {
    available: config.configured && !config.accountMode,
    authenticated: config.configured && !config.accountMode && Boolean(resolveReadSyncPrincipal(event, config)),
  };
});
