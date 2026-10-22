# STALKER framework and 2008 Zone

This first #4791 slice provides an opt-in Chornobyl Zone in a 2000 campaign. It is a source candidate; native HOI4 acceptance is pending.

## Boundaries

The default-disabled `rule_stalker_scenario` controls startup registration. A successful registry sets `GLOBAL_STALKER_zone_registry_initialized`; runtime content gates read that flag because the game rule is unavailable during some load-time checks. Registration is idempotent and changes no active gameplay before the 2008 yearly hook.

The reference-locations rule records stable anchor IDs 1-31 or only ID 1. These locations are inert; this slice activates only ID 1 in state 698. Regional profiles, randomized layouts and global activation are deferred. Their unused setters and triggers are omitted.

## Behavior

The 2008 hook activates the state and applies its penalties before offering policy to the current controller. A 60-day state flag guards the policy; it expires to the baseline policy if unanswered. Each answer checks the live controller and pending state before charging `small_expenditure` (0.2% of GDP) once. Military policy adds 30 containment; scientific access adds 30 exploitation.

The controller receives 1% consumer-goods upkeep and -0.5% recruitable population per active anchor. Research speed is exploitation multiplied by 0.0005, capped at +10% across controlled anchors. State control changes remove administration from the former controller, refresh the new controller and redeliver any pending policy. Event text names Chornobyl directly, so no shared global display target is needed.

Reinforce the Perimeter costs 50 Political Power and 0.2% of GDP. It adds up to 20 containment and lowers activity by up to 10 and exploitation by up to 5. Its 180-day state cooldown also guards AI treasury relief and direct repeat execution. An AI with fewer than 50 Political Power, at least 10 treasury, containment below 30, no bankruptcy mission and no pending policy/cooldown pays the same treasury charge for relief.

The first emission occurs on the first monthly pulse after a 90-day grace period once the pending policy has ended. Later pulses roll (activity + exploitation - containment) multiplied by 0.2, clamped to 2-20%, with 180 days between emissions. An emission adds 10 activity, removes up to 5 containment, disrupts the state for 60 days, and requests -2% Stability, plus -1% if resulting containment is below 20. Infrastructure damage is requested only if infrastructure exists and containment was below 40.

## Source tests and limits

`tools/tests/content/stalker_framework_test.py` is independent of OEM, TOP, FBC and AI Race. It executes this slice's real branches with a bounded fixture, including its actual administration refresh. Numeric state scopes and array counts are normalized for the existing parser; unsupported operations and unconsumed text fail. Native effects such as treasury charges and building damage are recorded requests.

These tests do not establish engine scopes, event delivery, dynamic-modifier rendering, natural AI selection, yearly dispatch timing, native flag expiry or save serialization. The fixture's day counter and explicit transfers are modeled inputs, not engine observations.

## Native acceptance still required

Record exact commit, deployed files, HOI4 version/checksum, DLC and rule settings, fresh logs and screenshots for each run. Use an isolated disposable profile and preserve existing saves.

1. Fresh 2000 start with rules disabled: no registry, active Zone, events, decisions, modifiers or monthly work. Repeat startup/reload.
2. Enabled starts with reference locations on/off: 31 or one unique registered anchor, no management before 2008. Reload before activation.
3. Advance naturally across the 2008 yearly boundary. Verify activation once, both policy branches, 0.2% GDP charge, current controller and displayed administration/research/state penalties.
4. Lose/regain state 698 while policy is pending and after answering. Verify old windows cannot charge or reward the former controller; verify new-controller notice and modifiers.
5. Let policy expire and advance through the first-emission grace period and later cooldowns. Verify costs, bounds, infrastructure guards, event artwork and tooltip values.
6. Use the containment decision, then repeat or transfer during its cooldown. Check engine Political Power charging as well as script treasury charges.
7. Observe AI Ukraine naturally, including low Political Power, low treasury, bankruptcy and relief cooldown. A forced fixture is not AI acceptance.
8. Save/reload while policy is pending, during emission disruption and during reinforcement cooldown. Compare live state, queues, modifiers and fresh error.log. Complete at least two playtests under the content review guide.

BLUF
