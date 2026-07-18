import {
  SITE_DESCRIPTION,
  SITE_DISCORD_URL,
  SITE_FALLBACK_ORIGIN,
  SITE_ORGANIZATION_NAME,
  SITE_TITLE,
} from "@/shared/config/site";
import { toAbsolute, withBase } from "@/shared/lib/routing/urls";

interface SectionMeta {
  title: string;
  url: string;
}

export function buildVideoGameJsonLd(): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "VideoGame",
    name: SITE_TITLE,
    description: SITE_DESCRIPTION,
    url: toAbsolute("/"),
    applicationCategory: "Game",
    gamePlatform: "PC",
    operatingSystem: "Windows, macOS, Linux",
    genre: "Grand strategy",
    isPartOf: {
      "@type": "VideoGame",
      name: "Hearts of Iron IV",
    },
    publisher: {
      "@type": "Organization",
      name: SITE_ORGANIZATION_NAME,
      url: toAbsolute("/"),
    },
    sameAs: [SITE_DISCORD_URL, `${SITE_FALLBACK_ORIGIN}${withBase("/")}`],
  };
}

export function buildBreadcrumbListJsonLd(input: {
  path: string;
  title?: string;
  sections?: Record<string, SectionMeta>;
}): Record<string, unknown> | null {
  const segments = (input.path || "/")
    .split("/")
    .filter(Boolean)
    .filter((segment) => segment !== "index.html");

  if (segments.length <= 1) return null;

  const itemListElement = [
    {
      "@type": "ListItem",
      position: 1,
      name: "Home",
      item: toAbsolute("/"),
    },
  ];

  segments.forEach((segment, index) => {
    const isLast = index === segments.length - 1;
    const section = input.sections?.[segment];
    const segmentPath = `/${segments.slice(0, index + 1).join("/")}/`;
    const segmentTitle = section?.title ?? segment.replace(/-/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
    const segmentHref = section?.url ?? segmentPath;

    itemListElement.push({
      "@type": "ListItem",
      position: index + 2,
      name: isLast ? (input.title ?? segmentTitle) : segmentTitle,
      item: toAbsolute(segmentHref),
    });
  });

  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement,
  };
}

export function buildArticleJsonLd(input: {
  headline: string;
  description?: string;
  canonicalPath: string;
  datePublished?: string;
  dateModified?: string;
  author?: string;
  imageUrl?: string;
}): Record<string, unknown> {
  const article: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: input.headline,
    description: input.description,
    url: toAbsolute(input.canonicalPath),
    mainEntityOfPage: toAbsolute(input.canonicalPath),
    publisher: {
      "@type": "Organization",
      name: SITE_ORGANIZATION_NAME,
      url: toAbsolute("/"),
    },
  };

  if (input.datePublished) article.datePublished = input.datePublished;
  if (input.dateModified) article.dateModified = input.dateModified;
  if (input.author) {
    article.author = {
      "@type": "Person",
      name: input.author,
    };
  }
  if (input.imageUrl) article.image = input.imageUrl;

  return article;
}
