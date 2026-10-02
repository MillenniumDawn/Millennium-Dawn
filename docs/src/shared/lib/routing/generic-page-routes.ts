import { getCollection } from "astro:content";
import type { CollectionEntry } from "astro:content";
import { CONTENT_PAGE_ROUTES } from "@/shared/lib/seo/page-meta";
import { getEntryBaseId } from "./content-routes";

/** Permalinks with dedicated `src/pages/.../index.astro` routes — not served by the catch-all. */
const BESPOKE_PAGE_PERMALINKS = new Set<string>(Object.values(CONTENT_PAGE_ROUTES));

export function getGenericPagePermalink(entry: CollectionEntry<"pages">): string {
  return entry.data.permalink ?? `/${getEntryBaseId(entry)}/`;
}

export function isBespokePageEntry(entry: CollectionEntry<"pages">): boolean {
  return BESPOKE_PAGE_PERMALINKS.has(getGenericPagePermalink(entry));
}

export async function getGenericPageEntries(): Promise<CollectionEntry<"pages">[]> {
  const entries = await getCollection("pages");
  return entries.filter((entry) => !isBespokePageEntry(entry));
}

export function genericPageSlug(entry: CollectionEntry<"pages">): string {
  return getGenericPagePermalink(entry).replace(/^\/+|\/+$/g, "");
}
