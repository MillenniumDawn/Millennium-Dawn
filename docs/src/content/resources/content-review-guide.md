---
title: Developer Content Review Guide
description: Quality guidelines and checklist for reviewing Millennium Dawn content before submission
---

This guide outlines the quality expectations for Millennium Dawn content. It covers playtesting notes, writing standards, and review criteria established by the team. Use it as a checklist when developing or reviewing content.

> **Supporting Resources:**
>
> - [Focus Tree Lifecycle Checklist](/dev-resources/focus-tree-lifecycle-checklist/)
> - [Code Stylization Guide](/dev-resources/code-stylization-guide/)
> - [Code Resource](/dev-resources/code-resource/)
> - [New General Guidelines](/dev-resources/new-general-guidelines/)

---

## What Is a Content Review?

A content review evaluates proposed content against the team's quality standards. It includes playtesting notes, writing expectations, and more. This process requires careful thought — compose your feedback thoroughly and ensure the content meets our standards.

## Why Do We Do Content Reviews?

Content reviews ensure a consistent, high-quality product for both the team and players. Your content is a reflection of the team. Make sure it is consistent in quality with the rest of the mod.

---

## Content Guidelines

### Economic Guidelines

- **Do all buildings that require a slot have one provided in effect?**
  All shared buildings (industrial complexes, arms factories, office sectors) should include a supporting building slot, as the cost reflects this. This also helps foster growth for the nation. In some cases you may intentionally omit the slot — adjust the building cost accordingly.

- **Do all buildings/factories have a monetary cost?**
  All buildings should have their monetary cost as specified in the [Code Resource](/dev-resources/code-resource/). This ensures a balanced game.

- **Do all trade opinion effects have a supplementary effect?**
  Trade opinion on its own is a shallow effect. Always pair it with something meaningful.

- **Are there any "changes" in budget laws (social spending, healthcare, etc.)?**
  Budget law changes alone are shallow filler effects. Add more effects to support the law change. Strive for something unique in each effect.

- **Is gaining more building slots/economic benefits possible than the generic tree?**
  The generic tree is the baseline for all economic effects. If your tree provides fewer benefits than the generic tree, it is likely too shallow. Revisit it and ensure it meets or exceeds the generic tree.

- **Have I adjusted the starting economic situation for the country?**
  You have free reign to change debt, treasury, national spirits, budget, etc. The only exception is starting factories — these are set to match IRL GDP PPP and must not be changed.

### Political Guidelines

- **Were all the parties founded before January 1st, 2000?**
  Any party founded after that date must be hidden until created through a unique circumstance (e.g., an economic crash creating AKP in Turkey) or a trigger for its founding year.

- **Have I added custom traits to all leaders?**
  Add at least two traits per leader, with at least one providing an effect or modifier. Ensure the trait is relevant to the leader.

- **Is my content politically neutral and unbiased?**
  All content should be as objective and factual as possible. Keep things politically neutral.

- **Do your political parties have descriptions and icons?**
  All new content for a nation should include party icons and descriptions. This adds flavour and is a straightforward task.

- **Are the tree paths well-balanced against one another?**
  All paths should have a reason to be taken. No path should be objectively stronger than another.

- **Are the paths plausible or relevant to the nation?**
  Ensure fictional or implausible content is locked behind a game rule (e.g., Scythia with Ossetia).

- **Is the focus tree path linear?**
  Avoid railroaded content. Millennium Dawn is a sandbox — ensure players have choices and dynamics within their game.

- **Do effects from my country's content to another nation come from an event/choice?**
  Most permanent effects targeting another nation should come from an event. Give the target player agency to respond.

- **Have I added new cores?**
  Do not add cores for free at game start. Cores represent whether a population reasonably wishes to join a nation. Create a mechanic for gaining cores. Without an integration system, require at least 80% compliance for states being cored. You can implement this via a decision or focus.

- **Have I added flavour events?**
  Aim for at least 10-15 flavour events. Gameplay should not be "click focus, wait, click focus, wait." Make the country feel alive.

### Visual Appearance

- **Is there a focus icon in every spot?**
  Ensure no focus is missing its icon.

- **Are there focus filters for every focus?**
  All focuses should have `search_filters` defined.

- **Do I display the potential effects of an event in a focus?**
  Where a focus triggers events, use tooltips to indicate what may happen.

- **Are there too many meme GFX?**
  Use no more than one meme GFX in the content (e.g., wojaks, trollface).

- **Are there any tooltips or code language strips that need to be added?**
  Everything player-facing must be localised.

- **Has the localisation been spell-checked and grammar-checked?**
  All English grammar rules apply. Titles should be capitalised properly with consistent spelling and punctuation. Trees with significant grammar or spelling issues will not be accepted for merge until corrected.

- **Is there any localisation showing up as non-localised?**
  Ensure there are no unlocalised strings. Focus descriptions must not be blank or re-use the focus name. All starting national spirits must have descriptions — if negative and removable, explain how. Reference Iran or Libya starting spirits for examples.

- **Is the use of custom focus icons moderated?**
  Do not use custom focus icons for every other focus. Reserve them for major focuses (parties, key decisions, etc.).

### Military Guidelines

- **Have I redone/expanded the officer corps for my nation?**
  This is not critical but adds good flavour. Try to do this if you have time.

- **Have I updated my nation's Order of Battle (OOBs)?**
  If so, use well-documented resources. Do not give your nation equipment they would not have historically.

- **Have I created name lists for my country?**
  Name lists add immersion. Reference the Libyan or Japanese name lists for examples.

- **Have I added new generals?**
  Follow the [New General Guidelines](/dev-resources/new-general-guidelines/). This is a standard process. If you have questions about the number of generals for your country, consult the team.

### AI Guidelines

- **Have I created AI game rules?**
  Create AI game rules so players can customise their experience. This is a core part of what makes Millennium Dawn unique.

- **Have I added AI rules to my focus tree?**
  Add basic AI logic to prevent the AI from making self-destructive choices.

- **Have I added AI strategies to guide the nation?**
  Create AI strategies to help the AI respond to conditions from your content. This makes the game feel more alive.

- **Have I used `add_ai_strategy` in any effect?**
  Do not use `add_ai_strategy` in effects. It is harmful to AI performance. Consult the AI team if you need assistance.

- **Do all events targeting another nation have AI weighting?**
  For example, if an event asks Russia for a trade deal, ensure Russia's acceptance is based on opinion — not random chance.

- **Have I added AI to any GUIs/mechanics I have made?**
  Ensure the AI can interact with any GUIs you create. Add game rules for AI interaction where applicable.

### Miscellaneous Guidelines

- **Have I added my nation to the bookmarks screen?**
  Do not add to bookmarks. Nations are added to bookmarks only after being merged into the master branch.

- **Is your tree at least the same size as the generic one?**
  The generic tree is currently 114 focuses.

- **Have I added cosmetic tags to my content?**
  If so, ensure the cosmetic tag is dropped when no longer applicable (e.g., Germany becomes the German Empire, then loses it upon becoming a democracy again).

- **Have I added additional countries/tags to my nation's content?**
  New tags require: an Order of Battle, name lists, political structuring, starting laws, and a historically accurate starting leader.

- **Have I added ribbons/custom achievements?**
  These are optional but encouraged. Achievements are challenge runs; ribbons are minor or strategic goals. These can be added at any point and are not required during initial review.

- **Have I ensured no errors related to my content in the error.log?**
  Check the error log for any errors related to your nation. Keep the error log clean.

- **Is my content well-researched?**
  Ensure your content is thoroughly researched. Do not cut corners.

- **Is my content easy to understand?**
  If you need to explain how your content works outside of the in-game tooltips, the design needs improvement. Content should be understandable from its descriptions alone.

- **Have I playtested this?**
  Playtest your content at least twice before requesting a review.

- **Have I reviewed my content?**
  Review your content at least twice before requesting a review.

- **Have I added my content additions to Changelog.txt?**
  You are responsible for documenting your content in the changelog before submitting for review.

- **Have I reviewed my pipeline?**
  Review the CI pipeline to ensure it has either succeeded or any errors are acknowledged and explained.

---

## Code Guidelines

- **Is my code neatly tabbed?**
  Ensure consistent tab indentation throughout. See the [Code Stylization Guide](/dev-resources/code-stylization-guide/) for the formatting standard.

- **Do all effects have a log?**
  All content should be logged to make debugging easier. This helps find crashes, bugs, and other issues.

- **Do all my focuses have `ai_will_do`?**
  If not, add them.

- **Do I have empty `allowed`/`available`/`cancel`/`bypass` or any other trigger set?**
  Delete empty trigger blocks. They are bloat and do not benefit the mod.

- **Am I using `relative_position_id`?**
  All focus trees must use `relative_position_id`. This makes it easier to rework and expand content.

- **Are any references to the tag capitalised?**
  All tags should be capitalised, including at the start of script IDs (e.g., `SPR_focus_name_here`).
