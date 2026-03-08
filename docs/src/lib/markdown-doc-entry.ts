import { getCollection, render } from "astro:content";
import type { CollectionEntry } from "astro:content";
import { buildEntryStaticPaths } from "./content-routes";

export type MarkdownDocCollection =
  | "changelogSections"
  | "devDiaries"
  | "misc"
  | "resources"
  | "tutorials";

export async function buildMarkdownDocStaticPaths<C extends MarkdownDocCollection>(
  collection: C,
  getSlug: (entry: CollectionEntry<C>) => string,
) {
  const entries = await getCollection(collection);
  return buildEntryStaticPaths(entries, getSlug);
}

export async function renderMarkdownDocEntry<C extends MarkdownDocCollection>(entry: CollectionEntry<C>) {
  return render(entry);
}
