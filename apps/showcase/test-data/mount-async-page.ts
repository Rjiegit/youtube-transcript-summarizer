import { flushPromises, mount, type ComponentMountingOptions } from "@vue/test-utils";
import { defineComponent, h, Suspense, type Component } from "vue";

export async function mountAsyncPage(component: Component, options: ComponentMountingOptions<any> = {}) {
  let setupError: unknown;
  const wrapper = mount(defineComponent({
    render: () => h(Suspense, null, { default: () => h(component) }),
  }), {
    ...options,
    global: {
      ...options.global,
      config: {
        ...options.global?.config,
        errorHandler: (error) => { setupError = error; },
      },
    },
  });
  await flushPromises();
  if (setupError) {
    wrapper.unmount();
    throw setupError;
  }
  return wrapper;
}
