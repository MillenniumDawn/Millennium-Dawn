import { unified } from "@astrojs/markdown-remark";
import remarkDirective from "remark-directive";
import rehypeExternalLinks from "rehype-external-links";
import rehypeSanitize from "rehype-sanitize";
import { SITE_BASE_PATH } from "../../config/site";
import { markdownSanitizeSchema } from "./markdown-sanitize-schema";
import { remarkCountryDirectives } from "./remark-country-directives";
import { remarkRootRelativeToBase } from "./remark-root-relative";
import { rehypeImageDimensions } from "./rehype-image-dimensions";
import { rehypePreWrapper } from "./rehype-pre-wrapper";
import { rehypeTableScope } from "./rehype-table-scope";
import { rehypeTableWrapper } from "./rehype-table-wrapper";
import { rehypeTailwindContent } from "./rehype-tailwind-content";

export const markdownProcessor = unified({
  remarkPlugins: [remarkDirective, remarkCountryDirectives, [remarkRootRelativeToBase, SITE_BASE_PATH]],
  rehypePlugins: [
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
});
