import fs from "node:fs";
import path from "node:path";

const nuxtDir = path.resolve(process.cwd(), ".nuxt");
const pathsFile = path.join(nuxtDir, "paths.mjs");

const contents = `import { joinRelativeURL } from "ufo"
const getAppConfig = () => ({ baseURL: "/", buildAssetsDir: "/_nuxt/", cdnURL: "" })
export const baseURL = () => getAppConfig().baseURL
export const buildAssetsDir = () => getAppConfig().buildAssetsDir
export const buildAssetsURL = (...segments) => joinRelativeURL(publicAssetsURL(), buildAssetsDir(), ...segments)
export const publicAssetsURL = (...segments) => {
  const appConfig = getAppConfig()
  const publicBase = appConfig.cdnURL || appConfig.baseURL
  return segments.length ? joinRelativeURL(publicBase, ...segments) : publicBase
}
if (import.meta.client) {
  globalThis.__buildAssetsURL = buildAssetsURL
  globalThis.__publicAssetsURL = publicAssetsURL
}
`;

fs.mkdirSync(nuxtDir, { recursive: true });
if (!fs.existsSync(pathsFile) || fs.readFileSync(pathsFile, "utf8") !== contents) {
  fs.writeFileSync(pathsFile, contents, "utf8");
}
