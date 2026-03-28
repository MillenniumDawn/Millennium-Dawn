import { readFileSync } from "node:fs";
import type { Root } from "hast";
import imageSize from "image-size";
import { visit } from "unist-util-visit";
import { resolveLocalRasterImageFile } from "../media/docs-content-paths";

const RASTER_EXT = /\.(png|jpe?g|webp|avif|gif)$/i;

const dimensionCache = new Map<string, { width: number; height: number }>();

/**
 * Inject `width`/`height` on `<img>` for resolvable local rasters so layout is stable before paint.
 * Pages that render markdown via `MarkdownImage` may still get dimensions here from the hast pipeline;
 * this avoids layout shift when the HTML path does not go through that component.
 */
export function rehypeImageDimensions(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, "element", (node) => {
      if (node.tagName !== "img") return;

      const src = node.properties?.src;
      if (typeof src !== "string") return;

      const hasWidth = node.properties?.width !== undefined && node.properties?.width !== "";
      const hasHeight = node.properties?.height !== undefined && node.properties?.height !== "";
      if (hasWidth && hasHeight) return;

      const fsPath = resolveLocalRasterImageFile(src);
      if (!fsPath || !RASTER_EXT.test(fsPath)) return;

      let dim = dimensionCache.get(fsPath);
      if (!dim) {
        try {
          const read = imageSize(readFileSync(fsPath));
          if (!read.width || !read.height) return;
          dim = { width: read.width, height: read.height };
          dimensionCache.set(fsPath, dim);
        } catch {
          return;
        }
      }

      node.properties = {
        ...node.properties,
        width: String(dim.width),
        height: String(dim.height),
      };
    });
  };
}
