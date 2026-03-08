import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import type { OgPageData } from "./og-pages";
import { SITE_BRAND_TAGLINE, SITE_ORGANIZATION_NAME, SITE_TITLE } from "../shared/config/site";

const OG_WIDTH = 1200;
const OG_HEIGHT = 630;
const FONT_FAMILY = "KaTeX Sans Serif";
const require = createRequire(import.meta.url);
const KATEX_FONTS_DIRECTORY = path.join(path.dirname(require.resolve("katex/package.json")), "dist", "fonts");

const FONT_PATHS = {
  regular: path.join(KATEX_FONTS_DIRECTORY, "KaTeX_SansSerif-Regular.ttf"),
  bold: path.join(KATEX_FONTS_DIRECTORY, "KaTeX_SansSerif-Bold.ttf"),
} as const;

const IMAGE_PATHS = {
  logo: path.resolve("assets/images/branding/main-menu.png"),
  hero: path.resolve("assets/images/branding/hero.jpeg"),
} as const;

interface LoadedFonts {
  regular: ArrayBuffer;
  bold: ArrayBuffer;
}

interface BrandingAssets {
  logo: string;
  hero: string;
}

let fontCache: LoadedFonts | null = null;
let brandingCache: BrandingAssets | null = null;

function toArrayBuffer(buffer: Buffer): ArrayBuffer {
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength) as ArrayBuffer;
}

function readFileDataUri(filePath: string, mimeType: string): string {
  const fileBuffer = fs.readFileSync(filePath);
  return `data:${mimeType};base64,${fileBuffer.toString("base64")}`;
}

function loadFonts(): LoadedFonts {
  if (fontCache) return fontCache;

  fontCache = {
    regular: toArrayBuffer(fs.readFileSync(FONT_PATHS.regular)),
    bold: toArrayBuffer(fs.readFileSync(FONT_PATHS.bold)),
  };

  return fontCache;
}

function loadBrandingAssets(): BrandingAssets {
  if (brandingCache) return brandingCache;

  brandingCache = {
    logo: readFileDataUri(IMAGE_PATHS.logo, "image/png"),
    hero: readFileDataUri(IMAGE_PATHS.hero, "image/jpeg"),
  };

  return brandingCache;
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 1) + "…";
}

function buildHomeContent(logo: string) {
  return [
    {
      type: "div" as const,
      props: {
        style: {
          display: "flex",
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column" as const,
          gap: "20px",
        },
        children: [
          {
            type: "img" as const,
            props: {
              src: logo,
              width: 180,
              height: 180,
              style: { objectFit: "contain" as const },
            },
          },
          {
            type: "div" as const,
            props: {
              style: {
                fontSize: "48px",
                fontWeight: 700,
                textAlign: "center" as const,
                lineHeight: 1.2,
              },
              children: SITE_ORGANIZATION_NAME,
            },
          },
          {
            type: "div" as const,
            props: {
              style: {
                fontSize: "26px",
                fontWeight: 400,
                color: "#cbd5e0",
                textAlign: "center" as const,
              },
              children: SITE_BRAND_TAGLINE,
            },
          },
        ],
      },
    },
  ];
}

function buildPageContent(logo: string, title: string, description: string) {
  return [
    {
      type: "div" as const,
      props: {
        style: {
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "flex-start",
        },
        children: {
          type: "img" as const,
          props: {
            src: logo,
            width: 72,
            height: 72,
            style: { objectFit: "contain" as const },
          },
        },
      },
    },
    {
      type: "div" as const,
      props: {
        style: { display: "flex", flex: 1 },
        children: [],
      },
    },
    {
      type: "div" as const,
      props: {
        style: {
          fontSize: title.length > 40 ? "42px" : "52px",
          fontWeight: 700,
          lineHeight: 1.2,
          marginBottom: "20px",
        },
        children: title,
      },
    },
    {
      type: "div" as const,
      props: {
        style: {
          fontSize: "26px",
          fontWeight: 400,
          color: "#cbd5e0",
          lineHeight: 1.4,
        },
        children: description,
      },
    },
    {
      type: "div" as const,
      props: {
        style: {
          display: "flex",
          marginTop: "30px",
          fontSize: "20px",
          color: "#94a3b8",
        },
        children: SITE_TITLE,
      },
    },
  ];
}

function buildOgMarkup(page: OgPageData, assets: BrandingAssets) {
  const isHome = page.slug === "index";
  const title = truncate(page.title, 80);
  const description = truncate(page.description, 160);
  const overlayGradient =
    "linear-gradient(to bottom, rgba(26,32,44,0.40) 0%, rgba(26,32,44,0.78) 48%, rgba(26,32,44,0.96) 100%)";

  return {
    type: "div" as const,
    props: {
      style: {
        width: "100%",
        height: "100%",
        display: "flex",
        backgroundImage: `url("${assets.hero}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      },
      children: {
        type: "div" as const,
        props: {
          style: {
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column" as const,
            backgroundImage: overlayGradient,
            padding: "60px 70px",
            fontFamily: FONT_FAMILY,
            color: "#ffffff",
          },
          children: isHome
            ? buildHomeContent(assets.logo)
            : buildPageContent(assets.logo, title, description),
        },
      },
    },
  };
}

export async function generateOgImage(page: OgPageData): Promise<ArrayBuffer> {
  const fonts = loadFonts();
  const assets = loadBrandingAssets();

  const svg = await satori(buildOgMarkup(page, assets), {
    width: OG_WIDTH,
    height: OG_HEIGHT,
    fonts: [
      { name: FONT_FAMILY, data: fonts.regular, weight: 400, style: "normal" },
      { name: FONT_FAMILY, data: fonts.bold, weight: 700, style: "normal" },
    ],
  });

  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: OG_WIDTH },
  });

  return toArrayBuffer(resvg.render().asPng());
}
