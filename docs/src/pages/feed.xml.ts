import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { getCollection } from "astro:content";
import { withBase } from "@/shared/lib/routing/urls";
import { SITE_DESCRIPTION, SITE_FALLBACK_ORIGIN, SITE_TITLE } from "@/shared/config/site";
import { getChangelogPath, getDevDiaryPath } from "@/shared/lib/routing/content-routes";

function mapItem(title: string, description: string | undefined, path: string, pubDate?: Date) {
  return {
    title,
    description: description ?? "",
    link: withBase(path),
    ...(pubDate ? { pubDate } : {}),
  };
}

export async function GET(context: APIContext) {
  const [changelogs, devDiaries] = await Promise.all([getCollection("changelogSections"), getCollection("devDiaries")]);
  const visibleChangelogs = changelogs.filter((entry) => !entry.data.hidden);

  const changelogItems = visibleChangelogs.map((entry) =>
    mapItem(entry.data.title, entry.data.description, getChangelogPath(entry)),
  );
  const devDiaryItems = devDiaries
    .map((entry) => mapItem(entry.data.title, entry.data.description, getDevDiaryPath(entry), entry.data.date))
    .sort((a, b) => (b.pubDate?.getTime() ?? 0) - (a.pubDate?.getTime() ?? 0));

  const items = [...changelogItems, ...devDiaryItems];

  return rss({
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    site: context.site ?? SITE_FALLBACK_ORIGIN,
    items,
    customData: `<language>en</language>`,
  });
}
