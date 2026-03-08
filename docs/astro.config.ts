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

// Astro and @tailwindcss/vite currently resolve different Vite type instances.
const tailwindPlugins =
  tailwindcss() as unknown as NonNullable<NonNullable<AstroUserConfig["vite"]>["plugins"]>;

const siteBase = "/Millennium-Dawn";

export default defineConfig({
  site: "https://millenniumdawn.github.io",
  base: siteBase,
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
    remarkPlugins: [remarkDirective, remarkCountryDirectives, [remarkRootRelativeToBase, siteBase]],
    rehypePlugins: [rehypeTableWrapper],
  },
});
