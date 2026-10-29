import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import type { OgPageData } from "./og-pages";
import { buildOgMarkup } from "./og-template";
import { OG_FONT_FAMILY, OG_HEIGHT, OG_WIDTH, loadOgBrandingAssets, loadOgFonts, toArrayBuffer } from "./og-assets";

export async function generateOgImage(page: OgPageData): Promise<ArrayBuffer> {
  const fonts = loadOgFonts();
  const assets = loadOgBrandingAssets();

  const svg = await satori(buildOgMarkup(page, assets), {
    width: OG_WIDTH,
    height: OG_HEIGHT,
    fonts: [
      { name: OG_FONT_FAMILY, data: fonts.regular, weight: 400, style: "normal" },
      { name: OG_FONT_FAMILY, data: fonts.bold, weight: 700, style: "normal" },
    ],
  });

  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: OG_WIDTH },
  });

  return toArrayBuffer(resvg.render().asPng());
}
