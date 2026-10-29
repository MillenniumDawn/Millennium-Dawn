# Economic Forum System

Economic forums compete for government delegations, companies, speakers, and
prestige through yearly summits. Attendance is nonexclusive. A country can visit
several forums while hosting at most one (Issue #4802).

## Entry Points

- `econ_forum_setup`: called once during startup after power rankings are seeded.
- `econ_forum_monthly_update`: called in the global monthly block.
- `econ_forum_add_deal_targets`: called monthly for countries with forum agreements
  and after the yearly investment-target rebuild. The investment scoring effect
  also recognizes the directional `econ_forum_deal@PREV` flag.
- The International Systems Forums tab calls `econ_forum_build_screen` when opened
  or reopened. Forum changes refresh the open human screens and dirty counter.
- AI hosts and guests use scripted effects in the monthly cycle. The scripted GUI
  itself is disabled for AI.

The implementation is in `01_econ_forum_effects.txt`,
`01_econ_forum_triggers.txt`, `econ_forum_decisions.txt`, and
`events/EconomicForums.txt`. Event namespaces are `econ_forum` and `econ_forum_news`.

## Registry

Global arrays share a zero-based forum index. Effects take it in temporary
variable `ef_i`; program tracks use `ef_t`. Country attendance arrays share the
forum index. Sector arrays use `forum * 6 + track`, with 54 entries for nine forums.

| ID | Forum | Initial summit month | Host or eligible founder |
| --- | --- | --- | --- |
| 0 | World Economic Forum | January | Switzerland, private incumbent |
| 1 | Visegrád Economic Conference | September | Poland, Czechia, Hungary, Slovakia |
| 2 | St. Petersburg International Economic Forum | June | Russia, active at startup |
| 3 | Boao Forum for Asia | March | China, from 2001 |
| 4 | Global South Economic Forum | November | Regional or greater power with GDP per capita below 20 |
| 5 | African Development Conference | May | Sub-Saharan regional or greater power |
| 6 | Arctic Economic Forum | October | Norway, Denmark, Iceland, Finland, Sweden, Canada, Russia, United States |
| 7 | Transatlantic Technology Forum | April | NATO regional or greater power |
| 8 | Independent Economic Forum | Chosen at founding | Great or super power boycotting an existing forum |

The WEF starts at 80 prestige and St. Petersburg at 35. Newly founded forums start
at 15. A forum follows its seat state if ownership changes. Its current cycle is
cancelled on succession; a seat owner already hosting another forum leaves it
vacant until eligible.

## Yearly Cycle

Preparation opens two calendar months before the summit. The host chooses up to
three program tracks, invites governments, buys sponsors, books speakers, and can
arrange ceremonies, a private room, or sideline talks. Personal invitations close
one month before the summit. Summits remain at least 11 months apart even after
rescheduling.

The six tracks are AI and technology, energy, finance, defense industry,
infrastructure and trade, and development. Each forum has its own sector prestige
as well as overall prestige. Attendance, corporate delegations, speakers, and the
summit's other outcomes determine its score. Overall prestige moves toward that
score, while program tracks compete for sector leadership.

Standing invitations depend on prior attendance, core membership, prestige, and
the host's audience. AI attendance also weighs opinion, factions, sanctions,
BRICS, sector interest, boycotts, and nearby competing summits. The WEF's partners
fund its program independently of Switzerland's budget.

Attendees receive timed investment benefits. The host and investor agreements are
directional: signing ceremonies also add the reverse agreement. Targets added by
an agreement are removed on expiry only if that agreement inserted them, retaining
targets selected through the ordinary investment system.

## Player Choices and State

The Forums tab lists active or vacant founded forums by prestige and shows sector
leaders. Guest buttons support sponsoring a session, bidding for a keynote,
requesting an invitation, and boycotting or rejoining. Host preparation uses the
Economic Forums decision category.

Targeted preparation decisions retain cached target filters for list construction
and repeat their live conditions in `available`. This prevents cached rows from
spending closed invitations or exceeding ceremony, private-room, and talks limits.

Invitation, private-room, ceremony, and talks events queue their forum identifiers
and snapshot the relevant host, seat, or parties. Replies check that the original
offer still applies. Speaker bookings snapshot the forum and cycle, and retain
their selection lock through pagination. A terminal booking or cancellation clears
that lock; cancelling refunds the decision's original 25 or 75 Political Power.

Councils reward repeat attendance. Competitiveness reports rank attending guests,
with a costly host option to favor one. Protests, security, controversial speakers,
walkouts, sanctions, and pandemic disruption supply risks. Summer Davos and Young
Global Leaders add WEF-specific activity.

## Adding a Forum or Track

Keep every registry array aligned. Add the forum's host, state-led status,
prestige, month, seat handling, identity tracks, founders, and localization. Increase
all fixed nine-slot country and global arrays together. A new track also requires
changing the flattened index width and every six-track loop.

Start a new campaign when changing the registry or serialization model. Development
saves are not migrated.
