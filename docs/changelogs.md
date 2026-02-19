---
layout: default
title: "Changelogs"
page_id: changelogs
toc: "off"
description: "Changelogs for Millennium Dawn: A Modern Day Mod"
permalink: /changelogs/
---

## Changelog Archive

This page indexes changelogs by major release branch. Open any card to see the full details for that release line.

For the [BETA test changes]({{ '/misc/beta-changelogs' | relative_url }}) click the link.

{% assign sections = site.changelog_sections | sort: "order" | reverse %}
{% include searchable-content-index.html
  items=sections
  aria_label="Changelog section index"
  page_size=8
  filter_label="Search"
  filter_placeholder="Type to filter..."
  empty_text="No changelog sections matched your search."
  default_kind="Changelog"
  excerpt_limit=220
%}
