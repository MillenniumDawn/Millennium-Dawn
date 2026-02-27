import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import remarkDirective from "remark-directive";
import { remarkCountryDirectives } from "./src/lib/remark-country-directives";
import { remarkRootRelativeToBase } from "./src/lib/remark-root-relative";
import { rehypeTableWrapper } from "./src/lib/rehype-table-wrapper";
import { hoiscriptLanguage } from "./src/lib/shiki-hoiscript";

export default defineConfig({
  site: "https://millenniumdawn.github.io",
  base: "/Millennium-Dawn",
  output: "static",
  trailingSlash: "always",
  integrations: [mdx(), sitemap()],
  vite: {
    plugins: [tailwindcss() as any],
  },
  markdown: {
    syntaxHighlight: {
      type: "shiki",
      excludeLangs: ["math"],
    },
    shikiConfig: {
      langs: [hoiscriptLanguage],
    },
    remarkPlugins: [remarkDirective, remarkCountryDirectives, remarkRootRelativeToBase],
    rehypePlugins: [rehypeTableWrapper],
  },
});
