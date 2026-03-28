import { createReadStream, existsSync, statSync } from "node:fs";
import type { IncomingMessage } from "node:http";
import { extname, join, resolve } from "node:path";
import type { Plugin } from "vite";
import { SITE_BASE_PATH } from "../shared/config/site";

const MIME: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
  ".avif": "image/avif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

function isContainedInRoot(root: string, candidate: string): boolean {
  const r = resolve(root);
  const c = resolve(candidate);
  return c === r || c.startsWith(r + "\\") || c.startsWith(r + "/");
}

/**
 * In `astro dev`, markdown may emit `<img src="/{base}/assets/images/...">` while files live only under
 * `src/assets/images/`. Production uses `copy-src-images-to-dist` after build; dev needs this middleware.
 *
 * Pass the docs package root from `astro.config` (`fileURLToPath(new URL(".", import.meta.url))`).
 * Do not derive it from `docs-content-paths` here: Vite may prebundle that module and skew `import.meta.url`.
 */
export function viteServeSrcImages(docsPackageRoot: string): Plugin {
  const imagesRoot = join(docsPackageRoot, "src", "assets", "images");
  const base = SITE_BASE_PATH.endsWith("/") ? SITE_BASE_PATH.slice(0, -1) : SITE_BASE_PATH;
  const prefix = "/assets/images/";

  return {
    name: "vite-serve-src-images",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use((req: IncomingMessage, res, next) => {
        const raw = req.url?.split("?")[0] ?? "";
        let pathname = raw;
        if (base && (pathname === base || pathname.startsWith(`${base}/`))) {
          pathname = pathname.slice(base.length) || "/";
        }
        if (!pathname.startsWith(prefix)) {
          next();
          return;
        }
        const relative = pathname.slice(prefix.length).replace(/\\/g, "/");
        if (!relative || relative.split("/").some((s) => s === "..")) {
          next();
          return;
        }
        const filePath = resolve(imagesRoot, ...relative.split("/"));
        if (!isContainedInRoot(imagesRoot, filePath) || !existsSync(filePath) || !statSync(filePath).isFile()) {
          next();
          return;
        }
        const ct = MIME[extname(filePath).toLowerCase()] ?? "application/octet-stream";
        res.setHeader("Content-Type", ct);
        createReadStream(filePath).on("error", () => next()).pipe(res);
      });
    },
  };
}
