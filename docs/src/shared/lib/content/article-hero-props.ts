import type { CollectionEntry } from "astro:content";

export interface ArticleHeroProps {
  eyebrow: string;
  title: string;
  description?: string;
  metaItems?: { label: string; value: string; datetime?: string }[];
  tags?: string[];
}

function extractVersionFromTitle(title: string): string | undefined {
  const match = /^v[\d.]+/i.exec(title);
  return match?.[0];
}

export function getChangelogHeroProps(entry: CollectionEntry<"changelogSections">): ArticleHeroProps {
  const version = extractVersionFromTitle(entry.data.title);
  const metaItems: ArticleHeroProps["metaItems"] = [];
  if (version) metaItems.push({ label: "Version", value: version });
  if (typeof entry.data.order === "number") {
    metaItems.push({ label: "Release", value: `#${entry.data.order}` });
  }

  return {
    eyebrow: "Changelog",
    title: entry.data.title,
    description: entry.data.description,
    metaItems: metaItems.length > 0 ? metaItems : undefined,
  };
}

export function getResourceHeroProps(entry: CollectionEntry<"resources">): ArticleHeroProps {
  return {
    eyebrow: "Developer Resource",
    title: entry.data.title,
    description: entry.data.description,
  };
}

export function getTutorialHeroProps(entry: CollectionEntry<"tutorials">): ArticleHeroProps {
  return {
    eyebrow: "Player Tutorial",
    title: entry.data.title,
    description: entry.data.description,
  };
}
