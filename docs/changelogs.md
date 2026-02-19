---
layout: default
title: "Changelogs"
page_id: changelogs
toc: "off"
description: "Changelogs for Millennium Dawn: A Modern Day Mod"
---

## Changelog Archive

This page indexes changelogs by major release branch. Open any card to see the full details for that release line.

For the [BETA test changes]({{ '/misc/beta-changelogs' | relative_url }}) click the link.

<section class="changelog-index" data-changelog-index data-page-size="6" aria-label="Changelog section index">
    <label class="changelog-index__filter-label" for="changelog-filter">Filter by version or keyword</label>
    <input id="changelog-filter"
           class="changelog-index__filter-input"
           type="search"
           placeholder="e.g. v1.12, economy, AI..."
           autocomplete="off"
           data-changelog-filter>

    <div class="changelog-index__cards" data-changelog-cards>
        {% assign sections = site.changelog_sections | sort: "order" | reverse %}
        {% for section in sections %}
        {% include changelog-card.html item=section %}
        {% endfor %}
    </div>

    <p class="changelog-index__empty text-muted" data-changelog-empty hidden>No changelog sections matched your filter.</p>

    <nav class="changelog-index__pagination" aria-label="Changelog pagination">
        <button type="button" class="btn btn-secondary" data-changelog-prev>Previous</button>
        <span class="changelog-index__status" data-changelog-status aria-live="polite"></span>
        <button type="button" class="btn btn-secondary" data-changelog-next>Next</button>
    </nav>
</section>
