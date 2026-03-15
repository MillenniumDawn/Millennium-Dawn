import type { ImageMetadata } from "astro";

const imageAssets = import.meta.glob<ImageMetadata>("../../assets/images/**/*.{png,jpg,jpeg,webp,avif,gif,svg}", {
  eager: true,
  import: "default",
});

const assetMap = new Map<string, ImageMetadata>(
  Object.entries(imageAssets).map(([modulePath, metadata]) => {
    const normalized = modulePath.replace(/^\.\.\/\.\.\/assets\/images/, "/assets/images");
    return [normalized, metadata];
  }),
);

export function getInternalImageAsset(src: string): ImageMetadata | undefined {
  return assetMap.get(src);
}

export function resolveImageSource(src: string | ImageMetadata): string | ImageMetadata {
  if (typeof src !== "string") return src;
  return getInternalImageAsset(src) ?? src;
}
