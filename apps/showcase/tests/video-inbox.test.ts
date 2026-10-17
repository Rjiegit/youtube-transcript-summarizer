import { describe, expect, it } from 'vitest';
import { validateSubmission, authorizeSubmission } from '../server/utils/video-inbox';

describe('video inbox boundary', () => {
  it('rejects anonymous, wrong tokens and cross origin requests', () => {
    expect(() => authorizeSubmission('', 'secret', 'https://site.test', 'https://site.test')).toThrow();
    expect(() => authorizeSubmission('wrong', 'secret', 'https://site.test', 'https://site.test')).toThrow();
    expect(() => authorizeSubmission('secret', 'secret', 'https://evil.test', 'https://site.test')).toThrow();
    expect(() => authorizeSubmission('secret', '', 'https://site.test', 'https://site.test')).toThrow();
    expect(() => authorizeSubmission('secret', 'secret', 'https://site.test', 'https://site.test')).not.toThrow();
  });
  it('normalizes only trusted youtube sources and requires stable UUID', () => {
    const body = { submission_id: 'b1cdf760-37af-4b70-95ac-64484a97da91', url: 'https://youtu.be/dQw4w9WgXcQ' };
    expect(validateSubmission(body).url).toBe('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    expect(() => validateSubmission({ ...body, url: 'https://evil.test/youtube.com/watch?v=dQw4w9WgXcQ' })).toThrow();
    expect(() => validateSubmission({ ...body, submission_id: '' })).toThrow();
  });
});
