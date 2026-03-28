import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import type { AstroIntegration } from "astro";

const DOCS_PACKAGE_ROOT = fileURLToPath(new URL("../..", import.meta.url));

/**
 * Emit a static mirror of `src/assets/images` at `dist/assets/images` so root-relative
 * `/assets/images/...` URLs in HTML (e.g. markdown fallbacks) resolve during `check_site_links`.
 * Optimized `/_astro/*` assets are unchanged.
 *
 * **Contract:** This integration owns `dist/assets/images` after each build (`rmSync` then full copy).
 * Do not add a separate build step that writes other files under that directory, or they will be removed.
 */
export function copySrcImagesToDist(): AstroIntegration {
  return {
    name: "copy-src-images-to-dist",
    hooks: {
      "astro:build:done": ({ dir }) => {
        const distDir = fileURLToPath(dir);
        const srcImagesDir = join(DOCS_PACKAGE_ROOT, "src", "assets", "images");
        if (!existsSync(srcImagesDir)) return;

        const destDir = join(distDir, "assets", "images");
        rmSync(destDir, { recursive: true, force: true });
        mkdirSync(join(distDir, "assets"), { recursive: true });
        cpSync(srcImagesDir, destDir, { recursive: true });
      },
    },
  };
}
