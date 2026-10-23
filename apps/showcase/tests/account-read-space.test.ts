// @vitest-environment node
import { expect, it, vi } from 'vitest';
import { requireAccountUser } from '../server/utils/account-access';
import { requireReadStateSpace } from '../server/utils/read-sync-server';
import type { ReadSyncConfig } from '../server/utils/read-sync-config';

vi.mock('../server/utils/account-access', () => ({ requireAccountUser: vi.fn() }));

it('isolates account read state by validated user ID', async () => {
  vi.mocked(requireAccountUser).mockResolvedValue('invited-user');
  const config = { accountMode: true, configured: true } as ReadSyncConfig;
  expect(await requireReadStateSpace({} as never, config)).toBe('account:invited-user');
  expect(requireAccountUser).toHaveBeenCalledOnce();
});
