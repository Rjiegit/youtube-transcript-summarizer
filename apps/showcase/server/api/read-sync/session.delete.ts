import { deleteCookie, defineEventHandler } from "h3";

import { READ_SYNC_COOKIE_NAME } from "../../utils/read-sync-auth";
import { setPrivateNoStore } from "../../utils/read-sync-server";

export default defineEventHandler((event) => {
  setPrivateNoStore(event);
  deleteCookie(event, READ_SYNC_COOKIE_NAME, { path: "/" });
  return { available: true, authenticated: false };
});
