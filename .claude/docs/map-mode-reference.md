# Map Mode Reference

Scripted map modes live in `common/map_modes/`. Engine keys are in
`common/map_modes/documentation.txt`.

## Colorblind rules

`tools/tests/content/map_mode_palette_test.py` enforces these. Add every new mode to its
`MAP_MODES` table, or the test fails. Colors are simulated with the Machado (2009)
matrices at full severity and compared with CIEDE2000 (ΔE).

- **Categorical modes.** On Standard, any two colors of one mode stay at least ΔE 10
  apart under normal vision, protanopia, deuteranopia, and tritanopia. The red-green
  option needs ΔE 15 under protanopia and deuteranopia, the blue-yellow option ΔE 15
  under tritanopia. A mode with one palette must clear all three bars with it.
- **Ramps.** One palette. Bands run from worst to best in code order, brightness rises
  every step, and neighbors stay ΔE 10 apart under all four visions. Darker is worse.
  Use one band per legend line, with thresholds that match the legend text.
- **Ruling Party.** Its 25 colors (24 parties and a fallback) cannot reach the options'
  ΔE 15, so it keeps one palette that clears the Standard bar. Keep each party near its
  outlook's hue family when retuning.
- Never lower a bar to pass. Merge or cut categories instead, as the EU mode does by
  grouping nine offices into five tiers.

## The palette setting

- `map_mode_palette` on the player country: unset or 0 is Standard, 1 is red-green, 2
  is blue-yellow. The Automation Settings General page sets it. The GUI is player-only.
- Color blocks read `ROOT.map_mode_palette`, since ROOT is the player in a color
  trigger. Write each category as `if` 1, `else_if` 2, `else` Standard, so an unset
  variable falls through to Standard.
- List every mode that reads the variable in `refresh_palette_map_modes`
  (`common/scripted_effects/00_map_mode_palette_effects.txt`). The test checks the list.
- Add variants only where the tuned bar beats Standard. Ramps and modes with a few
  colors keep one palette.
- The variable lives on the country, so a tag switch or co-op on one country shares it.
  Standard is the reset.

## Legends and hover text

- The `_tooltip_delayed` key names the hovered country's value or status, as reserve
  currency does. FROM is the hovered state, so call country scripted loc as
  `[FROM.CONTROLLER.name]`.
- Legend color names must hold for every palette, so variants stay near the Standard
  hues. Text color codes only approximate the map; the words and the status line carry
  the meaning.
- Legend text must stay readable on the dark tooltip. `§Z` and `§b` vanish there, so
  ramps start at navy, which `§n` matches.
- Palette-aware legends end by pointing to the Automation Settings choice.

## Unverified engine behavior

- That ROOT in the color trigger and in the tooltip is the local viewer in multiplayer,
  so each player sees their own setting.
- That `force_update_map_mode` redraws the map on every client.
