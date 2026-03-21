import type { APIRoute } from "astro";
import { SITE_BASE } from "@/shared/lib/urls";
import { SITE_FALLBACK_ORIGIN } from "@/shared/config/site";

export const GET: APIRoute = ({ site }) => {
  const origin = site ? site.origin : SITE_FALLBACK_ORIGIN;
  const body = ["User-agent: *", "Allow: /", "", `Sitemap: ${origin}${SITE_BASE}/sitemap-index.xml`].join("\n");

  return new Response(body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
};
