import fs from "node:fs";
import path from "node:path";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import type { OgPageData } from "./og-pages";

const OG_WIDTH = 1200;
const OG_HEIGHT = 630;

const INTER_FONT_URL =
  "https://cdn.jsdelivr.net/fontsource/fonts/inter@latest/latin-400-normal.ttf";
const INTER_BOLD_FONT_URL =
  "https://cdn.jsdelivr.net/fontsource/fonts/inter@latest/latin-700-normal.ttf";

let fontCache: { regular: ArrayBuffer; bold: ArrayBuffer } | null = null;

async function loadFonts(): Promise<{ regular: ArrayBuffer; bold: ArrayBuffer }> {
  if (fontCache) return fontCache;

  const [regular, bold] = await Promise.all([
    fetch(INTER_FONT_URL).then((r) => r.arrayBuffer()),
    fetch(INTER_BOLD_FONT_URL).then((r) => r.arrayBuffer()),
  ]);

  fontCache = { regular, bold };
  return fontCache;
}

let logoDataUri: string | null = null;

function getLogoDataUri(): string {
  if (logoDataUri) return logoDataUri;
  const logoPath = path.resolve("assets/images/branding/main-menu.png");
  const logoBuffer = fs.readFileSync(logoPath);
  logoDataUri = `data:image/png;base64,${logoBuffer.toString("base64")}`;
  return logoDataUri;
}

let heroDataUri: string | null = null;

function getHeroDataUri(): string {
  if (heroDataUri) return heroDataUri;
  const heroPath = path.resolve("assets/images/branding/hero.jpeg");
  const heroBuffer = fs.readFileSync(heroPath);
  heroDataUri = `data:image/jpeg;base64,${heroBuffer.toString("base64")}`;
  return heroDataUri;
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 1) + "…";
}

// Dark theme background colour (#1a202c) used for gradient stops.
const BG = "26,32,44";

export async function generateOgImage(page: OgPageData): Promise<ArrayBuffer> {
  const fonts = await loadFonts();
  const logo = getLogoDataUri();
  const hero = getHeroDataUri();
  const isHome = page.slug === "index";
  const title = truncate(page.title, 80);
  const description = truncate(page.description, 160);

  // Gradient that darkens from centre-top toward bottom so text is always
  // readable while the hero image remains visible in the upper area.
  const overlayGradient =
    `linear-gradient(to bottom, rgba(${BG},0.40) 0%, rgba(${BG},0.78) 48%, rgba(${BG},0.96) 100%)`;

  const markup = {
    type: "div" as const,
    props: {
      // Outer shell: hero image as background
      style: {
        width: "100%",
        height: "100%",
        display: "flex",
        backgroundImage: `url("${hero}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      },
      children: {
        // Inner shell: gradient overlay + all content
        type: "div" as const,
        props: {
          style: {
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column" as const,
            backgroundImage: overlayGradient,
            padding: "60px 70px",
            fontFamily: "Inter",
            color: "#ffffff",
          },
          children: isHome
        ? [
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
                      children: "Millennium Dawn",
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
                      children: "A Modern Day Mod for Hearts of Iron IV",
                    },
                  },
                ],
              },
            },
          ]
          : [
            // Top bar with logo
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
            // Spacer
            {
              type: "div" as const,
              props: {
                style: { display: "flex", flex: 1 },
                children: [],
              },
            },
            // Title
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
            // Description
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
            // Bottom bar
            {
              type: "div" as const,
              props: {
                style: {
                  display: "flex",
                  marginTop: "30px",
                  fontSize: "20px",
                  color: "#94a3b8",
                },
                children: "Millennium Dawn: A Modern Day Mod",
              },
            },
          ],
        },
      },
    },
  };

  const svg = await satori(markup, {
    width: OG_WIDTH,
    height: OG_HEIGHT,
    fonts: [
      { name: "Inter", data: fonts.regular, weight: 400, style: "normal" },
      { name: "Inter", data: fonts.bold, weight: 700, style: "normal" },
    ],
  });

  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: OG_WIDTH },
  });

  const pngData = resvg.render().asPng();
  // Return a properly-typed ArrayBuffer so Response() accepts it without
  // TypeScript errors (Uint8Array<ArrayBufferLike> is not assignable to BodyInit).
  return pngData.buffer as ArrayBuffer;
}
