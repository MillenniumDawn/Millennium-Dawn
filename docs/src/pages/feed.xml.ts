import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { getCollection } from "astro:content";
import { stripMarkdownExt } from "../lib/slugs";
import { withBase } from "../lib/urls";

function mapItem(
  title: string,
  description: string | undefined,
  path: string,
) {
  return {
    title,
    description: description || "",
    link: withBase(path),
    pubDate: new Date(),
  };
}

export async function GET(context: APIContext) {
  const [changelogs, devDiaries] = await Promise.all([
    getCollection("changelogSections"),
    getCollection("devDiaries"),
  ]);

  const items = [
    ...changelogs.map((entry) =>
      mapItem(entry.data.title, entry.data.description, `/changelogs/${stripMarkdownExt(entry.id)}/`),
    ),
    ...devDiaries.map((entry) =>
      mapItem(
        entry.data.title,
        entry.data.description,
        entry.data.permalink || `/dev-diaries/${stripMarkdownExt(entry.id)}/`,
      ),
    ),
  ];

  return rss({
    title: "Millennium Dawn: A Modern Day Mod",
    description:
      "Documentation for the Millennium Dawn: A Modern Day mod for the game Hearts of Iron IV.",
    site: context.site || "https://millenniumdawn.github.io",
    items,
    customData: `<language>en</language>`,
  });
}
