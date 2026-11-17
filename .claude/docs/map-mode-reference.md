# Map Mode Reference

Scripted map modes live in `common/map_modes/`. Engine keys are in
`common/map_modes/documentation.txt`.

## Colorblind rules

`tools/tests/content/map_mode_palette_test.py` enforces these. Add every new mode to its
`MAP_MODES` table, or the test fails. Colors are simulated with the Machado (2009)
matrices at full severity and compared with CIEDE2000 (ΔE).

- **Categorical modes.** One palette. Any two colors of one mode stay at least ΔE 10
  apart under normal vision and ΔE 15 under protanopia, deuteranopia, and tritanopia.
- **Ramps.** Bands run from worst to best in code order, brightness rises
  every step, and neighbors stay ΔE 10 apart under all four visions. Darker is worse.
  Use one band per legend line, with thresholds that match the legend text.
- **Ruling Party.** Its 25 colors (24 parties and a fallback) cannot reach ΔE 15, so
  the bar is ΔE 10 under all four visions. Keep each party near its outlook's hue
  family when retuning.
- Never lower a bar to pass. Merge or cut categories instead, as the EU mode does by
  grouping nine offices into five tiers.

## Layers

- Draw each country in one layer only. Overlapping EU layers may explain the off-white
  members in Issue #6005; the blending behavior is unverified. Exclude the top layer's
  countries from the bottom layer's color trigger.
- Target each layer with the array its color trigger checks.

## No palette variants

- Each mode has one palette that every player sees. Do not branch colors on a player
  setting: a branch per category costs script on every redraw and triples the colors
  to maintain.
- When a new color fails a bar, retune the mode's palette or merge categories.
- Keep colors clear of the sea, about (0.075, 0.145, 0.247) on screen.

## Legends and hover text

- The `_tooltip_delayed` key names the hovered country's value or status, as reserve
  currency does. FROM is the hovered state, so call country scripted loc as
  `[FROM.CONTROLLER.name]`.
- Text color codes only approximate the map; the words and the status line carry the
  meaning.
- Legend text must stay readable on the dark tooltip. `§Z` and `§b` vanish there, so
  ramps start at navy, which `§n` matches.

## Unverified engine behavior

- That `force_update_map_mode` redraws the map on every client.
- How two layers on one country blend. The off-white is inferred from a screenshot.
