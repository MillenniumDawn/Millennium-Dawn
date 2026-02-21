---
layout: default
page_id: home
permalink: /
description: "Documentation for the Millennium Dawn: A Modern Day mod for the game Hearts of Iron IV."
---

{% include hero.html %}

# Welcome to the MD Wiki

{% assign release = site.data.site.release.current %}
{% assign home = site.data.content.home %}

**Current Expected Version:** {{ release.md_version }}

**Current Expected Checksum:** {{ release.checksum }}

**Note:** The following Wiki is currently a work in progress. However, we will do our best to get meaningful content updated and placed on this page.

## Roadmap Images

{% for roadmap in home.roadmaps %}
### {{ roadmap.title }}

{% if roadmap.paragraphs %}
{% for paragraph in roadmap.paragraphs %}
{{ paragraph }}
{% endfor %}
{% endif %}

{% include responsive-image.html src=roadmap.image.src alt=roadmap.image.alt width=roadmap.image.width height=roadmap.image.height loading=roadmap.image.loading %}
{% endfor %}

### Joining the Millennium Dawn Development Team

{{ home.team_join.description | markdownify | remove: '<p>' | remove: '</p>' }}

### Translations

#### Paratranz Projects

{% for item in home.paratranz_projects %}
- [{{ item.name }}]({{ item.url }})
{% endfor %}

{% for group in home.resource_groups %}
### {{ group.heading }}

{% for item in group.items %}
{% if item.url contains '://' %}
- [{{ item.title }}]({{ item.url }})
{% else %}
- [{{ item.title }}]({{ item.url | relative_url }})
{% endif %}
{% endfor %}
{% endfor %}

### Submods

**DISCLAIMER** Any issues with a submod should be first reported to the submod you are playing with. Even something as simple as a graphics mod could break something in Millennium Dawn. Please try without submods if you encounter any issues.

For a list of Known Submods follow this [link]({{ '/misc/known-submods' | relative_url }}).

## Credits

A full list of credits for all of the models that are currently in use in-game: [Model Credit List]({{ home.credits.model_credit_list }}).

{% for thanks in home.credits.special_thanks %}
{{ thanks.text }}
{% endfor %}

Furthermore, a non-exhaustive list can be found at the [Authors]({{ '/misc/authors' | relative_url }}).
