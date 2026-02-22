---
layout: default
title: "Tutorials"
page_id: tutorials
toc: "off"
description: "Guides and tutorials for playing Millennium Dawn: A Modern Day mod for Hearts of Iron IV."
permalink: /tutorials/
---

## Tutorials for Millennium Dawn

The following is a non-exhaustive list of tutorials or guides that are available on the website. The guides are always work-in-progress and you can contribute to expand them by creating a fork of [Millennium Dawn](https://github.com/MillenniumDawn/Millennium-Dawn) and submit new guides and information.

{% assign tutorial_pages = site.pages
  | where_exp: "p", "p.path contains 'player-tutorials/' and p.path contains '.md'"
  | sort: "title"
  | sort: "order" %}

{% include searchable-content-index.html
  items=tutorial_pages
  aria_label="Player tutorials"
  page_size=8
  filter_label="Search"
  filter_placeholder="Type to filter..."
  empty_text="No tutorials matched your search."
%}
