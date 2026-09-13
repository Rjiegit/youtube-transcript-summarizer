import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const extensionRoot = path.join(repositoryRoot, "apps", "browser-extension");
const manifestPath = path.join(extensionRoot, "manifest.json");
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));

if (manifest.manifest_version !== 3) {
  throw new Error("Browser Extension must use Manifest V3.");
}

const referencedFiles = new Set();
const addReference = (value) => {
  if (typeof value === "string" && value.length > 0) referencedFiles.add(value);
};

addReference(manifest.background?.service_worker);
addReference(manifest.options_page);
addReference(manifest.action?.default_popup);
Object.values(manifest.icons || {}).forEach(addReference);
for (const contentScript of manifest.content_scripts || []) {
  (contentScript.js || []).forEach(addReference);
  (contentScript.css || []).forEach(addReference);
}

for (const relativePath of referencedFiles) {
  const absolutePath = path.join(extensionRoot, relativePath);
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Manifest references missing file: ${relativePath}`);
  }
}

const htmlFiles = [...referencedFiles].filter((file) => file.endsWith(".html"));
for (const htmlFile of htmlFiles) {
  const html = fs.readFileSync(path.join(extensionRoot, htmlFile), "utf8");
  const assetPattern = /(?:src|href)=["']([^"']+)["']/g;
  for (const match of html.matchAll(assetPattern)) {
    const reference = match[1];
    if (/^(?:https?:|data:|#)/.test(reference)) continue;
    const assetPath = path.resolve(extensionRoot, path.dirname(htmlFile), reference);
    if (!fs.existsSync(assetPath)) {
      throw new Error(`${htmlFile} references missing file: ${reference}`);
    }
    if (reference.endsWith(".js")) referencedFiles.add(path.relative(extensionRoot, assetPath));
  }
}

for (const relativePath of referencedFiles) {
  if (!relativePath.endsWith(".js")) continue;
  const source = fs.readFileSync(path.join(extensionRoot, relativePath), "utf8");
  new vm.Script(source, { filename: relativePath });
}

console.log(`Browser Extension validation passed (${referencedFiles.size} referenced files).`);
