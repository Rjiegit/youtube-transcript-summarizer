import { createError, defineEventHandler, readBody } from "h3";

import type { ReadStateMutation } from "../../../types/read-sync";
import { createReadStateRepository } from "../../utils/read-state-repository";
import {
  getRequestReadSyncConfig,
  requireReadSyncPrincipal,
  setPrivateNoStore,
} from "../../utils/read-sync-server";

const MAX_MUTATIONS_PER_REQUEST = 1000;

function normalizeMutations(value: unknown, ttlSeconds: number): ReadStateMutation[] | null {
  if (!Array.isArray(value) || value.length > MAX_MUTATIONS_PER_REQUEST) {
    return null;
  }
  const mutations: ReadStateMutation[] = [];
  for (const rawMutation of value) {
    if (!rawMutation || typeof rawMutation !== "object") {
      return null;
    }
    const mutation = rawMutation as Partial<ReadStateMutation>;
    const contentKey = typeof mutation.contentKey === "string" ? mutation.contentKey.trim() : "";
    const updatedAt = typeof mutation.updatedAt === "string" ? Date.parse(mutation.updatedAt) : NaN;
    if (!contentKey || contentKey.length > 2048 ||
        (mutation.status !== "read" && mutation.status !== "unread") ||
        !Number.isFinite(updatedAt)) {
      return null;
    }
    if (updatedAt < Date.now() - ttlSeconds * 1000) {
      continue;
    }
    mutations.push({
      contentKey,
      status: mutation.status,
      updatedAt: new Date(updatedAt).toISOString(),
    });
  }
  return mutations;
}

export default defineEventHandler(async (event) => {
  setPrivateNoStore(event);
  const config = getRequestReadSyncConfig(event);
  const principal = requireReadSyncPrincipal(event, config);
  const body = await readBody<{ mutations?: unknown }>(event);
  const mutations = normalizeMutations(body?.mutations, config.ttlSeconds);
  if (!mutations) {
    throw createError({ statusCode: 400, statusMessage: "Invalid read-state mutations." });
  }
  const repository = createReadStateRepository(config);
  return {
    entries: await repository.applyMutations(principal.syncSpaceId, mutations),
  };
});
