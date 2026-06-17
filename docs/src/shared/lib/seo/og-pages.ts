import { getCollection } from "astro:content";
import { STATIC_PAGE_META } from "./page-meta";
import { getGenericPagePermalink } from "@/shared/lib/routing/generic-page-routes";
import { SITE_DESCRIPTION } from "@/shared/config/site";
import {
  getChangelogPath,
  getCountryPath,
  getDevDiaryPath,
  getLastPathSegment,
  getMiscPath,
  getResourcePath,
  getTutorialPath,
} from "@/shared/lib/routing/content-routes";

export interface OgPageData {
  slug: string;
  title: string;
  description: string;
}

const DEFAULT_DESCRIPTION = SITE_DESCRIPTION;

async function getStaticPages(): Promise<OgPageData[]> {
  const pages: OgPageData[] = [
    ...Object.values(STATIC_PAGE_META).map((page) => ({
      slug: page.ogSlug,
      title: page.title,
      description: page.description,
    })),
  ];

  const contentPages = await getCollection("pages");
  for (const entry of contentPages) {
    const permalink = getGenericPagePermalink(entry);
    pages.push({
      slug: getLastPathSegment(permalink),
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  return pages;
}

async function collectDynamicPages(): Promise<OgPageData[]> {
  const pages: OgPageData[] = [];

  const [countryEntries, changelogEntries, devDiaryEntries, tutorialEntries, resourceEntries, miscEntries] =
    await Promise.all([
      getCollection("countries"),
      getCollection("changelogSections"),
      getCollection("devDiaries"),
      getCollection("tutorials"),
      getCollection("resources"),
      getCollection("misc"),
    ]);

  for (const entry of countryEntries) {
    pages.push({
      slug: getCountryPath(entry).replace(/^\/+|\/+$/g, ""),
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of changelogEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: getChangelogPath(entry).replace(/^\/+|\/+$/g, ""),
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of devDiaryEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: getDevDiaryPath(entry).replace(/^\/+|\/+$/g, ""),
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of tutorialEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: getTutorialPath(entry).replace(/^\/+|\/+$/g, ""),
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of resourceEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: getResourcePath(entry).replace(/^\/+|\/+$/g, ""),
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of miscEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: getMiscPath(entry).replace(/^\/+|\/+$/g, ""),
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  return pages;
}

export async function getAllOgPages(): Promise<OgPageData[]> {
  const [staticPages, dynamicPages] = await Promise.all([getStaticPages(), collectDynamicPages()]);
  return [...staticPages, ...dynamicPages];
}
