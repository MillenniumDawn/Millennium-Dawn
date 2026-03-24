---
title: "Dev Diary #55: Algeria — Le Pouvoir"
description: An in-depth look at the three interlocking political systems of Algeria — the Balance of Power, the Deep State, and the Cabinet.
permalink: /dev-diaries/55-algeria-le-pouvoir/
author: Okazaki
date: 2026-03-16
tags:
  - dev diary
  - v2.0
---

_By Okazaki (AKA Mostapha) – 16 Mar 2026_

**السلام عليكم و رحمة الله و بركاته!** Welcome to another Millennium Dawn Dev Diary. I'm Okazaki, and today I'll be walking you through one of the most politically layered countries in the mod — **Algeria**.

Algeria starts in the year 2000, fresh out of the Black Decade — a brutal civil war that claimed over 200,000 lives and left the country economically gutted and politically fractured. President Abdelaziz Bouteflika has staked his mandate on national reconciliation, but behind him stands **le Pouvoir** — the shadowy network that has ruled Algeria from the shadows since independence. Who really controls Algeria? That question is at the heart of everything we built.

---

### The Balance of Power: Le Pouvoir vs. Le Peuple

The first system you'll encounter is the **Balance of Power**, representing the ongoing struggle between two forces:

- **Le Pouvoir** — the military high command, the DRS (Département du Renseignement et de la Sécurité) and its all-seeing director **Mohamed Mediène "Toufik"** who ran the intelligence apparatus for 25 years, the FLN old guard, figures like **Khaled Nezzar** and **Larbi Belkheir** who cancelled the 1991 elections rather than let the FIS govern, and the patronage networks that have rotated power among themselves ever since.

- **Le Peuple** — a broad, evolving coalition that has never taken one single form. In 2000 it is the FFS of **Hocine Aït Ahmed** — the independence war hero who spent decades calling out the system from inside it — and the RCD, the Kabyle Berberist movement fresh from the Black Spring and the *aârouch* uprising of 2001, labour unions, independent journalists, and tens of thousands of ordinary citizens who mounted the localised street protests known as *protesta* throughout the 2000s without any party ever managing to channel their anger into a unified political force. The Hirak of 2019 was not the beginning of this story — it was its loudest chapter yet.

<img src="/assets/images/dev-diaries/055/bop_overview.png" alt="Algeria Balance of Power overview" class="mx-auto my-6 max-w-full" />

The bar starts at the center. Shift it far enough toward le Peuple and you trigger the **Democratic Surge** — Bouteflika falls, the opposition takes power, and Algeria enters a fragile transition. Shift it far enough toward le Pouvoir and the **Military Coup** fires — the generals formalize their grip and Algeria becomes a junta state.

Neither outcome is handed to you. Both require active work — and both carry real costs. The democratic path means confronting a military that has already done this before in 1992 and has no reason to stop now. The junta path delivers short-term stability but Algeria becomes ideologically rigid and internationally isolated.

Warning events fire as you approach either extreme, giving you a last chance to course-correct before the regime-defining outcome triggers.

<img src="/assets/images/dev-diaries/055/bop_warning.png" alt="Balance of Power warning event" class="mx-auto my-6 max-w-full" />

---

### The Deep State System

The second system is the **Deep State** — and this one runs whether you engage with it or not.

To understand what we were trying to capture here, you need to go back to **December 1991**. The FIS won the first round of parliamentary elections by a landslide. Rather than let them govern, the military — led by Defense Minister **Khaled Nezzar** and Chief of Staff **Mohamed Lamari** — cancelled the elections, forced President Chadli Bendjedid to resign, dissolved parliament, and handed power to a High State Committee. No single man stood on a tank. There was no formal coup declaration. Just a system asserting its own supremacy over a democratic result it did not like.

Then came **Liamine Zéroual**. Appointed president in 1994, he genuinely attempted to negotiate a political solution with the Islamists and sought to reclaim some presidential authority from the military. The generals progressively froze him out — advisors sidelined, communications controlled, decisions quietly reversed. By 1998, exhausted and unable to govern, he announced early elections and resigned before his term was up. He was not defeated by a vote. He was worn down by men who never appeared on television.

That dynamic — the civilian president as a managed facade while the real decisions happen elsewhere — is what we are modeling.

We track it through a single variable: **deep_state_power**, ranging from 0 to 30. It starts at 5 — the generals already have their fingers in everything — and grows passively every few weeks.

<img src="/assets/images/dev-diaries/055/deep_state_variable.png" alt="Deep state power variable tooltip" class="mx-auto my-6 max-w-full" />

As it crosses key thresholds, events force you to make increasingly difficult choices:

At **5** the deep state begins operating openly. At **10** you must decide whether to concede space or push back — at a real cost to stability. At **15**, military oversight of civilian institutions becomes formalized as a national idea. At **20**, the generals hold effective veto power over the government. And at **28**... the coup event begins firing.


A series of **random monthly events** also shift the variable — military contract corruption, intelligence overreach, retired generals entering politics through the back door, provincial commanders being promoted outside civilian channels, or foreign powers quietly offering to help you rein in the army. Every one of these reflects patterns that have played out repeatedly in Algeria since independence.


Certain focuses can freeze the variable's growth entirely. But you cannot simply ignore it. Le Pouvoir does not wait.

---

### The Cabinet System

The third system is the **Cabinet** — and this is where Algeria becomes genuinely personal.

We want the player to feel the impossible arithmetic of Algerian governance: every appointment either buys loyalty from the people or tolerance from the generals. You cannot fully have both.

The four key positions are the **Prime Minister**, the **Minister of Defense**, the **Intelligence Chief**, and the **Interior Minister**. Each has multiple candidates with different tradeoff profiles. Appointing a hardline general to Defense brings military buy-in — but feeds the deep state variable. Appointing a civilian reformist does the opposite, and the brass will make their displeasure known.

<img src="/assets/images/dev-diaries/055/cabinet_appointment.png" alt="Cabinet appointment event with candidate options" class="mx-auto my-6 max-w-full" />

Loyalty decays naturally over time. When it drops below a critical threshold, a **Cabinet Disloyalty Crisis** fires — you dismiss, negotiate, or accept the fallout.


When deep state influence grows high enough, it starts pressuring your cabinet directly — pushing ministers to align with military interests regardless of your preferences.



To give you a sense of why we built this the way we did — consider the real case of **Major General Abdelkader Haddad**, known by his nickname **Nasser El Djinn** (literally: the Genie — the unseen force that moves things you cannot see). He was the head of the DGSI, Algeria's internal security directorate, a man who had accumulated decades of secrets about every major figure in the system. Bouteflika's restructuring of the DRS — his long attempt to break the intelligence apparatus's autonomous power and bring it under presidential control — created figures like Haddad: loyal to factions rather than to any institution, dangerous precisely because of what they knew. When his faction lost the internal power struggle, he was placed under house arrest. Knowing what typically awaits men in his position — and fearing his death would be staged as a suicide — he escaped across the Mediterranean by speedboat to Alicante, Spain in September 2025. Algiers woke up under a security lockdown. Helicopters over the capital. Roadblocks across the city. The man who once ran internal security had become its most wanted fugitive — and he was carrying the regime's darkest secrets with him across the sea.

That is the machine we are modeling. Not a clean hierarchy. Not a stable authoritarian government you can optimize. A system that devours its own — where yesterday's intelligence chief is tomorrow's prisoner, and where the most powerful men in the country can find themselves fleeing on a speedboat because they know too much.

<img src="/assets/images/dev-diaries/055/cabinet.png" alt="Cabinet Overview" class="mx-auto my-6 max-w-full" />

---

### How It All Connects

These three systems are not independent — they feed into each other constantly.

Your cabinet appointments shift **deep_state_power**. The deep state variable shifts the **Balance of Power**. The Balance of Power determines which focus branches open, which in turn shapes your cabinet options. And all of this runs in the background while you are also trying to rebuild an economy shattered by a decade of civil war, manage Kabyle satisfaction before it collapses, navigate the Sonatrach corruption scandals, and decide what to do about the FIS.


Algeria is not a country you can optimize your way through. Every decision has a cost. Le Pouvoir is patient. And the people have been waiting for a long time.

We look forward to hearing your thoughts. Until next time — **يحيا الشعب الجزائري!**

— Okazaki (AKA Mostapha)
