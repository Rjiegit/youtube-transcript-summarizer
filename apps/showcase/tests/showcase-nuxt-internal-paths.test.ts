import fs from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

describe("Nuxt internal paths shim scripts", () => {
  it("regenerates the Nuxt internal paths shim after production build", () => {
    const packageJson = JSON.parse(
      fs.readFileSync(path.resolve(process.cwd(), "package.json"), "utf8"),
    ) as { scripts?: Record<string, string> };

    expect(packageJson.scripts?.build).toBe(
      "node ./scripts/ensure-nuxt-internal-paths.mjs && nuxt build && node ./scripts/ensure-nuxt-internal-paths.mjs",
    );
  });
});
