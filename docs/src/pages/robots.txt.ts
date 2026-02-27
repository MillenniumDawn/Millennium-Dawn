import type { APIRoute } from "astro";
import { SITE_BASE } from "../lib/urls";

export const GET: APIRoute = ({ site }) => {
  const origin = site ? site.origin : "https://millenniumdawn.github.io";
  const body = [`Sitemap: ${origin}${SITE_BASE}/sitemap-index.xml`].join("\n");

  return new Response(body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
};
