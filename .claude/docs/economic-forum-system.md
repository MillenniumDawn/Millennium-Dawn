# Economic Forum System

Economic forums are yearly summits that compete for governments, companies and
headline speakers (Issue #4802). The World Economic Forum is the incumbent. The
St. Petersburg International Economic Forum runs from the start. Six more forums
wait for a founder: the Visegrád Economic Conference, the Boao Forum for Asia, the
Global South Economic Forum, the African Development Conference, the Arctic
Economic Forum and the Transatlantic Technology Forum.
A forum is a registry slot, not an event chain, so a new forum is data plus
localisation.

Files:

- `common/scripted_effects/01_econ_forum_effects.txt`: registry, cycle, scoring.
- `common/scripted_triggers/01_econ_forum_triggers.txt`: core members, track
  identity and interest, invitations.
- `common/decisions/econ_forum_decisions.txt`: founding, preparation, program
  tracks and scheduling.
- `events/EconomicForums.txt`: `econ_forum.1-4`, `econ_forum_news.1-5`.
- `common/scripted_localisation/01_econ_forum_scripted_localisation.txt`: names,
  standings and the program view.
- Hooks: `econ_forum_setup` in `on_startup` (`00_on_actions.txt`),
  `econ_forum_monthly_update` in the global monthly block (`MD_on_actions.txt`)
  and the `econ_forum_deal@PREV` bonus in `AI_country_selection_calculation`
  (`99_AI_investment_scripted_effects.txt`).

## Registry

Global arrays share one index, the forum id. Every effect takes the id in the
temp variable `ef_i`, and a program track id in `ef_t`.

| Array                       | Meaning                                         |
| --------------------------- | ----------------------------------------------- |
| `econ_forum_host`           | Host country id; 0 until founded                |
| `econ_forum_seat`           | Seat state: the host's capital when registered  |
| `econ_forum_state_led`      | 1 when a government runs it and gains from it   |
| `econ_forum_prestige`       | 0-100 standing                                  |
| `econ_forum_month`          | Summit month (1-12)                             |
| `econ_forum_preparing`      | 1 from preparation until the summit             |
| `econ_forum_invites_left`   | Personal invitations left this cycle            |
| `econ_forum_sponsors`       | Corporate points bought this cycle (max 25)     |
| `econ_forum_speakers`       | Headline speakers booked this cycle (max 3)     |
| `econ_forum_track_count`    | Tracks on this cycle's program (max 3)          |
| `econ_forum_tracks`         | Track on the program, index `forum * 6 + track` |
| `econ_forum_track_prestige` | Sector prestige, index `forum * 6 + track`      |
| `econ_forum_last_heads`     | Heads of government at the last summit          |
| `econ_forum_last_ministers` | Ministerial delegations at the last summit      |
| `econ_forum_last_score`     | Score of the last summit                        |

| Id  | Forum                               | Month | Founder            | Core members        |
| --- | ----------------------------------- | ----- | ------------------ | ------------------- |
| 0   | World Economic Forum                | 1     | SWI, prestige 80   | None                |
| 1   | Visegrád Economic Conference        | 9     | POL, CZE, HUN, SLO | V4                  |
| 2   | St. Petersburg Intl. Economic Forum | 6     | SOV, prestige 35   | BLR KAZ ARM KYR TAJ |
| 3   | Boao Forum for Asia                 | 3     | CHI, from 2001     | Asian nations       |
| 4   | Global South Economic Forum         | 11    | Developing power   | Developing powers   |
| 5   | African Development Conference      | 5     | Sub-Saharan power  | Sub-Saharan         |
| 6   | Arctic Economic Forum               | 10    | Arctic nation      | Arctic nations      |
| 7   | Transatlantic Technology Forum      | 4     | NATO power         | NATO members        |

Only the World Economic Forum is private; the rest are state-led. Founded forums
start at 15 prestige. A developing power is a regional power with GDP per capita
under 20. The Arctic nations are NRY, DEN, ICE, FIN, SWE, CAN, SOV and USA.
Founding costs 100 PP (Boao 50) and needs stability above 40% and peace.

A forum follows its seat. When the seat state's owner is not the host, the old
host loses the forum, alive or not, and the cycle in progress is cancelled. The
seat owner takes it over and `econ_forum_news.6` fires, unless it already hosts a
forum; then the forum stands vacant, still listed with its prestige, until its seat
owner is free. Each invitation event keeps its forum's seat, so a reply answered
after its forum changed hands or closed is refunded and does nothing.

Per-country arrays use the same forum index:

- `econ_forum_status`: this cycle. 0 none, 1 standing invitation, 2 personal
  invitation, 3 ministers attend, 4 head of government attends, -1 declined.
- `econ_forum_last`: level at that forum's last summit (0, 3 or 4).
- `econ_forum_streak`: consecutive summits attended.

A host carries `econ_forum_hosted` (its forum id), the flag `econ_forum_preparing`
while preparing, and `econ_forum_view_selected` / `econ_forum_view_prestige`, a
six-slot copy of its program that the decision text reads. One country hosts at
most one forum.

## Program Tracks

| Track | Name                     | Interested governments                        |
| ----- | ------------------------ | --------------------------------------------- |
| 0     | AI and technology        | GDP per capita 20 or more                     |
| 1     | Energy                   | Energy deficit, or oil exports above 1        |
| 2     | Finance                  | GDP 500 or more, or GDP per capita 50 or more |
| 3     | Defense industry         | At war, or defence spending law 04 or higher  |
| 4     | Infrastructure and trade | GDP per capita under 20                       |
| 5     | Development              | GDP per capita under 7                        |

A host puts up to three tracks on each program (10 PP each). An AI host runs its
forum's three strongest tracks. Each forum starts with three identity tracks at its
prestige and the rest at half, so an AI host opens with its identity and then
follows whatever its summits build:

| Forum          | Identity tracks                      |
| -------------- | ------------------------------------ |
| WEF            | AI, finance, development             |
| Visegrád       | Energy, defense, infrastructure      |
| St. Petersburg | Energy, finance, infrastructure      |
| Boao           | AI, infrastructure, development      |
| Global South   | Energy, infrastructure, development  |
| African        | Finance, infrastructure, development |
| Arctic         | Energy, defense, infrastructure      |
| Transatlantic  | AI, finance, defense                 |

After each summit a track on the program moves 40% toward the score; a track off
it keeps 95% of its prestige.

## Yearly Cycle

1. **Preparation** opens two months before the summit month. The host gets
   `3 + prestige / 25` personal invitations. Standing invitations go to last
   year's attendees, core members and, above 60 prestige, every country in
   `global.PR_regional_or_greater_powers`. A human invitee gets `econ_forum.2`,
   Each invitation queues its forum id in `econ_forum_invite_queue` and each
   event claims the oldest one in `immediate`, saving the host as
   `econ_forum_inviter`, so invitations from several forums never collide. A human host gets
   `econ_forum.1` and the decisions. An AI host runs `econ_forum_ai_prepare`.
2. **Host decisions** (human host):
   - Invite a regional power (15 PP) or a neighbor outside that pool (10 PP),
     +15 attendance chance. Invitations close a
     month before the summit so every reply resolves in time.
   - Paid replies to an invitation need the political power they cost.
   - Buy a sponsor package: 3.0 treasury and 10 PP for 5 corporate points.
   - Book a headline speaker: 50 PP, a roll of `60 + (ours - rival) / 2`,
     clamped to 20-90. A speaker landed while the WEF is also preparing is taken
     from it. `econ_forum.4` reports the result.
   - Add a program track: 10 PP, up to three.
3. **Summit** in the summit month. AI invitees roll attendance, every invitee is
   tallied, the score is computed and prestige moves 30% toward it.

Outside preparation a host can reschedule once every two years (50 PP): the month
after its strongest rival's (counter-programming) or six months after it. Founding
or rescheduling a summit one or two months away opens preparation at once; one
month away leaves no time for personal invitations, for AI hosts too. A reschedule
that lands on the current month refunds its 50 PP and starts no cooldown.

An AI host of a state-led forum buys one sponsor package (3.0 treasury) when its
treasury is above 10 and one speaker attempt (50 PP) when it has more than 150 PP.
The World Economic Forum is private: its partners fund 15 corporate points and two
speaker attempts every cycle, whatever Switzerland can afford.

A summit always comes at least 11 months after the forum's previous one
(`econ_forum_months_since`, which counts calendar months for every founded forum,
vacant or not), so rescheduling right after a summit waits for the next cycle
instead of holding a second summit that year.

## AI Attendance

`econ_forum_ai_decide_attendance`, clamped to 0-95:

| Factor                                          | Chance                 |
| ----------------------------------------------- | ---------------------- |
| Forum prestige                                  | × 0.6                  |
| Personal invitation                             | +15                    |
| Streak                                          | +3 each, max +15       |
| Opinion of host above 25 / below -25            | +10 / -15              |
| Same faction as host                            | +10                    |
| Core member                                     | +15                    |
| At war with host                                | -100                   |
| Each track on the program that interests them   | + track prestige × 0.1 |
| Led a delegation to each other forum last cycle | -10 each               |
| More prestigious forum within one month         | -20                    |

A roll under the chance attends. A roll under 40% of the chance sends the head of
government, but only to forums with prestige 30 or more, or as a core member.

## Score

- Governments: each attendee adds its share of world power ranking in percent
  (`percentage_of_global_factories × 100`), doubled for a head of government.
  The sum × 0.6 caps at 60.
- Corporate: `prestige × 0.15 + sponsors + 3 per track the forum leads`, capped at
  30. A forum leads a track when its sector prestige beats every other active
  forum's.
- Speakers: `5 per speaker + prestige × 0.1`.
- Counter-programming: +5 when a more prestigious forum met the month before, or
  earlier in the same month's tick.
- Score = the sum, capped at 100. New prestige = `old + (score - old) × 0.3`.

## Rewards and Rivalry

- Every attendee, host included, gets `econ_forum_delegation_modifier` for 365
  days: `receiving_investment_cost_modifier` of `-prestige × 0.0005`, doubled for a
  head of government. The best forum of the year sets the value.
- State-led hosts gain `prestige × 0.02`% influence in each attendee (doubled for a
  head of government), a +10 opinion modifier from each, and
  `econ_forum_host_modifier` for 365 days: `prestige × 0.005` political power gain
  and `prestige × 0.002` foreign influence.
- Each attendee of a state-led forum signs an investment agreement: the host gets
  `econ_forum_deal@<attendee>` for 365 days, which adds 25 to that attendee's AI
  investment score for the host, like a trade agreement.
- Each head of government a counter-programmed summit draws who did not lead a
  delegation to the rival that just met costs the rival 1 prestige, up to 5. If one of
  them is a great or super power, `econ_forum_news.3` fires.
- Once per campaign: `econ_forum_news.5` when a challenger reaches 50 prestige,
  `econ_forum_news.2` when one passes the WEF, and `econ_forum_news.4` when the
  WEF retakes first place, checked after every summit. Before 21 April 2025 the
  WEF news names Klaus Schwab.

## Adding a Forum

1. Append one entry to every registry array in `econ_forum_setup`, raise the
   `size = 8` values there, the `^num < 8` checks in
   `econ_forum_ensure_country_arrays` and `econ_forum_can_be_invited`, and the
   `size = 48` track arrays by six.
2. Add its core members to `econ_forum_is_core_member` and its identity to
   `econ_forum_track_in_identity`.
3. Add the name key and a branch to each `econ_forum_name_*` scripted loc, a
   `econ_forum_preparation_<id>` key and branch, and a standing line to
   `econ_forum_category_desc`.
4. Add a founding decision calling `econ_forum_found`, or register a startup
   host with `econ_forum_register_host`, and make the founder see
   `econ_forum_category`.

## Known Limits and Next Phases

- AI hosts do not reschedule.
- A seat owner that already hosts a forum cannot inherit a second one, so that
  forum stands vacant until the seat changes hands or its owner stops hosting.

Next, from #4802: a company roster once #4357 lands, and forums splitting after
political disputes.
