import { access } from "node:fs/promises";
import { resolve } from "node:path";
import { imageSizeFromFile } from "image-size/fromFile";
import { getDocsPublicRoot } from "./docs-content-paths";
import { isContainedInRoot } from "./fs-path-safety";
import { normalizeSiteBase, stripPathBase } from "./site-path-base";

interface PublicImageDimensions {
  width: number;
  height: number;
}

const SITE_BASE_NORMALIZED = normalizeSiteBase(import.meta.env.BASE_URL);

const sizeCache = new Map<string, Promise<PublicImageDimensions | null>>();

async function readPublicImageDimensions(src: string): Promise<PublicImageDimensions | null> {
  const normalized = stripPathBase(src, SITE_BASE_NORMALIZED);
  if (!normalized.startsWith("/") || normalized.startsWith("//")) return null;

  const publicRoot = getDocsPublicRoot();
  const segments = normalized.replace(/^\/+/, "").split("/").filter(Boolean);
  if (segments.some((s) => s === "..")) return null;

  const publicFilePath = resolve(publicRoot, ...segments);
  if (!isContainedInRoot(publicRoot, publicFilePath)) return null;

  try {
    await access(publicFilePath);
    const dimensions = await imageSizeFromFile(publicFilePath);
    if (!dimensions.width || !dimensions.height) return null;
    return {
      width: dimensions.width,
      height: dimensions.height,
    };
  } catch {
    return null;
  }
}

export function getPublicImageDimensions(src: string): Promise<PublicImageDimensions | null> {
  const normalized = stripPathBase(src, SITE_BASE_NORMALIZED);
  const cached = sizeCache.get(normalized);
  if (cached) return cached;

  const pending = readPublicImageDimensions(src);
  sizeCache.set(normalized, pending);
  return pending;
}
