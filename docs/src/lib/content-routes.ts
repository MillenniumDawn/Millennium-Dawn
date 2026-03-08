import { stripMarkdownExt } from "../shared/lib/slugs";

interface RoutedEntryLike {
  id: string;
  data: {
    permalink?: string;
    page_id?: string;
    body_class?: string;
    slug?: string;
  };
}

function trimSlashes(value: string): string {
  return value.replace(/^\/+|\/+$/g, "");
}

export function getEntryBaseId(entry: Pick<RoutedEntryLike, "id">): string {
  return stripMarkdownExt(entry.id);
}

export function getLastPathSegment(path: string): string {
  return trimSlashes(path).split("/").pop() ?? "";
}

export function getCountrySlug(entry: RoutedEntryLike): string {
  return entry.data.slug ?? getEntryBaseId(entry);
}

export function getCountryPath(entry: RoutedEntryLike): string {
  return `/countries/${getCountrySlug(entry)}/`;
}

export function getChangelogPath(entry: RoutedEntryLike): string {
  return `/changelogs/${getEntryBaseId(entry)}/`;
}

export function getDevDiarySlug(entry: RoutedEntryLike): string {
  return entry.data.permalink ? getLastPathSegment(entry.data.permalink) : getEntryBaseId(entry);
}

export function getDevDiaryPath(entry: RoutedEntryLike): string {
  return entry.data.permalink ?? `/dev-diaries/${getEntryBaseId(entry)}/`;
}

export function getTutorialPath(entry: RoutedEntryLike): string {
  return `/player-tutorials/${getEntryBaseId(entry)}/`;
}

export function getResourcePath(entry: RoutedEntryLike): string {
  return `/dev-resources/${getEntryBaseId(entry)}/`;
}

export function getMiscPath(entry: RoutedEntryLike): string {
  return `/misc/${getEntryBaseId(entry)}/`;
}

export function getEntryPageId(entry: RoutedEntryLike): string {
  return entry.data.page_id ?? getEntryBaseId(entry);
}

export function getEntryBodyClass(entry: RoutedEntryLike): string | undefined {
  return entry.data.body_class;
}

export function buildEntryStaticPaths<T>(entries: T[], getSlug: (entry: T) => string) {
  return entries.map((entry) => ({
    params: { slug: getSlug(entry) },
    props: { entry },
  }));
}
