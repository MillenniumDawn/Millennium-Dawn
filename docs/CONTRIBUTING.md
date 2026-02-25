# Contributing to Millennium Dawn Docs (Astro)

## Быстрый старт

```bash
cd docs
npm install
npm run dev
```

Откройте локальный сайт по адресу из вывода `astro dev`.

## Где редактировать контент

- Обычные страницы: `src/content/pages/*.md`
- Страны: `src/content/countries/*.md`
- Ченджлоги: `src/content/changelogSections/*.md`
- Туториалы: `src/content/tutorials/*.md`
- Ресурсы: `src/content/resources/*.md`
- Dev diaries: `src/content/devDiaries/*.md`
- Misc: `src/content/misc/*.md`

## Важные правила

- Используйте только Markdown + frontmatter.
- Не используйте Liquid (`{% ... %}` / `{{ ... }}`).
- Для внутренних ссылок используйте root-relative путь: `/tutorials/`, `/countries/germany/`.
- Не добавляйте вручную префикс `/Millennium-Dawn`.

## Шаблон frontmatter (обычная страница)

```md
---
# Обязательное: заголовок страницы
title: "Название страницы"

# Рекомендуется: описание для SEO и карточек
description: "Короткое описание страницы"

# Опционально: канонический URL
permalink: "/player-tutorials/new-guide/"

# Опционально: режим оглавления
# Возможные значения: "auto" или "off"
toc: "auto"

# Опционально: SEO/robots
seo: true
# robots: "noindex, nofollow"
---
```

## Шаблон frontmatter (страна)

```md
---
title: "Germany"
slug: "germany"
description: "National content overview for Germany."
unique_focus_tree: true
grid_order: 24
grid_note: "EU major branch"
flag_image: "/assets/images/flags/germany.png"
infobox:
  - section: "Overview"
    stats:
      - { label: "Tag", value: "GER" }
      - { label: "Capital", value: "Berlin" }
---
```

Контент страны пишется в теле Markdown:

```md
## Political Situation

Обычный markdown-текст.

| Party | Ideology | Popularity |
|---|---|---|
| SPD | Social Democracy | 28% |
```

## Проверки перед PR

```bash
npm run lint:md
npm run lint:remark
npm run check
npm run build
npm run check:links
npm run check:og
npm run check:a11y
npm run check:perf
```
