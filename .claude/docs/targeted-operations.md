# Targeted Operations

Local implementation on `oem/targeted-operations`, based on fork main
`cf4dc93975ab564a34baa3d34b38c69cca102027`. New campaigns default to enabled.
The Off rule retains legacy content branches. There is no save migration or new bookmark.

## Ownership and identity

The manifest is `tools/data/targeted_operations.json`. Run
`python tools/generators/generate_targeted_operations.py` after authoring changes;
`--check` verifies that its checked-in output matches. Numeric IDs must never be recycled.
IDs 1–55 are militants, 56–63 are Iraqi fugitives, and 64 is Qasem Soleimani.
Slots 65–128 are bounded generated successors; zero is reserved. Generated names are fictional.
IDs 129–141 add thirteen authored political, military, and civilian figures. The global registry
has 142 slots and 22 affiliation/office groups; existing permanent IDs are unchanged.

Global arrays contain physical status, affiliation, office, host/state, custody, and lifetime
attempts/removal credit. Country arrays contain discovered dossiers, confidence, lead age/state,
authority, assessments, capture exploitation, and reports. CT organization IDs are resolved to
their current mutable slots before reading or changing organization arrays. Named organizations
use CT IDs 10–14, and all ID-indexed country arrays have 15 slots.

Historical windows permit activation. They do not enforce deaths, arrests, or promotions. Current
organization HQs, surviving movement countries, and authored regional fallbacks provide game
locations. These locations are simulation choices, not real-world location intelligence.
An office vacancy chooses a surviving authored successor before consuming a generated identity.
Exhaustion leaves a vacancy; it does not erase the organization or recycle a person.

The manifest distinguishes dated primary identity evidence, attributed analytical profiles for
several inherited ISIS entries, and unresolved historical outcome claims. An identity citation
does not verify every role or date. Unverified claims remain research notes, not campaign facts.

## Player flow

Open the counterterrorism screen and Dossiers. Designate one person for each target country.
Different country cases proceed independently; Active Cases lists the reserved slots.
Collection costs 25 Political Power once per assignment and runs through the existing staggered CT country processing. CT intelligence,
infiltration, funding, and tracking operations improve collection. Leads decay and can identify
the wrong state. Failed operations increase acquisition difficulty.

Authorization opens staff review, a sovereignty/consent decision, and senior review. Country
policy and political targets can require enhanced review. Capability and exceptional political
authority are checked separately. See [approval details](targeted-operations-authorization.md)
for the dated policy sources and deliberate game abstractions.

Senior approval costs 50 Political Power and records a standing mandate for that country case
for 91 game-clock days. Drone and capture raids use native equipment, basing, preparation,
and outcome mechanics.
Deniable action, rendition, partner capture, and sabotage use an actor-owned per-person timed record.
Sabotage records industry, infrastructure, or resource facilities before preparation. Resource
disruption is a temporary state modifier; industry and infrastructure damage can be repaired.

Changing the selected dossier cannot change a mandate, mission, host request, or delayed report.
Native cancellation leaves the mandate available. Renewing the identical open person/method/state
preserves its prepared native raid. Closed native tuples cannot be reauthorized, preventing an old
callback from attaching to a new identical mandate. See the [case contract](targeted-operations-cases.md)
for this engine constraint and the country-slot assessment lock. A callback for another case fails
the binding checks. State control must still match the recorded
host. Partner refusal produces a declined archive entry without an attempted attack.

Capture creates custody and provides intelligence once per actor/person. Removal rewards and
organization disruption occur only on the first neutralization. Release permits renewed pursuit
without repeating that reward. Custody transfers retain the Iraqi objective's distinct-person
credit and publish a usable dossier to the recipient. If a custodian is annexed, custody follows
the controller of its recorded detention state. Executing a prisoner cannot count them twice.

Actual death resolves immediately. Public confirmation and legacy lethal reports follow the
recorded assessment after a delay; assessment never rerolls the operation. An unresolved lethal
attempt can later report escape. Each country keeps 128 recent archive rows and persistent
per-target attempts. Archive method/state values belong to the recorded operation. Confirm the
assessment to free the country case; a new person requires a fresh designation and review.

Timed protective-security and counterintelligence policies defend mapped serving officials.
Eligible defenders can buy protection even without offensive eligibility. Their independent popup
includes an unobtrusive Palantir parody badge. See [security policies](targeted-operations-security.md).

## Existing content

- OEF retains its wars, access, and diplomatic branches. Discovery and consent supply leads and
  authority; extradition uses the shared capture resolver. Compatibility hideout/terminal flags
  follow canonical status, including release.
- Iraq retains all eight cards, regional searches, and the 1,825-day deadline. Completion requires
  four distinct fugitives dead or securely detained. Calendar Saddam events become conditional
  opportunities and custody-dependent follow-up. Cards distinguish detention from confirmed death.
- The thirteen original ISIS HVTs use the same registry. Their existing pulse develops leads;
  retirement, disruption, and coalition/Russian reports consume one recorded outcome.
- Soleimani's authored exceptional mandates remain required. Existing diplomatic and retaliation
  consequences are routed through the shared outcome/report interfaces.
- The 2024, 2025, and 2026 opportunity windows are processed once per eligible country through CT
  staggering. They select an already discovered, surviving authored target and grant intelligence.
  They never create a death, force a promotion, or resurrect an absent movement.

## Verification boundaries

Python tests execute script contracts using the repository's test interpreter, with engine-only
effects recorded at their boundary. This is separate from native engine behavior. The acceptance
checklist below has not been played in HOI4. A completed pytest run does not establish raid DLC
availability, GUI rendering, natural campaign balance, or save/reload behavior.

Use a fresh temporary directory outside the repository on the same drive for pytest on this
Windows installation. Python 3.12 is required by existing repository tests; the local `py -3`
alias can select Python 3.9.

Local verification on 7 September 2026, Python 3.12:

- Full repository pytest suite: 5,690 passed, 12 skipped, zero failures (519 seconds).
  This includes 258 Targeted Operations contract cases across six test modules.
- Roster generation check: no generated output differs. Focused checks for the new contracts
  and isolated staged-validation CLI behavior: 260 passed.
- Scoped GUI, scripted-localisation, variable/tooltip, unused-variable, common-mistake,
  character, idea, MIO, OOB, and style checks passed after repairs.
- Full decision validation: zero errors, 448 repository warnings, no Targeted Operations finding.
- The full scoped hook run was not clean: existing USA YAML duplicates and 105 undefined
  `usa_economic_events` references remain. The undefined references were verified at the base
  commit; the separate corporate-history check's 34 duplicate keys were also verified there.
- CI unit checkout now includes country tags, generated raids, and the Iraqi card GUI consumed
  by these tests. The existing configuration guard checks those fixtures.

Native-engine console fixtures, visual acceptance, and natural campaign tests have not been run.
The source-interpreter results above do not close those acceptance items.

## Approximate in-game acceptance plan

Use disposable new campaigns. Record game version, loaded mod path, base SHA, local file hashes,
DLC settings, save name, and whether each check used console setup or natural campaign play.

**USA, 2000: OEF and custody**

- [ ] Follow OEF discovery and host consent, confirm the named dossier receives a lead and authority.
- [ ] Accept extradition, confirm Bin Laden is detained once and later hunts agree with custody.
- [ ] In a separate save, capture through the named map raid and compare the same terminal consumers.
- [ ] Release and recapture him, confirm the hunt reopens without repeat removal rewards.
- [ ] Confirm Saudi leadership setters cannot recruit him while captured or dead.
- [ ] Transfer custody to an actor with no dossier, confirm its custody controls become usable.
- [ ] Annex the custodian, confirm custody follows the detention state's new controller.

**USA and Iraq, 2000 campaign: Most Wanted**

- [ ] Start the existing hunt, confirm all eight cards and the five-year deadline remain visible.
- [ ] Complete four captures, four deaths, and a mixture in separate saves; confirm four distinct IDs.
- [ ] Transfer prisoners, confirm credit persists; release before completion, confirm credit falls.
- [ ] Execute a detained fugitive, confirm no second objective credit and no pre-capture execution.
- [ ] Reach Saddam's calendar opportunities with him free, detained, and dead in separate saves.

**Native operations and concurrency**

- [ ] Authorize each method against a discovered eligible dossier and complete its strategic review.
- [ ] Run two country cases in parallel; confirm a second person in the same country is blocked.
- [ ] Confirm an assessment, then designate the next person in that country and rebuild review.
- [ ] Change dossiers while preparing; confirm the original person and state remain bound.
- [ ] Cancel a native raid, confirm authority remains; renew the identical case and reuse preparation.
- [ ] Revoke or expire a mandate; confirm its old callback cannot affect another person or case.
- [ ] Verify closed native tuples cannot be reused, while identical open renewals retain preparation.
- [ ] Conquer the target state during preparation; confirm renewed host review is required.
- [ ] Have two countries pursue one person; confirm capture/death/rewards resolve once globally.
- [ ] Exercise false leads, escape, compromise, unresolved assessment, and confirmed death reports.
- [ ] Change selection/authority before assessment arrives; confirm archived method/state remain original.
- [ ] Obtain partner refusal, confirm no attack, relocation, adaptation, or exposure is applied.
- [ ] Sabotage each facility type; remove the recorded facility before completion and check cancellation.

**Organizations, progression, and interface**

- [ ] Remove and recreate a CT organization and shift its slot, confirm surviving IDs keep affiliation.
- [ ] Exhaust authored then generated successors, confirm the organization survives the vacancy.
- [ ] Invoke old leadership setters after capture/death, confirm retired identities do not return.
- [ ] Play into 2024–2026, confirm opportunities only use known living people and eligible vacancies.
- [ ] Keep Mehsud eligible through a divergent campaign, confirm no calendar death or forced promotion.
- [ ] Save/reload during collection, review, preparation, assessment, and custody.
- [ ] Check Dossiers, Authorization, Archive, Iraqi cards, long names, tooltips, and 128-row rollover.

**DLC and AI**

- [ ] Repeat native raid creation/launch with all four La Résistance/Götterdämmerung combinations.
- [ ] Disable La Résistance, confirm the timed CT collection path is available to eligible countries.
- [ ] Observe AI PP reserves, target selection, review decisions, preparation, and mandate expiry.
- [ ] Start with Targeted Operations Off, confirm the existing OEF/Iraq/ISIS/raid routes still run.

Keep static contracts, console fixtures, visual checks, and natural campaign outcomes separately
reported. Do not mark unchecked playthrough items complete from Python tests alone.
