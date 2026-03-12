import { access } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { imageSizeFromFile } from "image-size/fromFile";

interface PublicImageDimensions {
  width: number;
  height: number;
}

const publicRoot = fileURLToPath(new URL("../../../public", import.meta.url));
const sizeCache = new Map<string, Promise<PublicImageDimensions | null>>();

async function readPublicImageDimensions(src: string): Promise<PublicImageDimensions | null> {
  if (!src.startsWith("/") || src.startsWith("//")) return null;

  const publicFilePath = resolve(publicRoot, `.${src}`);
  if (!publicFilePath.startsWith(publicRoot)) return null;

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
  const cached = sizeCache.get(src);
  if (cached) return cached;

  const pending = readPublicImageDimensions(src);
  sizeCache.set(src, pending);
  return pending;
}
