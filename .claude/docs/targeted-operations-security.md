# Targeted Operations: Defense, Pressure, and Liaison

Defensive TOP systems remain available to eligible countries even when the country
cannot initiate an operation. AI countries may use these defensive, host, liaison,
custody, attribution, and crisis systems, but never cross into the offensive pipeline.

## National security policies

Protection and counterintelligence are independent 182-day national policies.

| Tier        | Political Power | Treasury, bn | Protection | Collection | Exposure |
| ----------- | --------------: | -----------: | ---------: | ---------: | -------: |
| Basic       |              25 |         0.25 |          5 |          3 |        5 |
| Reinforced  |              40 |         0.75 |         10 |          6 |       10 |
| Exceptional |              60 |         1.50 |         15 |          9 |       15 |

Protection subtracts percentage points from timed success. A native raid instead has
the tier's percentage chance to reduce a nonfailure result by one tier because the
callback exposes the engine result rather than its internal chance. Counterintelligence
subtracts from attacker collection and adds to exposure.

A purchase replaces that track's tier and expiry. It does not stack or bank unused
days. Both tracks charge once through the treasury effect after checking eligibility,
controlled territory, Political Power, and cash. Standing down clears both without a
refund. Expired values are ignored because every read requires expiry after the
current TOP clock.

`TOP_security_country_tick` may maintain AI defensive policies. It does not call any
offensive effect. A country with an authored protected official can buy defense even
when `TOP_country_eligible` is false.

## Central defensive resolver

`TOP_get_defensive_modifiers` is called in attacker scope with a recorded person in
`TOP_target`. It resets and returns:

- `TOP_defensive_collection_penalty`;
- `TOP_defensive_success_penalty`;
- `TOP_defensive_exposure_bonus`.

The roster's protection-country dispatcher supplies the defender. Presence in a
country does not itself grant official protection. Militants do not inherit a host's
VIP defense. Retired, detained, prosecuted, and dead people do not keep stale serving
protection.

The resolver centralizes national policy, individual VIP detail, person pressure,
organization-pressure spillover, and active organization disruption before clamping
each output. Authorization does not freeze later defensive spending. The operation
samples defense again when the attempt resolves.

## Individual VIP details

Eligible subjects are:

- serving political leaders;
- serving state-security officials;
- authored civilian public figures.

Militants and inactive former officeholders are ineligible. Capacity starts at two,
gains one slot from the existing passive-defense or early advanced-encryption
progression, gains another from later advanced cryptography or encryption, and is
capped at four.

Each assignment costs 25 Political Power and 0.25 billion treasury, lasts 91 days,
and applies:

- 3 points less attacker collection;
- 10 percentage points less operation success;
- 5 points more exposure.

The detail stacks with national policy only through the centralized resolver. Renewal
or reassignment replaces the remaining term without refund. Expired assignments free
capacity on the security tick.

## Person and organization pressure

Person and organization pressure are separate 0 through 100 values.

| Activity                         | Pressure gain |
| -------------------------------- | ------------: |
| Detected collection              |             5 |
| Detected review or host approach |            10 |
| Detected preparation             |            20 |
| Completed attempt                |            35 |
| 28 days left alone               |            -5 |

A person's effective pressure is direct person pressure plus 50 percent of affiliated
organization pressure, capped at 100. A direct person increase also adds 25 percent
of that increase to the organization.

Thresholds at 25, 50, and 75 apply automatic behavior and fire one defender event on
first entry into each tier. Falling below and later crossing a threshold does not spam
an already recorded notice.

Militants relocate more often as pressure rises. Officials and public figures tighten
protection and reduce travel. The highest tier blocks ordinary authored travel
opportunities. State-security organizations harden facilities and increase false
location risk.

## Detection, warning, and deception

Counterintelligence warnings reveal only an escalating actor assessment:

1. unknown foreign interest;
2. likely foreign service;
3. likely actor.

Warnings never reveal the exact person package, organization objective, method,
review stage, or scheduled date.

A likely actor permits private warnings, personnel expulsion, access cuts, or subject
hardening. That defensive actor assessment is not operation attribution and cannot
open a public strategic crisis by itself.

A defender can fund a deception response for 25 Political Power and 0.25 billion.
It lasts 91 days and adds 25 points to the chance that detected location collection
produces a wrong state in the correct host. If the host has no other controlled state,
the result becomes unresolved. Deception never writes or reveals physical truth.

## Liaison snapshots

Liaison sharing transfers a one-time country-owned snapshot. It never synchronizes
dossiers after delivery.

The snapshot contains:

- all three person or organization belief axes;
- believed state and host;
- lead age and report date;
- typed subject identity;
- source reliability.

It never transfers authorization, doctrine, methods, package ownership, operation
preparation, custody rights, or hidden source identities.

A request costs 25 Political Power and creates a 91-day subject-and-country-pair
cooldown. A valid relationship is a shared faction, subject relationship, cooperative
host relationship, intelligence partnership, or opinion of at least 50.

Reliability applies:

| Reliability | Supplied value used | Initial leak chance |
| ----------- | ------------------: | ------------------: |
| Trusted     |         100 percent |          10 percent |
| Mixed       |          75 percent |          25 percent |
| Suspect     |          50 percent |          40 percent |

The merge is non-destructive. An axis changes only when adjusted incoming knowledge
is higher. Believed location changes only when the incoming report is newer or
stronger. A deceptive source can provide a false state in the correct host. A leak
adds 10 pressure and gives the defender a vague warning.

AI countries may accept, partially share, refuse, or deceive. Receiving or sharing a
dossier never grants AI operational authority.

## Organization disruptions

Only one disruption type can be active for an organization. A later facility success
replaces the type and refreshes the 90-day expiry.

- Command/communications adds 5 collection gain against the organization and members.
- Training/logistics adds 10 percentage points to success against the organization
  and members.
- Funding/industrial reduces effective protection and relocation chance by 5.

The funding objective retains the one-time 3-point Counter-Terror threat reduction
when the organization has a current mapped CT slot. Missing `ct_id` is valid and does
not block the disruption or any other TOP organization behavior.

## Strategic-crisis support

A credibly attributed operation against a serving head of state or government can
notify the victim, attacker, physical host, faction partners, and victim guarantors.
Support consultations are one-time events for the current crisis token. Participants
may sanction the actor, reinforce the victim, share defensive intelligence, pressure
the actor, mediate, or abstain.

Support choices can change tension, opinion, Political Power, war support, or the
victim's defensive intelligence. They cannot directly declare war. Only the victim's
confirmed-attribution strategic-tripwire route can expose the one restricted war
choice, and that choice remains optional.

## Interface

Security remains a tab in the operations center and retains the existing
Counter-Terror entry point. It shows national policy, VIP assignments, capacity,
pressure, disruption, deception, warnings, and liaison actions for the selected
subject. Organization rows do not expose custody controls. Inactive former officials
do not expose VIP assignment.

The existing small sponsored-parody label has no external link or gameplay effect.
Its tooltip must continue to identify it as an in-game parody and disclaim actual
sponsorship, endorsement, or affiliation.

## Test and runtime acceptance

`python tools/analysis/targeted_operations_audit.py` checks national policy
independence, human-only offense, VIP capacity and cost, pressure increments and
spillover, threshold notices, deception, liaison cooldown and reliability, defensive
merge behavior, organization disruption replacement, and strategic-crisis support
dispatch.

Runtime acceptance must separately verify:

- each policy and VIP button's cost and tooltip;
- policy, detail, pressure, deception, and liaison persistence across save and reload;
- each pressure threshold for a militant, official, public figure, and state-security
  organization;
- anonymous, likely-service, and likely-actor warnings without secret detail leakage;
- a deceptive wrong-state report that remains in the correct host;
- trusted, mixed, suspect, refusing, and deceptive liaison partners;
- simultaneous national policy and VIP effects through one clamped resolver;
- faction-partner and guarantor crisis consultations without automatic war;
- layout at 1280 by 720, 1366 by 768, and 1920 by 1080.

Static fixtures do not establish rendering, native engine callbacks, or natural
campaign balance.
