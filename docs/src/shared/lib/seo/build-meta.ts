import { toAbsolute, withBase } from "@/shared/lib/routing/urls";
import { SITE_DESCRIPTION } from "@/shared/config/site";

export interface SeoImage {
  path: string;
  width?: number;
  height?: number;
  alt?: string;
}

export interface ArticleSeoMeta {
  publishedTime?: string;
  modifiedTime?: string;
  author?: string;
}

export interface SeoMeta {
  title: string;
  description: string;
  canonical: string;
  robots?: string;
  image?: SeoImage;
  seoEnabled: boolean;
  ogType?: "website" | "article";
  article?: ArticleSeoMeta;
  extraJsonLd?: Record<string, unknown>[];
}

const DEFAULT_DESCRIPTION = SITE_DESCRIPTION;

export function ogImagePath(canonicalPath: string): string {
  const slug = canonicalPath.replace(/^\/+|\/+$/g, "");
  return slug ? `/open-graph/${slug}.png` : "/open-graph/index.png";
}

export function ogImageAbsoluteUrl(canonicalPath: string): string {
  return toAbsolute(ogImagePath(canonicalPath));
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
  ogType?: "website" | "article";
  article?: ArticleSeoMeta;
  extraJsonLd?: Record<string, unknown>[];
}): SeoMeta {
  const canonicalPath = input.canonicalPath ?? "/";
  return {
    title: input.title,
    description: input.description ?? DEFAULT_DESCRIPTION,
    canonical: toAbsolute(canonicalPath),
    robots: input.robots,
    seoEnabled: input.seo !== false,
    ogType: input.ogType,
    article: input.article,
    extraJsonLd: input.extraJsonLd,
    image: input.image
      ? { ...input.image, path: withBase(input.image.path) }
      : {
          ...defaultOgImage(canonicalPath, input.title),
          path: withBase(defaultOgImage(canonicalPath, input.title).path),
        },
  };
}
