import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import remarkDirective from "remark-directive";
import { remarkCountryDirectives } from "./src/lib/remark-country-directives.js";
import { remarkRootRelativeToBase } from "./src/lib/remark-root-relative.js";

export default defineConfig({
  site: "https://millenniumdawn.github.io",
  base: "/Millennium-Dawn",
  output: "static",
  trailingSlash: "always",
  integrations: [mdx(), sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
  markdown: {
    remarkPlugins: [remarkDirective, remarkCountryDirectives, remarkRootRelativeToBase],
  },
});
