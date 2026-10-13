---
title: Balance Decisions
description: Why key balance values are what they are, with the history of each change
---

A log of balance values that differ from vanilla, why they changed, and who approved it. Add an entry whenever you change one of these values.

## Railway construction cost

**Current:** `rail_way` costs `base_cost = 850`, `per_level_extra_cost = 650` (`common/buildings/00_buildings.txt`). This is 5x vanilla (170 / 130), the same scale as most other MD buildings.

**History:**

| Date       | Base / per level | Change                     |
| ---------- | ---------------- | -------------------------- |
| 2021-12    | 2000 / 500       | Building graphics update   |
| 2022-02-01 | 10000 / 60000    | Railway rework             |
| 2022-02-10 | 1000 / 5000      | Railway rework follow-up   |
| 2026-02    | 1000 / 3750      | Generic tree update (#482) |
| 2026-10    | 850 / 650        | Reduced to 5x vanilla      |

**Why it changed:** the earlier cost (about 22x vanilla) was set for balance reasons at the time. Railways keep the vanilla construction priority, so the AI always builds them first. At 22x cost, one railway line held all the construction factories of a small country for years, and nothing else got built. For example, Nigeria queued its first dockyard and it received no factories for over a year. At 5x, railways finish quickly again and other buildings get their turn.

**Approved by:** Bird, 2026-10.
