import { toAbsolute, withBase } from "./urls";
import { SITE_DESCRIPTION } from "../shared/config/site";

export interface SeoImage {
  path: string;
  width?: number;
  height?: number;
  alt?: string;
}

export interface SeoMeta {
  title: string;
  description: string;
  canonical: string;
  robots?: string;
  image?: SeoImage;
  seoEnabled: boolean;
}

const DEFAULT_DESCRIPTION = SITE_DESCRIPTION;

function ogImagePath(canonicalPath: string): string {
  const slug = canonicalPath.replace(/^\/+|\/+$/g, "");
  return slug ? `/open-graph/${slug}.png` : "/open-graph/index.png";
}

function defaultOgImage(canonicalPath: string, title: string): SeoImage {
  return {
    path: ogImagePath(canonicalPath),
    width: 1200,
    height: 630,
    alt: title,
  };
}

export function buildSeoMeta(input: {
  title: string;
  description?: string;
  canonicalPath: string;
  robots?: string;
  seo?: boolean;
  image?: SeoImage;
}): SeoMeta {
  const canonicalPath = input.canonicalPath ?? "/";
  return {
    title: input.title,
    description: input.description ?? DEFAULT_DESCRIPTION,
    canonical: toAbsolute(canonicalPath),
    robots: input.robots,
    seoEnabled: input.seo !== false,
    image: input.image
      ? { ...input.image, path: withBase(input.image.path) }
      : {
          ...defaultOgImage(canonicalPath, input.title),
          path: withBase(defaultOgImage(canonicalPath, input.title).path),
        },
  };
}
