import { defineMiddleware } from "astro:middleware";

/**
 * Workaround for Astro dev server with `trailingSlash: "always"`.
 *
 * Non-HTML endpoints (e.g. `.png`, `.xml`, `.json`) should never require a
 * trailing slash, but the dev server rejects requests without one.  This
 * middleware internally rewrites such requests so the endpoint is matched.
 */
export const onRequest = defineMiddleware((context, next) => {
  if (!import.meta.env.DEV) return next();

  const { pathname } = context.url;

  // Only rewrite OG image endpoint URLs — static assets must pass through to Vite.
  if (pathname.includes("/open-graph/") && pathname.endsWith(".png")) {
    return context.rewrite(new Request(new URL(pathname + "/", context.url), context.request));
  }

  return next();
});
