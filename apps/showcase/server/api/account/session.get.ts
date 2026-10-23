import { defineEventHandler } from 'h3';
import { requireAccountUser } from '../../utils/account-access';

export default defineEventHandler(async (event) => ({ userId: await requireAccountUser(event) }));
