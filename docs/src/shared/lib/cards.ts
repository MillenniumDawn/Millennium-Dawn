import type { CollectionEntry } from "astro:content";
import { withBase } from "@/shared/lib/urls";

export interface CardItem {
  title: string;
  url?: string;
  kind?: string;
  description?: string;
  meta?: string;
  searchBlob: string;
}

function compactText(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

export function toCardItem(
  entry:
    | CollectionEntry<"tutorials">
    | CollectionEntry<"resources">
    | CollectionEntry<"changelogSections">
    | CollectionEntry<"countries">,
  opts: {
    url: string;
    kind?: string;
    meta?: string;
  },
): CardItem {
  const title = entry.data.title ?? entry.id;
  const description = entry.data.description ?? "";
  const kind = opts.kind ?? entry.data.kind;
  const searchBlob = compactText([title, kind, description].filter(Boolean).join(" ").toLowerCase());

  return {
    title,
    url: withBase(opts.url),
    kind,
    description: description || undefined,
    meta: opts.meta,
    searchBlob,
  };
}
