import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

export const OG_WIDTH = 1200;
export const OG_HEIGHT = 630;
export const OG_FONT_FAMILY = "KaTeX Sans Serif";

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

export interface LoadedFonts {
  regular: ArrayBuffer;
  bold: ArrayBuffer;
}

export interface BrandingAssets {
  logo: string;
  hero: string;
}

let fontCache: LoadedFonts | null = null;
let brandingCache: BrandingAssets | null = null;

export function toArrayBuffer(buffer: Buffer): ArrayBuffer {
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength) as ArrayBuffer;
}

function readFileDataUri(filePath: string, mimeType: string): string {
  const fileBuffer = fs.readFileSync(filePath);
  return `data:${mimeType};base64,${fileBuffer.toString("base64")}`;
}

export function loadOgFonts(): LoadedFonts {
  if (fontCache) {
    return fontCache;
  }

  fontCache = {
    regular: toArrayBuffer(fs.readFileSync(FONT_PATHS.regular)),
    bold: toArrayBuffer(fs.readFileSync(FONT_PATHS.bold)),
  };

  return fontCache;
}

export function loadOgBrandingAssets(): BrandingAssets {
  if (brandingCache) {
    return brandingCache;
  }

  brandingCache = {
    logo: readFileDataUri(IMAGE_PATHS.logo, "image/png"),
    hero: readFileDataUri(IMAGE_PATHS.hero, "image/jpeg"),
  };

  return brandingCache;
}
