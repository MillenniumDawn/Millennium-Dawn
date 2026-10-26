# Full STALKER upstream playthrough checklist

This checklist covers the complete OEM scenario port for #4791 and its Targeted Operations prerequisite #5498. It is an approximate plan grounded in the shipped source. Every box starts unchecked for this combined upstream candidate. Earlier #5962 fixture runs do not establish acceptance of this complete port.

Record the tested commit, HOI4 version and checksum, DLC list, game rules, actual save files, screenshots, game log, and error log. Preserve the normal playset and original saves. Record every test fixture or console command separately from normal campaign progression.

**Playthrough A: UKR 2000, scenario disabled (covers #4791)**

- [ ] Start a fresh 2000 campaign with STALKER disabled and both secondary rule choices varied, confirm no Zone registry, active anchor, scenario decision category, artifact bureau, or STALKER story becomes active (#4791).
- [ ] Save, close, and reload the disabled campaign, confirm isolation persists through the 2006 and 2008 dispatch boundaries (#4791).
- [ ] Keep TOP enabled during this control, confirm organizations 35 through 38 remain inactive and ordinary TOP dossiers, native raids, and agency operations retain their normal behavior (#4791).

**Playthrough B: UKR 2000 through 2018, original Zone and dated history (covers #4791)**

At startup and the 2008 boundary:

- [ ] Enable STALKER with reference locations, confirm registered anchors are inert before their authored activation and the original Zone is state 698 (#4791).
- [ ] Cross the 2006 dispatch, confirm its disaster story fires once without opening Zone management early (#4791).
- [ ] Save before January 2008 and reload across the monthly boundary, confirm the original Zone activates once and the current controller receives the policy choice (#4791).
- [ ] Exercise military containment and scientific exploitation from separate copies of the same pending policy save, confirm each cost is paid once and its modifier, society, and tooltip values match the effect (#4791).
- [ ] Transfer state 698 before answering the policy event, confirm the former controller cannot pay or apply it and the current controller receives the unresolved choice (#4791).
- [ ] Open Zone management and its overview, confirm names, faction strengths, status text, controls, event art, and English substitutions render correctly (#4791).

Routine management and connected campaigns:

- [ ] Reinforce containment, confirm the political or AI treasury cost and the shared 180-day cooldown (#4791).
- [ ] Save during the first-emission delay and reload, confirm exactly one due emission, its infrastructure and stability effects, and its disruption expiry (#4791).
- [ ] Create and resolve a perimeter breach, transfer control while the report is open, confirm it reaches the current human controller and cannot reward the former one (#4791).
- [ ] Advance society, Monolith, MDST, mutants, stalkers, Duty, Freedom, scientists, traders, bandits, military, and mercenaries through their exposed decisions and events, confirm thresholds and choices change only factions present in the Zone (#4791).
- [ ] Explore the X-Lab branch and its Brain Scorcher choice, confirm its rewards and costs do not select an unrelated dated Strelok route (#4791).
- [ ] Complete Yantar, Army Warehouses, and Red Forest dossiers in sequence, confirm 25-PP investigations and 50-PP recoveries run for 60 days, preserve pending assignments through reload, and deliver reports to a new controller (#4791).
- [ ] Exercise recurring scientific escorts and road patrols, confirm the shared assignment slot, 60-day duration, 180-day cooldown, and 5-point recurring effects without repeating campaign research rewards (#4791).
- [ ] Abandon a dossier from a separate save, confirm its bandit consequence and closed progression (#4791).
- [ ] Resolve Tearling gathering and backing, confirm rewards follow the participating factions and absent factions cannot collect paid support (#4791).

Dated branches and delayed delivery:

- [ ] Run separate 2011 Clear Sky saves for stopping Strelok, the marked canon route, and helping him remember, confirm mutually exclusive route flags and Scar's survival (#4791).
- [ ] Confirm stopping Strelok prevents the 2012 raid, and the other routes produce only their intended 2012 choices (#4791).
- [ ] Save during the delayed Fairway and Strider reports, remove or transfer the carrier, and reload, confirm each story recovers once with the intended route and current controller (#4791).
- [ ] Resolve the 2018 SIRCAA and Ward charter with and without shared Yantar findings, confirm the later scientist reward is applied once (#4791).
- [ ] Delay Clear Sky and SIRCAA simultaneously, confirm their independent relays cannot exchange outcomes and recover when their carriers disappear (#4791).

**Playthrough C: UKR, BLR, and international participants, 2008 onward (covers #4791)**

- [ ] Use the Belarus and international research paths, confirm access, opinions, funds, and artifact transfers reach the selected country (#4791).
- [ ] Run the Security Council response with the Zone controlled by a permanent member and then a nonmember, confirm one ballot per live permanent seat plus the controller and correct recovery of annexed uncast seats (#4791).
- [ ] Test foreign intelligence drift and artifact seizures, confirm faction leadership refreshes and source-linked TOP leads are granted only to eligible human countries (#4791).
- [ ] Buy and sell artifacts and unlock the anomalous-materials bureau with the relevant DLC enabled, confirm stock, treasury, research, and MIO upgrades account once (#4791).
- [ ] Start a polar artifact study at a powered, fuelled, undamaged Radiation Laboratory, confirm the 5-artifact charge and the 180-day research and station-iteration bonus (#4791).
- [ ] From separate study saves, lose laboratory operation or receive Treaty observers, confirm samples are seized or lost, the result is suppressed, and a station already reported for another violation receives no duplicate Treaty penalty (#4791).
- [ ] Repeat without Arms Against Tyranny, confirm MIO-only paths remain unavailable without invalid-scope errors and ordinary scenario decisions remain usable (#4791).

**Playthrough D: UKR 2022, aftermath and global Zones (covers #4791)**

- [ ] Reach the battle for the Zone with complete and incomplete field dossiers in separate saves, confirm unfinished campaigns close unprepared while completed history and recurring assignments remain (#4791).
- [ ] Verify a secured road offsets its 5 containment loss once and preserved Red Forest evidence discounts only one eligible MDST purge from 75 to 50 PP (#4791).
- [ ] Run each military sealing, Strelok, and Kaymanov outcome from a common pre-choice checkpoint, confirm its own aftermath and modifiers without leaking another outcome's flags (#4791).
- [ ] Run Kaymanov with global Zones disabled, reference layout, and randomized layout in separate campaigns, confirm only the selected rule determines proliferation (#4791).
- [ ] Inspect activated global and regional anchors, including Aksai Chin, Lake Mungo, and the added reference-map sites, confirm local names, controller administration, and regional narratives (#4791).
- [ ] Advance footprint spread, recession, drift, and a full-footprint split, confirm anchors stay fixed and the child uses its parent's ID plus 100 with independent administration (#4791).
- [ ] With crossover content disabled, confirm none of its stories fire; with it enabled and a human holding Lake Mungo, complete Alice's contact and delayed return through save/reload and control transfer (#4791).

**Playthrough E: USA and a low-PP AI Zone controller, TOP enabled (covers #4791)**

- [ ] Discover the Monolith, smugglers, SIRCAA, and mercenaries at their actual activation thresholds, confirm groups 35 through 38 use state 698 and its current controller rather than the original host's capital (#4791).
- [ ] Inspect the person and organization packages during calm and crisis, confirm the crisis disclosure, exposure adjustment, harm adjustment, and native operation modifiers (#4791).
- [ ] Complete native person and facility operations in a live Zone, confirm only successful matching callbacks disturb containment and faction strength, while cancelled, stale, mismatched, or unsuccessful operations do not (#4791).
- [ ] Transfer the Zone during preparation and confirm the reviewed host, state, objective, sequence, and controller checks prevent a stale resolution (#4791).
- [ ] Let an AI controller with less than 50 PP and at least 10 treasury face containment under 30 or a breach, confirm the treasury relief path fires once and respects the shared cooldown and bankruptcy gates (#4791).
- [ ] Finish with a real save/reload and a multi-month campaign, confirm no accumulating STALKER errors, stuck pending reports, duplicate rewards, or sustained monthly slowdown (#4791).
