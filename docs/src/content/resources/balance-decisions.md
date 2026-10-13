---
title: Balance Decisions
description: Why key balance values are what they are, with the history of each change
---

A log of balance values that differ from vanilla, why they changed, and who approved it. Add an entry whenever you change one of these values.

## Railway construction cost

**Current:** `rail_way` uses `base_cost = 850`, `per_level_extra_cost = 650` (`common/buildings/00_buildings.txt`). Building level N costs `base_cost + per_level_extra_cost × (N − 1)`, so every level now costs 5x vanilla (170 / 130). Other MD buildings range from about 1x to 7x vanilla, so 5x is a railway-specific choice, not a shared rule.

**Cost per level, old vs new:**

| Level | Vanilla | Before (1000 / 3750) | After (850 / 650) |
| ----- | ------- | -------------------- | ----------------- |
| 1     | 170     | 1000 (5.9x)          | 850 (5x)          |
| 2     | 300     | 4750 (15.8x)         | 1500 (5x)         |
| 3     | 430     | 8500 (19.8x)         | 2150 (5x)         |
| 4     | 560     | 12250 (21.9x)        | 2800 (5x)         |
| 5     | 690     | 16000 (23.2x)        | 3450 (5x)         |
| 6     | 820     | 19750 (24.1x)        | 4100 (5x)         |

New level-1 lines barely change; upgrades get much cheaper.

**History:**

| Date       | Base / per level | Change                     |
| ---------- | ---------------- | -------------------------- |
| 2021-12    | 2000 / 500       | Building graphics update   |
| 2022-02-01 | 10000 / 60000    | Railway rework             |
| 2022-02-10 | 1000 / 5000      | Railway rework follow-up   |
| 2026-02    | 1000 / 3750      | Generic tree update (#482) |
| 2026-10    | 850 / 650        | Every level to 5x vanilla  |

**Why it changed:** the upgrade costs were set for balance reasons at the time. Railways keep the vanilla construction priority, so the AI queues them ahead of other buildings. In a 2004–2006 test from a 2004 save, Nigeria's construction queue was held by railway upgrades (level 2, about 16x vanilla each) and its own first dockyard sat at zero progress for 16 months with no factories assigned (observed). When railways stopped holding the queue, the same dockyard got 14 factories and was about 30% built a year later (observed). Cheaper upgrades finish quickly, so other buildings get their turn while railways still come first.

**Side effects:** players and AI both upgrade railways faster, and repairing rail damaged by bombing or fighting costs less.

**Approved by:** Bird, 2026-10.
