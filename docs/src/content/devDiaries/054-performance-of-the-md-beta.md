---
title: "Dev Diary #54: The Great Performance Crusade"
description: AngriestBird breaks down the massive performance improvements coming in v2.0.0, plus a first look at the Generic Tree Expansion.
permalink: /dev-diaries/54-the-great-performance-crusade/
author: AngriestBird
date: 2026-03-09
tags:
  - dev diary
  - v2.0
---

_By AngriestBird – 09 Mar 2026_

Hey there everyone! My name is AngriestBird and I am one of the lead developers and owner of the Millennium Dawn mod.

Millennium Dawn has had one consistent reputation since its inception, and that has been that performance has been a struggle for the mod.

As part of our larger initiative for the upcoming patch v2.0.0, I have spent the better part of the last two months working exclusively on performance, and with great pleasure I finally have something I am ready to share with the larger community. I am also the author of Part 1 of the Generic Tree Expansion, which I will show off here as well so I am not yapping about performance too much.

People who have been playing on the [BETA Test Mod](https://steamcommunity.com/sharedfiles/filedetails/?id=3374271790) or playing off of the GitHub version have been able to take advantage of these changes and have been invaluable in helping us catch issues from the substantial rewrites.

For some numbies, I want to reference back to [Dev Diary #49: Europe, Voting and Brusselsprouts](https://www.reddit.com/r/MillenniumDawn/comments/1c2c72x/dev_diary_49_europe_voting_and_brusselsprouts/) and [Dev Diary #52: Special Projects, Performances, Raids and Missiles](https://docs.google.com/document/d/1TeHUY7SBIVW2HOhaXEme1y1-UzFocmiMmvNAPMJMnCk/edit?tab=t.0), which are our most recent public snapshots for our performance metrics.

Compared to the European Union benchmark, my hardware has remained the same with the only exception of switching from Windows to Linux:

Specs:

CPU: i9-12900k

OS: Kubuntu - Rolling Release - Linux Runtime

GPU: NVIDIA GeForce RTX 4070

| Tick    | Old Avg (ms) | New Avg (ms) | Improvement |
| ------- | -----------: | -----------: | ----------: |
| Hourly  |           45 |           26 |       42.2% |
| Daily   |          219 |           72 |       67.1% |
| Weekly  |          404 |          113 |       72.0% |
| Monthly |          445 |          212 |       52.4% |

<img src="/assets/images/dev-diaries/054/image-01.png" alt="In-game tick rate display" class="mx-auto my-6 max-w-full" />

As you can see, we have made substantial changes that have yielded insanely high performance improvements without removing or losing any content.

All major systems including the energy, economy, missile, and influence systems have had no loss of content. We were able to improve performance simply by strategic restructuring and using more contemporary approaches.
This also includes the new United Nations, Cyber Warfare, Improved Satellite Systems, Counter Terror, Recognition, and several other extensions to the economy and energy systems.

So in totality, we have given you a more complete modern geopolitical sandbox without any content loss, and with significantly more AI, global system reworks, and much more with a faster, more stable experience.
Without getting too technical, the performance changes can be broken down into three main categories:

- Economy & Energy
- Tech Debt & Code Cleanup
- System Changes

## Economy & Energy

The most notable features of Millennium Dawn are the economic and energy systems. They are some of the largest systems in the mod and are fundamental to the experience. Here we had some significant tech debt to clear specifically with the lack of 64-bit support of Hearts of Iron IV for the Data Structures.

Once that support was available, it dramatically improved our ability to do math using the available data structures. This allowed us to remove several thousand lines of rounding and normalization code that were only there to keep numbers manageable.

Furthermore, consolidating dynamic modifiers (national spirits for the end user) and reducing the number of global ones that were refreshing has also allowed for the improvement.

## Tech Debt & Code Cleanup

As the mod continued to grow over the years, like any large project we accumulated some bad coding practices along the way. We tackled this head-on by implementing a more rigid team structure and adding linters, which allowed us to eliminate large swaths of code duplication and dramatically increase the speed of the mod.

As you may know, fewer lines of code means the engine loads faster and runs more smoothly. Enforcing stricter internal standards allowed us to get load times down to a matter of seconds on my machine which is about 18.5 seconds on my NVMe.

All in all, substantially rewriting the money system, removing dead systems, eliminating unneeded logging, and cleaning up old code has contributed to a much better developer experience as well as a much more refined user experience. This has paid incredible dividends and will give you a significantly more performance-oriented gaming experience with Millennium Dawn.

It also ensures that end users get a consistent experience rather than needing to unpack the developer's intent with each piece of content, letting you get to enjoying things faster.

## System Changes

Notable system changes:

- Power Ranking is calculated every 6 months (we may move this to every 3 months based on BETA testing)
- Renewables no longer cycle power weekly and instead get a slight buff to their performance since you plan around their potential not what they would produce on a given week
- Shifted any systems that were not reasonably changing for the European Union and other misc systems to monthly checks

Unfortunately, performance work is not that glamorous, but the results speak for themselves. I hope that this helps everyone going forward to better enjoy Millennium Dawn and have a much better game from now and into the future.

## The Generic Tree Expansion

Now with that out of the way, the Generic Tree. Everyone loves to play the Generic tree alongside the custom country content, but it has always lagged a bit behind the main mod when it comes to new systems and features we have developed. This left an unfortunate gap for those nations that were not expected to receive dedicated content any time soon.

<img src="/assets/images/dev-diaries/054/image-02.png" alt="Generic tree economy branch" class="mx-auto my-6 max-w-full" />

<img src="/assets/images/dev-diaries/054/image-03.png" alt="Generic tree military branch" class="mx-auto my-6 max-w-full" />

Part 1 of the Generic Tree Expansion brings both an economy branch and a military branch, giving those nations a meaningful foundation to build from and bringing them up to speed with the rest of the mod.
This change should make the Generic Nations a bit more competitive with all the extra content we have added to allow them to participate with all the new content without being left behind.

Now, that is all I have for you today. Thank you for reading this dev diary and thank you for being players of Millennium Dawn and being here with us on this journey as we strive to deliver a great modern day geopolitical sandbox. Stay tuned in a couple of weeks for our next dev diary!
