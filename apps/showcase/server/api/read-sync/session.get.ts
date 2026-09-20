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
    available: config.configured,
    authenticated: config.configured && Boolean(resolveReadSyncPrincipal(event, config)),
  };
});
