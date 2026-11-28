<script setup lang="ts">
import MarkdownIt from "markdown-it";
import { computed } from "vue";

const props = defineProps<{
  source: string;
}>();

const markdownRenderer = new MarkdownIt({
  html: false,
  linkify: false,
  typographer: false,
});

const defaultLinkOpenRenderer = markdownRenderer.renderer.rules.link_open;

markdownRenderer.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const href = token.attrGet("href") ?? "";
  if (!/^\/(?![/\\])/.test(href)) {
    token.attrSet("target", "_blank");
    token.attrSet("rel", "noreferrer");
  }

  return defaultLinkOpenRenderer
    ? defaultLinkOpenRenderer(tokens, idx, options, env, self)
    : self.renderToken(tokens, idx, options);
};

const renderedContent = computed(() => {
  return renderTaskListInputs(markdownRenderer.render(props.source || ""));
});

function renderTaskListInputs(html: string): string {
  return html.replace(/<li>\[([ xX])\]\s+/g, (_match, checkedMarker: string) => {
    const checkedAttribute = checkedMarker.toLowerCase() === "x" ? " checked" : "";
    return `<li class="markdown-content__task"><input type="checkbox" disabled${checkedAttribute}> `;
  });
}
</script>

<template>
  <div class="markdown-content" v-html="renderedContent"></div>
</template>
