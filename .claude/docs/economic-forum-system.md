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
forum index. Sector arrays use `forum * 6 + track`, with 126 entries for 21 forums.

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
| 9 | ASEAN Economic Partnership Forum | February | Singapore, Malaysia, Indonesia, Thailand, Vietnam |
| 10 | South Asian Growth Forum | July | India, Bangladesh, Sri Lanka, Nepal |
| 11 | Pacific Island Economies Summit | August | Fiji, Papua New Guinea, Samoa |
| 12 | Caribbean Maritime Investment Summit | December | Jamaica, Trinidad and Tobago, Barbados |
| 13 | Andean Economic Cooperation Forum | February | Colombia, Peru, Ecuador, Bolivia |
| 14 | Southern Cone Production Forum | July | Brazil, Argentina, Uruguay, Paraguay |
| 15 | Maghreb Investment Forum | August | Morocco, Algeria, Tunisia |
| 16 | Adriatic Enterprise Forum | December | Croatia, Slovenia, Albania |
| 17 | East African Connectivity Forum | March | Kenya, Tanzania, Uganda, Rwanda |
| 18 | Tokyo Industrial Innovation Forum | September | Japan |
| 19 | Astana Economic Forum | May | Kazakhstan, from 2008 |
| 20 | Future Investment Initiative | October | Saudi Arabia, from 2017 |

Slots 9-20 start inactive and require a founding decision. Slots 9-18 are
alternate-history regional proposals available from the 2000 start, not claims
that these exact institutions existed then. Astana and the Future Investment
Initiative represent real institutions with inception-year gates. Their initial
months, tracks, membership, costs, and effects are gameplay choices, not historical
attendance or budget data. The inception sources are the
[Astana forum's 2008 history](https://forum-astana.org/en/history/2008) and
[PIF's FII history](https://www.pif.gov.sa/en/fii-riyadh-2025/).

Pacific Islands, Caribbean, Adriatic, and East African founding costs are 50
Political Power; the other new forums cost 100. All require peace, stability above
40%, no hosted forum, and an unused forum host and seat slot. Availability repeats
these live uniqueness checks so another founder cannot claim a cached decision.
New founding decisions have AI weight 0.1 and retain a Political Power reserve.
Core invitations include the eligible founders. Tokyo also includes South Korea,
China, and Taiwan; Astana includes Uzbekistan, Kyrgyzstan, Tajikistan, and
Turkmenistan; FII includes the United Arab Emirates, Qatar, Kuwait, Oman, and Bahrain.


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

## Financial Flow

Treasury values are billions of dollars. `modify_treasury_effect` adds
`treasury_change` directly, without a GDP multiplier or a millions-to-billions
conversion. Forums have only these cash purchases:

| Purchase | Treasury charge | Limit |
| --- | --- | --- |
| Guest session sponsorship | $1.5 billion | Once per forum cycle; total sponsor points below 25 |
| Host sponsor package | $3 billion | Adds 5 sponsor points, up to 25 |
| Host media blitz | $2 billion | One summit message per preparation |

Founding, invitations, delegation replies, tracks, speakers, ceremonies, and
security use Political Power, not treasury. Startup does not charge governments.
Attendance and company delegations do not charge treasury; MIO funds are MIO
progress points. Forum modifiers do not add recurring treasury or debt expenses.
Investment agreements change target eligibility and scores within the existing
weekly investment system; they do not create another investment spending pulse.

An AI state-led host buys one sponsor package when preparation opens and its cash
exceeds $10 billion. A media blitz also requires more than $30 billion. The WEF's
AI preparation is funded by private partners. AI guests can sponsor once per cycle
only with more than $20 billion in cash, and stop topping up a forum at 15 sponsor
points. Host cash decisions have zero AI weight, so they do not duplicate the AI
preparation purchases. These are cash-stock checks, not forecasts of a country's
future weekly balance.

## Player Choices and State

The Forums tab lists active or vacant founded forums by prestige and shows sector
leaders. Its dynamic rows use a scrollable panel without a fixed vertical slot
limit, so all founded entries remain reachable. Guest buttons support sponsoring a session, bidding for a keynote,
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
all 21-slot country and global arrays, their allocation guards, and the 126-slot
sector arrays together. Extend seat flags and every name getter, including event
scopes, row names, and sector leaders. A new track also requires
changing the flattened index width and every six-track loop.

Start a new campaign when changing the registry or serialization model. Development
saves are not migrated.


## Regression Coverage

`tools/tests/content/economic_forum_state_test.py` checks registry alignment,
array sizing, track identity and the three-track cap, founder eligibility and
uniqueness, inception gates, core membership, seat flags, English keys, and name
lookups in every forum context. It also checks the dynamic scrollable list wiring.
These source-level tests do not verify native UI rendering, a campaign's annual
cycle, or gameplay balance. The expansion does not change cash costs or provide
save migration.
