import { fileURLToPath } from "node:url";
import type { AstroUserConfig } from "astro";
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import { markdownProcessor } from "./src/shared/lib/markdown/markdown-processor";
import { hoiscriptLanguage } from "./src/shared/lib/markdown/shiki-hoiscript";
import { SITE_BASE_PATH, SITE_FALLBACK_ORIGIN } from "./src/shared/config/site";
import { copySrcImagesToDist } from "./src/integrations/copy-src-images-to-dist";
import { getSitemapExcludedUrls } from "./src/integrations/sitemap-excluded-paths";
import { viteServeSrcImages } from "./src/integrations/vite-serve-src-images";

const docsPackageRoot = fileURLToPath(new URL(".", import.meta.url));
const sitemapExcludedUrls = getSitemapExcludedUrls();

// Astro and @tailwindcss/vite currently resolve different Vite type instances.
const tailwindPlugins = tailwindcss() as unknown as NonNullable<NonNullable<AstroUserConfig["vite"]>["plugins"]>;
const vitePlugins = [
  viteServeSrcImages(docsPackageRoot),
  ...(Array.isArray(tailwindPlugins) ? tailwindPlugins : [tailwindPlugins]),
];

export default defineConfig({
  site: SITE_FALLBACK_ORIGIN,
  base: SITE_BASE_PATH,
  output: "static",
  trailingSlash: "always",
  integrations: [
    mdx(),
    sitemap({
      filter: (page) => !sitemapExcludedUrls.has(page),
    }),
    copySrcImagesToDist(),
  ],
  vite: {
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    plugins: vitePlugins,
  },
  markdown: {
    syntaxHighlight: {
      type: "shiki",
      excludeLangs: ["math"],
    },
    shikiConfig: {
      langs: [hoiscriptLanguage],
    },
    processor: markdownProcessor,
  },
});
