---
layout: default
title: "Dev Diaries"
page_id: dev-diaries
description: "Development diaries from the Millennium Dawn mod team, covering new features, changes, and updates."
permalink: /dev-diaries/
---

# Dev Diary Lists

The Millennium Dawn team rarely writes dev diaries due to our frequency of our update schedule. This is more of an archive of older dev diaries for past content.

{% for group in site.data.content.dev_diaries %}
## {{ group.title }}

<details markdown="1"><summary>{{ group.title }}</summary>

{% for entry in group.entries %}
{% assign diary_url = entry.url | default: '' %}
{% if diary_url == '' %}
- {{ entry.title }}{% if entry.note %} ({{ entry.note }}){% endif %}
{% elsif diary_url contains '://' %}
- [{{ entry.title }}]({{ diary_url }}){% if entry.note %} ({{ entry.note }}){% endif %}
{% else %}
- [{{ entry.title }}]({{ diary_url | relative_url }}){% if entry.note %} ({{ entry.note }}){% endif %}
{% endif %}
{% endfor %}

</details>
{% endfor %}
