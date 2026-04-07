---
title: Focus Tree Design Principles
description: Design philosophy and guidelines for creating engaging, balanced focus trees in Millennium Dawn
---

This guide covers the design philosophy behind Millennium Dawn focus trees — how to think about structure, pacing, and player choice. For related resources, see:

- [Focus Tree Lifecycle Checklist](/dev-resources/focus-tree-lifecycle-checklist/) — step-by-step development process
- [Code Stylization Guide](/dev-resources/code-stylization-guide/) — formatting and code structure
- [Content Review Guide](/dev-resources/content-review-guide/) — review criteria and quality checklist
- [Code Resource](/dev-resources/code-resource/) — effect costs and custom modifiers

---

## Core Philosophy

**Quality over quantity.** A well-designed 200-focus tree with meaningful effects and real choices is better than a 700-focus tree padded with Political Power and Stability bonuses. Every focus should contribute something specific to the nation's story or gameplay.

**Realism with room for alt-history.** Strive for realism as the baseline, but players should be able to pursue plausible alternate paths. Do not make nations powerful just because you think they are "based" — balance and plausibility come first.

**No content that violates Paradox guidelines.** Genocide, ethnic cleansing, or similarly extreme content is prohibited. This kind of content risks getting the entire mod shut down.

---

## Branch Structure & Replayability

**Interlock your branches.** Do not create isolated economy, politics, and diplomacy branches that never interact. Find ways to have these narratives combine in a single branch or at least influence each other. A diplomatic deal should have economic consequences; a military buildup should affect political stability.

**Avoid long vertical chains with no branching.** A straight line of sequential focuses with no choices offers no replayability and is boring game design. Give players options at regular intervals.

**Avoid oversized mutually exclusive branches.** Large mutually exclusive sections — especially those containing their own sub-mutexes — lock too much content behind a single choice, eliminating replay value. Use `available` requirements instead of `mutually_exclusive` where possible, so content is gated by conditions rather than permanently locked out.

**Every choice must be meaningful.** No path should be objectively superior to another. If one side of a mutually exclusive gives clearly better rewards, players will always pick it and the other path becomes wasted content. Design trade-offs into every decision — both for singleplayer and multiplayer, keeping in mind that a significant portion of the playerbase will min-max.

---

## Pacing & Rewards

**Focus duration should match the reward.** A 140-day focus that gives a minor bonus feels punishing. Keep wait times proportional to what the player receives. Short focuses for small benefits; longer focuses for transformative effects.

**Nothing is free.** All buildings, factories, and economic bonuses must have their monetary cost as specified in the [Code Resource](/dev-resources/code-resource/). Weight every reward against its cost to maintain balance across the mod.

**Avoid basic-only effects.** A string of focuses that only give Political Power, Stability, War Support, or factory counts is boring gameplay. Make effects specific to the nation — unique national spirits, decisions, mechanics, or event chains that make the country feel distinct.

---

## Ideology & Alt-History Paths

**Not every country needs every ideology.** However, alt-history options add significant replayability. A tree with only a democratic path will bore players who want to explore alternatives. Strike a balance appropriate to the nation.

**Include a historical modifier.** When the game rule is set to historical AI, the AI should follow the historical path. Add `ai_will_do` modifiers that check for the historical game rule so AI behavior matches player expectations.

---

## Cross-Nation Effects

Effects that target another nation should come through an event that gives the target player a choice. Do not force outcomes on other nations without their input. See the [Content Review Guide — Political Guidelines](/dev-resources/content-review-guide/#political-guidelines) for details.

---

## Events & Flavor

Events with rewards must offer multiple meaningful choices. A single-option event is railroading — it gives the player no agency and adds no gameplay value. Aim for at least 10-15 flavour events per nation to keep the gameplay dynamic between focus completions. See the [Content Review Guide](/dev-resources/content-review-guide/#political-guidelines) for full expectations.

---

## Starting Technology

A nation's starting technology should reflect what it **domestically produces**, not what tier of equipment it currently has in service. A country that imports advanced fighters but has no domestic aerospace industry should not start with advanced aircraft tech.

---

## Reworking Existing Trees

When reworking an existing focus tree, work **sector by sector**. Pick one area (e.g., the military branch), draft it, code it, test it, and merge it into master before moving on to the next sector (e.g., industry). This approach ensures that:

- Content actually gets finished and merged rather than stalling as an incomplete full rework.
- Players benefit from incremental improvements instead of waiting for a monolithic update.
- Each sector gets focused attention during review and playtesting.
