import type { GetStaticPaths, APIRoute } from "astro";
import { getAllOgPages, type OgPageData } from "@/shared/lib/og-pages";
import { generateOgImage } from "@/shared/lib/og-image";

export const getStaticPaths: GetStaticPaths = async () => {
  const pages = await getAllOgPages();
  return pages.map((page) => ({
    params: { slug: page.slug || undefined },
    props: { page },
  }));
};

export const GET: APIRoute = async ({ props }) => {
  const page = props.page as OgPageData;
  const png = await generateOgImage(page);
  return new Response(new Blob([png], { type: "image/png" }), {
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
};
