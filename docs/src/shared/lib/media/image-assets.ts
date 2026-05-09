import type { ImageMetadata } from "astro";

const imageAssets = import.meta.glob<ImageMetadata>("../../assets/images/**/*.{png,jpg,jpeg,webp,avif,gif,svg}", {
  eager: true,
  import: "default",
});

/** Map Vite glob keys (relative or absolute, any slash style) to public URL paths `/assets/images/...`. */
function modulePathToAssetUrl(modulePath: string): string | null {
  const posixPath = modulePath.replace(/\\/g, "/");
  const fromSrc = "src/assets/images/";
  const i = posixPath.indexOf(fromSrc);
  if (i !== -1) {
    return `/assets/images/${posixPath.slice(i + fromSrc.length)}`;
  }
  const rel = posixPath.replace(/^\.\.\/\.\.\/assets\/images\/?/, "/assets/images/");
  return rel.startsWith("/assets/images/") ? rel : null;
}

const assetMap = new Map<string, ImageMetadata>();
const rootUrlByMetadata = new WeakMap<ImageMetadata, string>();
for (const [modulePath, metadata] of Object.entries(imageAssets)) {
  const key = modulePathToAssetUrl(modulePath);
  if (key) {
    assetMap.set(key, metadata);
    rootUrlByMetadata.set(metadata, key);
  }
}

export function getInternalImageAsset(src: string): ImageMetadata | undefined {
  return assetMap.get(src);
}

/** Root-relative `/assets/images/...` URL for an imported metadata object, if it is in the asset map. */
export function getRootRelativeUrlForMetadata(meta: ImageMetadata): string | undefined {
  return rootUrlByMetadata.get(meta);
}

export function resolveImageSource(src: string | ImageMetadata): string | ImageMetadata {
  if (typeof src !== "string") return src;
  return getInternalImageAsset(src) ?? src;
}
