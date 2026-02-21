---
layout: default
title: "Known Submods"
description: "Known submods for Millennium Dawn: A Modern Day Mod"
---

# Known Submods for Millennium Dawn

The list here is a non-exhaustive list of submods that are available for Millennium Dawn. We do not guarantee that any of them work and are likely to dramatically change your experience playing Millennium Dawn.
As such we do not take bug reports when you are using a known submod. Please report it to those developers if there are any issues.

If you encounter an issue, PLEASE, try to make sure you have tested without the submod.

{% for group in site.data.content.known_submods.groups %}
## {{ group.title }}

{% if group.note %}
{{ group.note }}
{% endif %}

{% for item in group.items %}
[{{ item.title }}]({{ item.url }})
{% endfor %}
{% endfor %}
