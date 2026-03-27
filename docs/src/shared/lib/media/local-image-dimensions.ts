import { readFileSync } from "node:fs";
import imageSize from "image-size";
import { imageSizeFromFile } from "image-size/fromFile";
import { resolveLocalRasterImageFile, stripPublicationBase } from "./docs-content-paths";

const RASTER_EXT = /\.(png|jpe?g|webp|avif|gif)$/i;

interface RasterImageDimensions {
  width: number;
  height: number;
}

/** Keys match `resolveLocalRasterImageFile` (publication-relative path after base strip). */
const sizeCache = new Map<string, Promise<RasterImageDimensions | null>>();

/**
 * Width/height for a local raster (same rules as `resolveLocalRasterImageFile`: `/assets/images/` →
 * `src/assets/images/` only; other paths may use `public/`). Used when `getInternalImageAsset` has no entry.
 */
async function readLocalImageDimensions(src: string): Promise<RasterImageDimensions | null> {
  const fsPath = resolveLocalRasterImageFile(src);
  if (!fsPath) return null;

  try {
    const dimensions = await imageSizeFromFile(fsPath);
    if (!dimensions.width || !dimensions.height) return null;
    return {
      width: dimensions.width,
      height: dimensions.height,
    };
  } catch {
    return null;
  }
}

export function getLocalImageDimensions(src: string): Promise<RasterImageDimensions | null> {
  const cacheKey = stripPublicationBase(src);
  const cached = sizeCache.get(cacheKey);
  if (cached) return cached;

  const pending = readLocalImageDimensions(src);
  sizeCache.set(cacheKey, pending);
  return pending;
}

/** Sync probe for SSR when async `imageSizeFromFile` or cache ordering is unreliable; same path rules as `resolveLocalRasterImageFile`. */
export function getLocalRasterDimensionsSyncFromUrl(srcAttr: string): RasterImageDimensions | null {
  const fsPath = resolveLocalRasterImageFile(srcAttr);
  if (!fsPath || !RASTER_EXT.test(fsPath)) return null;
  try {
    const dim = imageSize(readFileSync(fsPath));
    if (!dim.width || !dim.height) return null;
    return { width: dim.width, height: dim.height };
  } catch {
    return null;
  }
}
