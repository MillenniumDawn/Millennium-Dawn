---
layout: default
title: "Technical Support"
description: "Technical support and troubleshooting help for Millennium Dawn: A Modern Day mod for Hearts of Iron IV."
permalink: /support/
---

# Technical Support

For the full [Troubleshooting Guide]({{ '/player-tutorials/troubleshooting-guide' | relative_url }}).

{% assign release = site.data.site.release.current %}
{% assign release_links = site.data.site.release.links %}

## How do I download Millennium Dawn?

Any other source then the below are not official team builds and as such we cannot guarantee the quality or the safeness of those builds.
Please ensure you are using the latest from one of the below versions.

**_Steam_**

Current MD Version: `{{ release.md_version }}`

HOI Version: `{{ release.hoi_version }}`

Checksum: `{{ release.checksum }}`

[{{ release_links.steam.label }}]({{ release_links.steam.url }})

**_GitHub Releases_**

Historical Builds of MD are kept here.

Available Versions are v1.12.2+

[{{ release_links.github_releases.label }}]({{ release_links.github_releases.url }})

**_GitLab Releases_**

Historical Builds of MD are kept here.
Available Versions are v1.8.4+ to v1.12.1d

[{{ release_links.gitlab_releases.label }}]({{ release_links.gitlab_releases.url }})

[{{ release_links.manual_install.label }}]({{ release_links.manual_install.url }})
