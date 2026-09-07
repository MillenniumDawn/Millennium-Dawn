# Targeted operations: defensive policies

Countries can fund two independent policies in the counterterrorism dossier window.
Each purchase lasts 182 days on the existing weekly targeted-operations clock.

| Tier        | PP  | Treasury, bn | Protection | Collection | Exposure |
| ----------- | --- | ------------ | ---------- | ---------- | -------- |
| Basic       | 25  | 0.25         | 5          | 3          | 5        |
| Reinforced  | 40  | 0.75         | 10         | 6          | 10       |
| Exceptional | 60  | 1.50         | 15         | 9          | 15       |

Protection subtracts percentage points from timed operation success. Native raids
instead have a 5/10/15 percent chance to reduce a nonfailure outcome by one tier;
their callback exposes the resolved tier, not the engine's underlying chance.
Counterintelligence subtracts confidence from foreign dossier collection and adds
percentage points to exposure risk. These values are game balance abstractions.

A purchase replaces that policy's tier and expiry. It cannot add another bonus or
bank unused days. Both tracks charge through `modify_treasury_effect` once, after
checking country eligibility, controlled territory, political power, and cash.
Standing down clears both policies without refund. Expired values remain harmless
because the effect reads require an expiry strictly beyond the current clock.

## Runtime interfaces

- `TOP_purchase_security_policy = { TRACK = protection LEVEL = 1 }`: country scope;
  supported tracks are `protection` and `counterintelligence`, levels 1 through 3.
- `TOP_security_stand_down = yes`: country scope; clears both tracks.
- `TOP_security_country_tick = yes`: existing staggered country tick; refreshes
  remaining days only for a human with the policy popup open. Wartime AI with a
  serving protected official buys basic policies when a track has expired and
  reserves exceed 100 political power and 2 billion in cash.
- `TOP_get_defensive_modifiers = yes`: attacker scope with `TOP_target` set to the
  recorded person. Resets all three output temporaries before every lookup.
- Outputs: `TOP_defensive_collection_penalty`, `TOP_defensive_success_penalty`,
  and `TOP_defensive_exposure_bonus`. All are nonnegative magnitudes, not ratios.

The roster's `TOP_get_protection_country` helper supplies `TOP_security_country`.
Only an existing foreign country returned by that helper contributes modifiers.
The security system does not infer protection from a person's location, host,
organization, or current GUI selection. Roster eligibility must require a living,
currently serving official. A militant in a protected state gains no bonus merely
by being present there. A captured, retired, or dead person cannot retain a serving
government's protection through a stale map location.

`TOP_has_protected_official` also grants defensive policy access to countries that
do not qualify for offensive counterterrorism, such as a smaller state with an
authored serving leader. It does not grant offensive operation eligibility.

The caller must subtract the collection and success penalties and add the exposure
bonus before clamping the corresponding result. Native and timed methods should
read the recorded person when resolving. Authorization does not freeze defensive
spending; protection in force when an attempt is resolved affects that attempt.

## Interface

The independent footer and popup attach to `TOP_window`; they do not require a
nested-container visibility override. The footer occupies x15–355, y660–740.
The popup occupies x15–535, y245–655 and has its own close control.

The small footer label reads “Sponsored by Palantir™”. Its hover text explicitly
identifies an in-game parody and disclaims actual sponsorship, endorsement, or
affiliation. It has no external link or gameplay effect.

## Acceptance

Focused source-executing fixtures check affordability, independent policy tracks,
renewal, expiry, stand-down, protected-country isolation, and reset of outputs.
These fixtures do not establish engine rendering or natural campaign acceptance.
In HOI4, verify the popup at supported resolutions, each button's cost/tooltip,
save and reload during active funding, and expiry after 26 weekly pulses. Compare
foreign attempts against a serving official, an unmapped militant in the same
host, and a retired or detained official. Confirm the badge hover text is visible.
