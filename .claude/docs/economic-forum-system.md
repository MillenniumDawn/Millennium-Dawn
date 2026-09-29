# Economic Forum System

Economic forums are yearly summits that compete for governments, companies and
headline speakers (Issue #4802). The World Economic Forum is the incumbent. The
Visegrád Economic Conference is the first challenger. A forum is a registry slot,
not an event chain, so a new forum is data plus localisation.

Files:

- `common/scripted_effects/01_econ_forum_effects.txt`: registry, cycle, scoring.
- `common/scripted_triggers/01_econ_forum_triggers.txt`: core members, invitations.
- `common/decisions/econ_forum_decisions.txt`: founding and host preparation.
- `events/EconomicForums.txt`: `econ_forum.1-3`, `econ_forum_news.1-2`.
- `common/scripted_localisation/01_econ_forum_scripted_localisation.txt`: names.
- Hooks: `econ_forum_setup` in `on_startup` (`00_on_actions.txt`) and
  `econ_forum_monthly_update` in the global monthly block (`MD_on_actions.txt`).

## Registry

Global arrays share one index, the forum id. Every effect takes the id in the
temp variable `ef_i`.

| Array                       | Meaning                                       |
| --------------------------- | --------------------------------------------- |
| `econ_forum_host`           | Host country id; 0 until founded              |
| `econ_forum_state_led`      | 1 when a government runs it and gains from it |
| `econ_forum_prestige`       | 0-100 standing                                |
| `econ_forum_month`          | Summit month (1-12)                           |
| `econ_forum_preparing`      | 1 from preparation until the summit           |
| `econ_forum_invites_left`   | Personal invitations left this cycle          |
| `econ_forum_sponsors`       | Corporate points bought this cycle (max 25)   |
| `econ_forum_speakers`       | Headline speakers booked this cycle (max 3)   |
| `econ_forum_last_heads`     | Heads of government at the last summit        |
| `econ_forum_last_ministers` | Ministerial delegations at the last summit    |
| `econ_forum_last_score`     | Score of the last summit                      |

| Id  | Forum                        | Host    | Month | Start prestige | State-led |
| --- | ---------------------------- | ------- | ----- | -------------- | --------- |
| 0   | World Economic Forum         | SWI     | 1     | 80             | No        |
| 1   | Visegrád Economic Conference | Founder | 9     | 15 on founding | Yes       |

Per-country arrays use the same index:

- `econ_forum_status`: this cycle. 0 none, 1 standing invitation, 2 personal
  invitation, 3 ministers attend, 4 head of government attends, -1 declined.
- `econ_forum_last`: level at that forum's last summit (0, 3 or 4).
- `econ_forum_streak`: consecutive summits attended.

A host country carries `econ_forum_hosted` (its forum id) and, while preparing,
the flag `econ_forum_preparing`. One country hosts at most one forum.

## Yearly Cycle

1. **Preparation** opens two months before the summit month. The host gets
   `3 + prestige / 25` personal invitations. Standing invitations go to last
   year's attendees, core members (V4 for Visegrád) and, above 60 prestige, every
   country in `global.PR_regional_or_greater_powers`. Human invitees get
   `econ_forum.2`. A human host gets `econ_forum.1` and the decisions. An AI host
   runs `econ_forum_ai_prepare`.
2. **Host decisions** (human host): invite a regional power (15 PP, +15 attendance
   chance), buy a sponsor package (3.0 treasury and 10 PP for 5 corporate points)
   and book a headline speaker (50 PP, a roll against the strongest rival).
   Personal invitations close a month before the summit, so every reply
   resolves in time. Paid replies need the political power they cost.
3. **Summit** in the summit month. AI invitees roll attendance, every invitee is
   tallied, the score is computed and prestige moves 30% of the way to it.

## AI Attendance

`econ_forum_ai_decide_attendance`, clamped to 0-95:

| Factor                                          | Chance           |
| ----------------------------------------------- | ---------------- |
| Forum prestige                                  | × 0.6            |
| Personal invitation                             | +15              |
| Streak                                          | +3 each, max +15 |
| Opinion of host above 25 / below -25            | +10 / -15        |
| Same faction as host                            | +10              |
| Core member                                     | +15              |
| At war with host                                | -100             |
| Led a delegation to each other forum last cycle | -10 each         |
| More prestigious forum within one month         | -20              |

A roll under the chance attends. A roll under 40% of the chance sends the head of
government, but only to forums with prestige 30 or more, or as a core member.

## Score

- Governments: each attendee adds its share of world power ranking in percent
  (`percentage_of_global_factories × 100`), doubled for a head of government.
  The sum × 0.6 caps at 60.
- Corporate: `prestige × 0.15 + sponsors`, capped at 30.
- Speakers: `5 per speaker + prestige × 0.1`.
- Score = the sum, capped at 100. New prestige = `old + (score - old) × 0.3`.

## Rewards

- Every attendee, host included, gets `econ_forum_delegation_modifier` for 365
  days: `receiving_investment_cost_modifier` of `-prestige × 0.0005`, doubled for a
  head of government. The best forum of the year sets the value.
- State-led hosts gain `prestige × 0.02`% influence in each attendee (doubled for a
  head of government), a +10 opinion modifier from each, and
  `econ_forum_host_modifier` for 365 days: `prestige × 0.005` political power gain
  and `prestige × 0.002` foreign influence.
- The first time a challenger passes the World Economic Forum in prestige,
  `econ_forum_news.2` fires once.

## Adding a Forum

1. Append one entry to every registry array in `econ_forum_setup`.
2. Raise the three `size = 2` values and the `^num < 2` check in
   `econ_forum_ensure_country_arrays`.
3. Add the name key and a branch to each `econ_forum_name_*` scripted loc, plus
   its core members in `econ_forum_is_core_member`.
4. Add a founding decision or a startup host, and the host's tag to the
   `allowed` block of `econ_forum_category`.

## Known Limits and Next Phases

- One pending human invitation at a time (`econ_forum_invited_to`). Forums whose
  preparation windows overlap need a per-forum invitation event.
- A dead host stalls its forum. Host succession is not implemented.
- Invitations only reach regional powers or greater.

Planned phases from #4802:

- **Program tracks**: pick up to three sectors (AI, energy, finance, defense
  industry, infrastructure). Sector prestige lets a forum lead a niche before it
  leads overall.
- **Scheduling**: counter-program a rival or move away from it.
- **Deals**: turn attendance into real investment projects through the
  investment system, and companies once #4357 lands.
- **Forum leadership events**: Klaus Schwab at Davos, poached speakers, heads of
  government skipping Davos.
- **More forums**: Summer Davos for China, Global South and Pacific forums.
