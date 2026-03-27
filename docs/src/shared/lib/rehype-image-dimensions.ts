import { readFileSync } from "node:fs";
import type { Root } from "hast";
import imageSize from "image-size";
import { visit } from "unist-util-visit";
import { resolveLocalRasterImageFile } from "./docs-content-paths";

const RASTER_EXT = /\.(png|jpe?g|webp|avif|gif)$/i;

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

      try {
        const dim = imageSize(readFileSync(fsPath));
        if (!dim.width || !dim.height) return;
        node.properties = {
          ...node.properties,
          width: String(dim.width),
          height: String(dim.height),
        };
      } catch {
        /* ignore missing or corrupt files */
      }
    });
  };
}
