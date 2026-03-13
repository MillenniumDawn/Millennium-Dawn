import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { getCollection } from "astro:content";
import { withBase } from "@/lib/urls";
import { SITE_DESCRIPTION, SITE_FALLBACK_ORIGIN, SITE_TITLE } from "@/shared/config/site";
import { getChangelogPath, getDevDiaryPath } from "@/lib/content-routes";

function mapItem(
  title: string,
  description: string | undefined,
  path: string,
) {
  return {
    title,
    description: description ?? "",
    link: withBase(path),
  };
}

export async function GET(context: APIContext) {
  const [changelogs, devDiaries] = await Promise.all([
    getCollection("changelogSections"),
    getCollection("devDiaries"),
  ]);
  const visibleChangelogs = changelogs.filter((entry) => !entry.data.hidden);

  const items = [
    ...visibleChangelogs.map((entry) =>
      mapItem(entry.data.title, entry.data.description, getChangelogPath(entry)),
    ),
    ...devDiaries.map((entry) => mapItem(entry.data.title, entry.data.description, getDevDiaryPath(entry))),
  ];

  return rss({
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    site: context.site ?? SITE_FALLBACK_ORIGIN,
    items,
    customData: `<language>en</language>`,
  });
}
