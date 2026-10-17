// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils';
import { expect, it, vi } from 'vitest';
import Submit from '../pages/submit.vue';

it('retains the ID after response loss and reload, without storing credentials', async () => {
  const stored = new Map<string, string>();
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => stored.get(key) ?? null,
    setItem: (key: string, value: string) => stored.set(key, value),
    removeItem: (key: string) => stored.delete(key),
  });
  const fetch = vi.fn().mockRejectedValueOnce(new Error('lost')).mockResolvedValueOnce({ accepted: true });
  vi.stubGlobal('$fetch', fetch);
  const options = { global: { stubs: { NuxtLink: true } } };
  let wrapper = mount(Submit, options);
  await wrapper.find('input[type=url]').setValue('https://youtu.be/dQw4w9WgXcQ');
  await wrapper.find('input[type=password]').setValue('private-token');
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  const first = fetch.mock.calls[0][1].body;
  expect(localStorage.getItem('showcase-video-inbox-pending')).not.toContain('private-token');
  wrapper.unmount();
  wrapper = mount(Submit, options);
  await wrapper.find('input[type=password]').setValue('private-token');
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  expect(fetch.mock.calls[1][1].body).toEqual(first);
  expect(localStorage.getItem('showcase-video-inbox-pending')).toBeNull();
  expect(wrapper.text()).toContain('已送入收件匣');
  wrapper.unmount();
  vi.unstubAllGlobals();
});

it('does not send on any retry when durable browser storage is unavailable', async () => {
  vi.stubGlobal('localStorage', {
    getItem: () => null,
    setItem: () => { throw new Error('storage blocked'); },
    removeItem: vi.fn(),
  });
  const fetch = vi.fn();
  vi.stubGlobal('$fetch', fetch);
  const wrapper = mount(Submit, { global: { stubs: { NuxtLink: true } } });
  await wrapper.find('input[type=url]').setValue('https://youtu.be/dQw4w9WgXcQ');
  await wrapper.find('input[type=password]').setValue('private-token');
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  await wrapper.find('form').trigger('submit');
  await flushPromises();
  expect(fetch).not.toHaveBeenCalled();
  wrapper.unmount();
  vi.unstubAllGlobals();
});
