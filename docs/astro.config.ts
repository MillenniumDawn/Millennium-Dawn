import { fileURLToPath } from "node:url";
import type { AstroUserConfig } from "astro";
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import remarkDirective from "remark-directive";
import rehypeExternalLinks from "rehype-external-links";
import { remarkCountryDirectives } from "./src/shared/lib/markdown/remark-country-directives";
import { remarkRootRelativeToBase } from "./src/shared/lib/markdown/remark-root-relative";
import { rehypeTailwindContent } from "./src/shared/lib/markdown/rehype-tailwind-content";
import { rehypePreWrapper } from "./src/shared/lib/markdown/rehype-pre-wrapper";
import { rehypeImgAlt } from "./src/shared/lib/markdown/rehype-img-alt";
import { rehypeImageDimensions } from "./src/shared/lib/markdown/rehype-image-dimensions";
import { rehypeTableScope } from "./src/shared/lib/markdown/rehype-table-scope";
import { rehypeTableWrapper } from "./src/shared/lib/markdown/rehype-table-wrapper";
import { hoiscriptLanguage } from "./src/shared/lib/markdown/shiki-hoiscript";
import { SITE_BASE_PATH, SITE_FALLBACK_ORIGIN } from "./src/shared/config/site";
import { copySrcImagesToDist } from "./src/integrations/copy-src-images-to-dist";
import { getSitemapExcludedUrls } from "./src/integrations/sitemap-excluded-paths";
import { viteServeSrcImages } from "./src/integrations/vite-serve-src-images";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";

const docsPackageRoot = fileURLToPath(new URL(".", import.meta.url));
const sitemapExcludedUrls = getSitemapExcludedUrls();
const markdownSanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    "*": [...(defaultSchema.attributes?.["*"] ?? []), "class", "className"],
  },
};

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
    remarkPlugins: [remarkDirective, remarkCountryDirectives, [remarkRootRelativeToBase, SITE_BASE_PATH]],
    rehypePlugins: [
      rehypeImgAlt,
      rehypeImageDimensions,
      [
        rehypeExternalLinks,
        {
          target: "_blank",
          rel: ["noopener", "noreferrer"],
          content: { type: "text", value: " (opens in new tab)" },
        },
      ],
      rehypeTableScope,
      rehypeTableWrapper,
      rehypePreWrapper,
      rehypeTailwindContent,
      [rehypeSanitize, markdownSanitizeSchema],
    ],
  },
});
