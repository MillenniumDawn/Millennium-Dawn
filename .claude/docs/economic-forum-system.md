# Economic Forum System

Economic forums are yearly summits that compete for governments, companies and
headline speakers (Issue #4802). The World Economic Forum is the incumbent. The
St. Petersburg International Economic Forum runs from the start, and V4 countries
and China can found the Visegrád Economic Conference and the Boao Forum for Asia.
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

| Id  | Forum                                       | Host    | Month | Start prestige |
| --- | ------------------------------------------- | ------- | ----- | -------------- |
| 0   | World Economic Forum                        | SWI     | 1     | 80             |
| 1   | Visegrád Economic Conference                | Founder | 9     | 15 on founding |
| 2   | St. Petersburg International Economic Forum | SOV     | 6     | 35             |
| 3   | Boao Forum for Asia                         | CHI     | 3     | 15 on founding |

Only the World Economic Forum is private. The other three are state-led. Core
members, always invited: V4 for Visegrád; BLR, KAZ, ARM, KYR and TAJ for St.
Petersburg; every country with `asian_nation_flag` for Boao.

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
forum's identity: WEF AI, finance and development; Visegrád energy, defense and
infrastructure; St. Petersburg energy, finance and infrastructure; Boao AI,
infrastructure and development. Identity tracks start at the forum's prestige,
the others at half.

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
   - Invite a regional power: 15 PP, +15 attendance chance. Invitations close a
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
   `size = 4` values there and in `econ_forum_ensure_country_arrays`, and the
   `size = 24` track arrays by six.
2. Add its core members to `econ_forum_is_core_member` and its identity to
   `econ_forum_track_in_identity`.
3. Add the name key and a branch to each `econ_forum_name_*` scripted loc, and a
   standing line to `econ_forum_category_desc`.
4. Add a founding decision or a startup host, and the host's tag to the
   `allowed` block of `econ_forum_category`.

## Known Limits and Next Phases

- A dead host stalls its forum. Host succession is not implemented.
- Invitations only reach regional powers or greater.
- AI hosts neither reschedule nor adapt their program.

Next, from #4802: a company roster once #4357 lands, player-founded forums,
forums splitting after political disputes, and AI hosts that pick tracks by
sector leadership.
