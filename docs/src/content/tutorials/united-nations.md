---
title: United Nations
description: Full guide to the United Nations in Millennium Dawn, membership, recognition, ascension, voting, the Security Council, the General Assembly, vote swaying, and the aid budget.
---

The United Nations is the mod's central diplomatic body. It runs on two chambers, the Security Council and the General Assembly, both of which vote on resolutions that bind or nudge the world. Full members get a standing bonus to stability, political power, and foreign influence. Nations without recognition, and non-state actors, are locked out entirely and pay a real penalty for it. This guide covers membership, how to get recognized and ascend to full membership, how votes actually resolve, and how to use the UN's tools (proposals, swaying, and the aid budget) to your advantage.

---

## Table of Contents

- [Membership and Recognition Status](#membership-and-recognition-status)
- [Gaining International Recognition](#gaining-international-recognition)
- [The Ascension Process](#the-ascension-process)
- [How Voting Works](#how-voting-works)
- [The Security Council](#the-security-council)
- [The General Assembly](#the-general-assembly)
- [Vote Swaying](#vote-swaying)
- [The UN Budget and Aid Programs](#the-un-budget-and-aid-programs)
- [Strategic Tips](#strategic-tips)

---

## Membership and Recognition Status

Every internationally recognized nation is automatically a General Assembly member and carries the UN member bonus: +1% stability, +10% political power gain, plus a political power factor, foreign influence gain, foreign influence defense, and investment cost/duration bonus that all scale with how much you put into the UN budget relative to what you take out (see [Aid Programs](#the-un-budget-and-aid-programs)).

Nations that aren't recognized carry a penalty idea instead, and non-state actors carry a harsher one on top of that:

| Status                          | Political Power | Trade Opinion | Other Penalties                                         |
| ------------------------------- | --------------- | ------------- | ------------------------------------------------------- |
| Lacks International Recognition | -5%             | -10%          | Barred from every UN vote and program                   |
| Non-State Actor                 | -10%            | -25%          | -20% research speed, -5% tax revenue, -1000 ally desire |

Losing recognition (or your UN seat) strips you out of both chambers immediately: any Security Council or General Assembly seat you held is vacated, and any vote about you in the queue is canceled.

---

## Gaining International Recognition

Recognition is bilateral and tracked per nation. Every state that formally recognizes you adds to your support count and grants you political power scaled to that state's power ranking (Non-Power +5, Minor Power +10, Regional Power +15, Large Power +25, Great Power +50, Superpower +100). As an unrecognized state, you have several ways to build that count from the State Recognition screen:

- **Grant Recognition** (25 PP): an ally that already recognizes you can extend recognition to you directly and instantly.
- **Pressure Countries** (100 PP): an ally asks other influential UN members to recognize you.
- **Recognition Campaign** (200 PP, once a year): you personally petition every UN member state to recognize you.
- **Improve Relations** (200 PP, once a year): a general goodwill campaign with every UN member, improving the odds that future recognition attempts land.
- **Ask for Independence** (350 PP, once a year, only if you split from a parent state): you formally ask your former ruler to recognize your independence. The odds are low unless you've built up good relations with them, but success also gets them to lobby other nations on your behalf.

AI-controlled UN members also periodically decide to recognize unrecognized states on their own, especially ones they have a good opinion of.

---

## The Ascension Process

Once your recognition count crosses roughly 40% of the current General Assembly's membership, you get a one-time notification that you're eligible to seek full membership. From there, ascension is a two-stage vote:

1. **Security Council recommendation.** Requires 9 or more yes votes (of 15 seats) and zero "No" votes from a permanent member. Any single permanent member's own cast "No" vote vetoes the recommendation outright.
2. **General Assembly admission.** Only reached if the Security Council stage passes. Requires a true two-thirds majority of current General Assembly members voting yes.

You (or your government, if AI-controlled) submit the bid yourself from the UN screen; it requires at least 200 political power on hand and locks you out of trying again for 365 days. There is no partial-membership outcome: if the General Assembly falls short of two-thirds, even by one vote, the bid fails completely and you remain unrecognized, exactly as if you'd lost by a landslide. Success removes your recognition penalty (and non-state actor penalty, if you carried one), seats you in the General Assembly, and grants the full UN member bonus.

---

## How Voting Works

Both chambers can only run one live vote at a time; anything else proposed while a vote is already underway (or its cooldown is active) queues up and waits its turn. Cooldowns run from when the previous vote in that chamber finished: 50 days for the General Assembly, 20 days for the Security Council. Security Council seat-confirmation votes and raid-response sanction votes automatically jump to the front of the General Assembly queue ahead of everything else.

Once a vote opens, every eligible member gets a voting event with **Yes**, **No**, and **Abstain**, with 4 days to respond. The vote officially closes 5 days after it opens, but it can resolve earlier than that if the passing threshold is already mathematically locked in before the window runs out.

Passing thresholds depend on the chamber and vote type:

- **Security Council:** 9 or more yes votes out of 15, and no permanent member has cast a "No" vote. A single permanent member's veto blocks the resolution regardless of every other vote.
- **General Assembly, two-thirds votes:** UN ascension, Security Council seat confirmation, and budget rate changes all require a true two-thirds supermajority of current members.
- **General Assembly, simple majority votes:** the raid-response sanctions vote and all twelve development resolutions only need more yes votes than no votes; abstentions don't count toward either side.

You can set your own vote to **Auto-Accept**, **Auto-Reject**, or **Auto-Abstain** for an entire chamber so you never see the popups again. Auto-Reject counts as an ordinary "No" vote, but it will not cast a veto even if you're a permanent Security Council member; only manually clicking "No" yourself exercises that veto power.

---

## The Security Council

The Security Council has 15 seats: 5 permanent members (China, France, Russia, the United Kingdom, and the United States) plus 10 elected members split regionally across Asia & Africa, Europe & the Americas, and South America. Unrecognized nations and non-state actors are never eligible for a seat.

**Election cycle.** Every June, one candidate is seeded for each open regional seat (the regional split alternates by year, so different regions get more or fewer seats depending on whether it's an even or odd year). Each candidate then goes through its own General Assembly confirmation vote (two-thirds majority). A candidate who passes locks in the seat and the next candidate in queue comes up automatically; a candidate who fails is dropped and replaced by another random pick from the same regional pool (capped at 15 re-rolls for the whole election). New members take their seats the following January, when the oldest cohort of elected members rotates out. If fewer replacements were confirmed than seats available, the outgoing members simply serve another term rather than leave a seat empty.

**Resolutions.** Only sitting Security Council members can propose a resolution, and doing so costs 250 political power. You can't propose against a nation you're at war with, can't propose anything while you yourself are waging an offensive war, and can't stack a second pending action against a target that already has one queued.

| Resolution                | Effect                                                                                                                                                                                                                                                                                                                      |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pressure to End War       | Target gets 210 days to end all its offensive wars. Failing to comply triggers automatic UNSC sanctions.                                                                                                                                                                                                                    |
| Establish Sanctions       | Binding trade opinion penalty of -0.5% per UN member (capped at -100%) and research speed penalty of -0.3% per UN member (capped at -50%) against the target. Lifts automatically once the target's world tension has fully subsided, it's no longer waging an offensive war, and it hasn't defied a volunteer restriction. |
| Restrict Volunteer Forces | Target can no longer send or receive volunteer divisions with other nations for the duration of its offensive war.                                                                                                                                                                                                          |
| Arms Embargo              | Target is locked out of the international arms market and blocked from sending or receiving lend-lease.                                                                                                                                                                                                                     |

---

## The General Assembly

Every recognized UN member votes in every General Assembly resolution. Beyond ascension and Security Council confirmations, the Assembly handles:

- **Budget rate changes** (200 PP, two-thirds majority, one attempt allowed anywhere in the world per year): raises or lowers the mandatory UN contribution rate by 0.01 percentage points, within a 0.01%-0.1% band.
- **Raid-response sanctions** (simple majority, no PP cost to trigger): fires automatically after a nation is caught conducting a raid or military strike on another. Trade opinion drops by 0.5% per yes vote (capped at -100%) and research speed drops by 0.1% per yes vote (capped at -50%), scaling with how many members vote in favor.
- **Development resolutions** (150 PP to propose, any UN member, simple majority, one live proposal per resolution type at a time): twelve thematic, non-binding resolutions that grant a one-year bonus idea to every nation that voted yes.

| Resolution                 | Effect for one year                                                                                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Poverty Reduction          | +3% stability, +4% consumer goods cost                                                                                                                               |
| Food Security              | +5% agricultural productivity, +5% agriculture district construction speed, +2% consumer goods cost, -2% civilian factory output                                     |
| Global Health              | +3% stability, -10% healthcare cost, +3% consumer goods cost                                                                                                         |
| Education Initiative       | +3% research speed, -10% education cost, +2% consumer goods cost, -2% construction speed                                                                             |
| Clean Energy               | +10% renewable energy construction speed, -5% renewable energy construction cost, -10% fossil powerplant construction speed, -2% civilian factory output             |
| Economic Growth            | +50% productivity growth, +3% civilian factory output, +3% consumer goods cost, -5% political power                                                                  |
| Infrastructure Development | +10% infrastructure construction speed, +5% industrial complex construction speed, -5% arms factory construction speed, +2% consumer goods cost                      |
| Reduced Inequality         | +5% stability, +4% consumer goods cost, -5% political power                                                                                                          |
| Climate Action             | +5% renewable energy construction speed, -15% fossil powerplant construction speed, -3% civilian factory output, +2% stability                                       |
| Peace & Institutions       | +50% political power gain, +10% drift defense, -10% foreign subversive activity, +2% consumer goods cost, -5% arms factory construction speed                        |
| Trade Partnerships         | +10% trade opinion, -5% trade cost for the target nation, -3% political power, +1% consumer goods cost                                                               |
| Digital Development        | +10% internet station construction speed, +5% microchip plant construction speed, +2% research speed, +3% consumer goods cost, -3% infrastructure construction speed |

If you voted No or Abstain on a resolution that passed, you get a follow-up choice once it's over: accept the same one-year bonus everyone else got, or formally reject it. Rejecting costs you a lasting opinion penalty with whichever nation proposed the resolution (roughly -15 general opinion and -10 trade opinion, both decaying slowly over time).

---

## Vote Swaying

While a vote is live, you can click a nation's flag in the vote tally to try to change their cast vote. You need enough Foreign Influence over them to attempt it: more than 15% for General Assembly votes, more than 40% for Security Council votes.

- **Left-click** flips their vote to the opposite side and spends 10% of your influence over them, win or lose.
- **Right-click** nudges them toward Abstain instead, for a cheaper 5% of your influence.

A nation can only be swayed once per vote; once it works, that nation is locked from being swayed again until the vote resolves. You can never sway your own vote.

If they consider your offer, you pick what to put on the table:

- Trade Agreement and Mutual Investment Treaty (also lifts any active embargo between you)
- A direct payment of 0.25% of their GDP
- Military, air base, and full satellite system access (both GPS-equivalent and communications satellites, military and civilian)
- A year-long mutual economic aid deal: you take a lasting penalty (-15% construction speed, -10% research speed, -5% civilian and dockyard capacity) while they get the mirrored bonus. You can't open a second aid-based offer while one you're already paying for is still active.

If they refuse, your opinion of them takes a real hit (roughly -25, decaying over time). If your influence over them is above 50%, refusing you also costs them 250 political power.

---

## The UN Budget and Aid Programs

Every UN member automatically contributes GDP times the current global contribution rate (0.01%-0.1% of GDP, set by the budget votes above) to the General Operating Budget each week; contributions below a $0.001bn floor don't count and earn no benefit. That budget splits evenly across three programs:

- **UNESCO**: political power gain and research speed.
- **UNIDO**: construction speed, plus free leased civilian factories for the neediest recipients.
- **UNCDF**: productivity growth and cheaper construction.

You can formally join any program (100 PP, requires UN membership) to add a voluntary contribution on top of your automatic share, adjustable in $0.1bn/$0.25bn/$0.5bn/$1bn steps and applied starting the next calendar year. Contributing more raises your foreign influence bonuses and political power gain.

If your nation is underperforming relative to the UN-wide average for a program's specialty (or sits below $1,000bn GDP for UNCDF), you can request subsidies from that program instead. Subsidies hand you a direct share of the program's benefits, but drawing from a program quietly reduces how much you gain from the base UN membership bonus, and they expire automatically once you no longer qualify. You can cancel all your optional contributions at once (500 PP) if you need the money elsewhere.

---

## Strategic Tips

1. **Recognition is a campaign, not an event.** Stack Improve Relations and Recognition Campaign attempts a year apart, and lean on allies for Grant Recognition and Pressure Countries in between. Don't wait passively at 39% support.
2. **One hostile permanent member can wall off the Security Council forever.** Cultivate at least one friendly P5 relationship, or be ready to sway one, before you need a resolution to pass.
3. **Weigh raids against the diplomatic fallout.** Getting caught triggers an automatic, simple-majority sanctions vote scaled to how many nations vote against you, no proposal or PP required from anyone.
4. **Budget votes are a once-a-year window, globally.** If you want to shape the UN's contribution rate, act early in the year before someone else locks in a different rate for everyone.
5. **Vote yes on development resolutions that match your economy.** They're a free one-year bonus for anyone who backs them, and even a No or Abstain vote gets you a second chance to accept afterward if you change your mind.
6. **Save your influence for votes that matter.** Swaying costs real influence and, if it fails, real opinion; don't burn it on a resolution you don't actually need to pass or block.
