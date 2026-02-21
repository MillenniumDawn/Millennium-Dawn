---
layout: default
title: "Dev Diaries"
description: "Development diaries from the Millennium Dawn mod team, covering new features, changes, and updates."
permalink: /dev-diaries-list/
---

# Dev Diary Lists

The Millennium Dawn team rarely writes dev diaries due to our frequency of our update schedule. This is more of an archive of older dev diaries for past content.

{% for group in site.data.dev_diaries %}
## {{ group.title }}

<details markdown="1"><summary>{{ group.title }}</summary>

{% for entry in group.entries %}
- [{{ entry.title }}]({{ entry.url }}){% if entry.note %} ({{ entry.note }}){% endif %}
{% endfor %}

</details>
{% endfor %}
