---
title: Balance Decisions
description: Why key balance values are what they are, with the history of each change
---

Balance values that differ from vanilla, why they changed, and when. Add an entry when you change one.

## Railway construction cost

`rail_way` costs `base_cost = 850` plus `per_level_extra_cost = 650` per level above 1 (`common/buildings/00_buildings.txt`), which is 5x vanilla at every level. Other MD buildings range from about 1x to 7x vanilla, so 5x is a railway choice, not a shared rule.

| Level | Vanilla | Before (1000 / 3750) | After (850 / 650) |
| ----- | ------- | -------------------- | ----------------- |
| 1     | 170     | 1000 (5.9x)          | 850 (5x)          |
| 2     | 300     | 4750 (15.8x)         | 1500 (5x)         |
| 3     | 430     | 8500 (19.8x)         | 2150 (5x)         |
| 4     | 560     | 12250 (21.9x)        | 2800 (5x)         |
| 5     | 690     | 16000 (23.2x)        | 3450 (5x)         |
| 6     | 820     | 19750 (24.1x)        | 4100 (5x)         |

| Date       | Base / per level | Change                     |
| ---------- | ---------------- | -------------------------- |
| 2021-12    | 2000 / 500       | Building graphics update   |
| 2022-02-01 | 10000 / 60000    | Railway rework             |
| 2022-02-10 | 1000 / 5000      | Railway rework follow-up   |
| 2026-02    | 1000 / 3750      | Generic tree update (#482) |
| 2026-10    | 850 / 650        | Every level to 5x vanilla  |

**Why:** the old upgrade costs were a past balance choice. The AI builds railways before other buildings, so in small countries the expensive upgrades took every construction factory for years. In a 2004–2006 test, Nigeria's first dockyard got no factories for 16 months; once railways stopped holding the queue, it was about 30% built within a year.

**Side effects:** railways upgrade faster for everyone, and rail repairs after bombing cost less.

**Decision:** team decision, 2026-10-12.
