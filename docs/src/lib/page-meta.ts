import { SITE_DESCRIPTION } from "../shared/config/site";

export interface StaticPageMeta {
  title: string;
  description: string;
  canonicalPath: string;
  pageId: string;
  ogSlug: string;
}

export const STATIC_PAGE_META = {
  home: {
    title: "Home",
    description: SITE_DESCRIPTION,
    canonicalPath: "/",
    pageId: "home",
    ogSlug: "index",
  },
  changelogs: {
    title: "Changelogs",
    description: "Changelogs for Millennium Dawn: A Modern Day Mod",
    canonicalPath: "/changelogs/",
    pageId: "changelogs",
    ogSlug: "changelogs",
  },
  devDiaries: {
    title: "Dev Diaries",
    description: "Development diaries from the Millennium Dawn mod team, covering new features, changes, and updates.",
    canonicalPath: "/dev-diaries/",
    pageId: "dev-diaries",
    ogSlug: "dev-diaries",
  },
  tutorials: {
    title: "Tutorials",
    description: "Guides and tutorials for playing Millennium Dawn: A Modern Day mod for Hearts of Iron IV.",
    canonicalPath: "/tutorials/",
    pageId: "tutorials",
    ogSlug: "tutorials",
  },
  resources: {
    title: "Resources",
    description: "List of resources for the development team of Millennium Dawn.",
    canonicalPath: "/resources/",
    pageId: "resources",
    ogSlug: "resources",
  },
  support: {
    title: "Technical Support",
    description: "Technical support and troubleshooting help for Millennium Dawn: A Modern Day mod for Hearts of Iron IV.",
    canonicalPath: "/support/",
    pageId: "support",
    ogSlug: "support",
  },
} as const satisfies Record<string, StaticPageMeta>;

export const CONTENT_PAGE_ROUTES = {
  "getting-started": "/getting-started/",
  faq: "/faq/",
  countries: "/countries/",
} as const;
