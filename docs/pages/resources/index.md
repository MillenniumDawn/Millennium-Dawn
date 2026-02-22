---
layout: default
title: "Resources"
page_id: resources
toc: "off"
description: "List of resources for the development team of Millennium Dawn."
permalink: /resources/
---

This is a non-exhaustive list of team-based resources for Millennium Dawn.

## Development Resources

{% assign resource_pages = site.pages
  | where_exp: "p", "p.path contains 'dev-resources/' and p.path contains '.md'"
  | sort: "title"
  | sort: "order" %}

{% include searchable-content-index.html
  items=resource_pages
  aria_label="Team development resources"
  page_size=8
  filter_label="Search"
  filter_placeholder="Type to filter..."
  empty_text="No resources matched your search."
%}
