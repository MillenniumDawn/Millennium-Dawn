import type { AstroUserConfig } from "astro";
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import remarkDirective from "remark-directive";
import { remarkCountryDirectives } from "./src/lib/remark-country-directives";
import { remarkRootRelativeToBase } from "./src/lib/remark-root-relative";
import { rehypeTableWrapper } from "./src/lib/rehype-table-wrapper";
import { hoiscriptLanguage } from "./src/lib/shiki-hoiscript";
import { SITE_BASE_PATH, SITE_FALLBACK_ORIGIN } from "./src/shared/config/site";

// Astro and @tailwindcss/vite currently resolve different Vite type instances.
const tailwindPlugins =
  tailwindcss() as unknown as NonNullable<NonNullable<AstroUserConfig["vite"]>["plugins"]>;

export default defineConfig({
  site: SITE_FALLBACK_ORIGIN,
  base: SITE_BASE_PATH,
  output: "static",
  trailingSlash: "always",
  integrations: [mdx(), sitemap()],
  vite: {
    plugins: tailwindPlugins,
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
    rehypePlugins: [rehypeTableWrapper],
  },
});
