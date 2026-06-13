#!/usr/bin/env python3
r"""
summarize_game_log.py  -  Hearts of Iron IV (Millennium Dawn) game.log summarizer.

HOI4's game.log is NOT a save file. What makes it summarizable is that mods like
Millennium Dawn dump scripted `log = "..."` effects into it. Every such line looks like:

    [17:40:45][2007.05.21.01][effectbase.cpp:1783]:  1:00, 21 May, 2007: Brazil: Focus BRA_protect_brazilian_democracy
    \_wall clock_/\_game date_/                       \_____ scripted payload "<Country>: <message>" _____/

This script streams the log once, parses (game-date, country, message) out of every
scripted line, classifies each message, and prints a readable "what happened" report:
session info, most active countries, conflicts/crises timeline, politics (elections,
recognitions, focuses), and a per-country deep dive with the latest economic snapshot.

The bulk of the file is economic/AI DEBUG spam (Weekly Economic Update, AI Tax, CT AI,
Energy GUI, ...). Those are summarized as latest-state snapshots, not as a timeline,
and hidden from the event feed unless you pass --full.

Usage:
    python summarize_game_log.py "path/to/game.log"
    python summarize_game_log.py game.log --country Korea
    python summarize_game_log.py game.log --top 20 --since 2003.1.1
    python summarize_game_log.py game.log --json > summary.json

No third-party dependencies. Python 3.8+.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict

# HOI4 writes game.log as UTF-8. Force UTF-8 stdout regardless of the host console
# code page so accented country names (Côte d'Ivoire) print instead of crashing on
# a cp1252 Windows console.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

LOG_ENCODING = "utf-8"

# ---------------------------------------------------------------------------
# Line parsing
# ---------------------------------------------------------------------------

# Game date appears as [YYYY.MM.DD.HH]. Lines often nest two of these (a 1799
# wrapper around the 1783 line); we take the LAST one, which is the real event time.
DATE_RE = re.compile(r"\[(\d{4})\.(\d{1,2})\.(\d{1,2})\.\d{1,2}\]")

# The scripted payload follows the human-readable date "H:MM, D Month, YYYY: ".
# Capture everything after it: that's "<Country>: <message>".
PAYLOAD_RE = re.compile(r"\d{1,2}:\d{2}, \d{1,2} [A-Za-z]+, \d{4}: (.+?)\s*$")

# Wall-clock timestamp [HH:MM:SS] at the very start of a physical line.
WALL_RE = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]")

# Event id like "iraq_civil_war.69.a executed" / "recognition.10.b" -> namespace.
EVENT_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\.\d+")

# Weekly Economic Update fields.
ECON_RE = re.compile(
    r"Weekly Economic Update: Treasury: (?P<treasury>-?[\d.]+) "
    r"Treasury Rate: (?P<rate>-?[\d.]+) "
    r"Debt: (?P<debt>-?[\d.]+) "
    r"Interest Rate: (?P<interest>-?[\d.]+) "
    r"Population Tax Rate: (?P<poptax>-?[\d.]+) "
    r"Corporate Tax Rate: (?P<corptax>-?[\d.]+)"
)
INFLATION_RE = re.compile(r"Inflation Update: Current Inflation Rate: (-?[\d.]+)%")
ANNEX_RE = re.compile(r"^(.+?) annexed (.+?)(?: -|$)")

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Keywords (matched against namespace + message) that mark a "significant" event
# worth putting on the conflict / crisis timeline.
CONFLICT_KW = ("civil_war", "civilwar", "_war", "war_", "war.", "terror", "raid",
               "coup", "revolt", "insurg", "border", "invasion", "intervention",
               "uprising", "rebellion", "secession")
POLITICS_KW = ("election", "recognition", "independ", "referendum", "union",
               "annex", "coalition")

# DEBUG / AI / economic chatter that should never reach the event feed.
SPAM_PREFIXES = (
    "DEBUG:", "AI Tax:", "AI Weapon Dump", "Highest Economic Expenditure",
    "Weekly Economic Update", "Expected military spending",
    "Expected education spending", "Expected police spending",
    "Expected welfare spending", "Expected healthcare spending",
    "Expected administrative spending", "Next Cycle Political Power Cost",
    "Index:", "Auto influencing",
)


def date_key(y, m, d):
    return y * 10000 + m * 100 + d


def fmt_date(y, m, d):
    return f"{d:>2} {MONTHS[m]} {y}"


# ---------------------------------------------------------------------------
# Core parse
# ---------------------------------------------------------------------------

def parse(path, since=None, until=None):
    stats = {
        "lines": 0, "parsed": 0, "skipped": 0,
        "wall_first": None, "wall_last": None,
        "game_first": None, "game_last": None,
    }
    activity = Counter()                       # entries per country
    categories = Counter()                     # message category -> count
    focuses = defaultdict(Counter)             # country -> focus_id -> count
    decisions = defaultdict(Counter)           # country -> decision -> count
    events = defaultdict(lambda: {"count": 0, "countries": Counter(),
                                  "first": None, "last": None})  # namespace -> info
    conflicts = []                             # significant event rows (timeline)
    annexations = []                           # (datekey, ymd, actor, target)
    economy = {}                               # country -> latest econ snapshot
    inflation = {}                             # country -> (datekey, ymd, rate)
    country_events = defaultdict(list)         # country -> [(datekey, ymd, kind, detail)]
    ideas = defaultdict(Counter)               # country -> idea -> count
    diplomacy = defaultdict(Counter)           # country -> action -> count
    events_by_country = defaultdict(Counter)   # country -> event namespace -> count

    def in_range(dk):
        if since is not None and dk < since:
            return False
        if until is not None and dk > until:
            return False
        return True

    with open(path, "r", encoding=LOG_ENCODING, errors="replace") as fh:
        for line in fh:
            stats["lines"] += 1

            w = WALL_RE.match(line)
            if w:
                wt = (int(w.group(1)), int(w.group(2)), int(w.group(3)))
                if stats["wall_first"] is None:
                    stats["wall_first"] = wt
                stats["wall_last"] = wt

            payload_m = PAYLOAD_RE.search(line)
            if not payload_m:
                stats["skipped"] += 1
                continue

            dates = DATE_RE.findall(line)
            if not dates:
                stats["skipped"] += 1
                continue
            y, m, d = (int(x) for x in dates[-1])
            dk = date_key(y, m, d)
            ymd = fmt_date(y, m, d)

            if stats["game_first"] is None:
                stats["game_first"] = (dk, ymd)
            stats["game_last"] = (dk, ymd)

            if not in_range(dk):
                continue

            payload = payload_m.group(1)
            stats["parsed"] += 1

            # Annexation lines have no "Country: " head ("Iraq annexed Iraq - ...").
            am = ANNEX_RE.match(payload)
            if am and " annexed " in payload:
                actor, target = am.group(1).strip(), am.group(2).strip()
                annexations.append((dk, ymd, actor, target))
                activity[actor] += 1
                categories["annexation"] += 1
                country_events[actor].append((dk, ymd, "annex", f"annexed {target}"))
                continue

            if ": " in payload:
                country, message = payload.split(": ", 1)
            else:
                country, message = payload, ""
            country = country.strip()
            message = message.strip()
            activity[country] += 1

            kind, detail = classify(country, message, economy, inflation,
                                    dk, ymd)
            categories[kind] += 1

            if kind == "focus":
                focuses[country][detail] += 1
                country_events[country].append((dk, ymd, "focus", detail))
            elif kind in ("decision", "decision_remove"):
                tag = detail if kind == "decision" else f"-{detail}"
                decisions[country][tag] += 1
                country_events[country].append((dk, ymd, kind, detail))
            elif kind == "idea_add":
                ideas[country][detail] += 1
            elif kind == "diplomacy":
                # "diplomatic action <phase> <action>" -> keep the action token.
                toks = message.split()
                diplomacy[country][toks[-1] if toks else message] += 1
            elif kind == "event":
                ns = detail
                events_by_country[country][ns] += 1
                info = events[ns]
                info["count"] += 1
                info["countries"][country] += 1
                if info["first"] is None:
                    info["first"] = (dk, ymd)
                info["last"] = (dk, ymd)
                lower = (ns + " " + message).lower()
                if any(k in lower for k in CONFLICT_KW):
                    conflicts.append((dk, ymd, country, ns, "conflict"))
                    country_events[country].append((dk, ymd, "conflict", ns))
                elif any(k in lower for k in POLITICS_KW):
                    conflicts.append((dk, ymd, country, ns, "politics"))
                    country_events[country].append((dk, ymd, "politics", ns))

    return {
        "stats": stats, "activity": activity, "categories": categories,
        "focuses": focuses, "decisions": decisions, "events": events,
        "conflicts": conflicts, "annexations": annexations,
        "economy": economy, "inflation": inflation,
        "country_events": country_events,
        "ideas": ideas, "diplomacy": diplomacy,
        "events_by_country": events_by_country,
    }


def classify(country, message, economy, inflation, dk, ymd):
    """Return (kind, detail). Side-effect: record economy/inflation snapshots."""
    if message.startswith("Focus "):
        return "focus", message[6:].strip()
    if message.startswith(("Decision remove ", "Decision Remove ")):
        return "decision_remove", message.split(" ", 2)[2].strip()
    if message.startswith("Decision "):
        return "decision", message[9:].strip()
    if message.startswith("add idea "):
        return "idea_add", message[9:].strip()
    if message.startswith("remove idea"):
        return "idea_remove", message[12:].strip()
    if message.startswith("diplomatic action"):
        return "diplomacy", message
    if message.startswith("Weekly Economic Update"):
        em = ECON_RE.search(message)
        if em:
            prev = economy.get(country)
            if prev is None or dk >= prev["_dk"]:
                economy[country] = {
                    "_dk": dk, "date": ymd,
                    "treasury": float(em.group("treasury")),
                    "treasury_rate": float(em.group("rate")),
                    "debt": float(em.group("debt")),
                    "interest": float(em.group("interest")),
                    "pop_tax": float(em.group("poptax")),
                    "corp_tax": float(em.group("corptax")),
                }
        return "economy", None
    im = INFLATION_RE.search(message)
    if im:
        prev = inflation.get(country)
        rate = float(im.group(1))
        if prev is None or dk >= prev[0]:
            inflation[country] = (dk, ymd, rate)
        return "inflation", None
    if any(message.startswith(p) for p in SPAM_PREFIXES):
        return "spam", None
    em = EVENT_RE.match(message)
    if em:
        return "event", em.group(1)
    if message.endswith("executed"):
        return "effect", message
    return "other", None


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def human(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)
    for unit, div in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(n) >= div:
            return f"{n/div:.2f}{unit}"
    return f"{n:.0f}"


def money(n):
    """Full figure with thousands separators, e.g. 4002, -14936 -> '4,002', '-14,936'."""
    try:
        return f"{float(n):,.0f}"
    except (TypeError, ValueError):
        return str(n)


def resolve_name(data, requested):
    """Match a user-supplied name to an exact in-log country name."""
    for c in data["activity"]:
        if c.lower() == requested.lower():
            return c
    for c in data["activity"]:
        if requested.lower() in c.lower():
            return c
    return requested  # unknown; deep_dive will say "no entries"


def pick_countries(data, requested, top_countries):
    """Build the ordered, de-duplicated list of countries to deep-dive."""
    chosen = []
    seen = set()

    def add(name):
        if name and name not in seen:
            seen.add(name)
            chosen.append(name)

    for r in (requested or []):
        add(resolve_name(data, r))

    # Auto-include the N most active countries (by scripted entries).
    for c, _ in data["activity"].most_common(top_countries or 0):
        add(c)

    # Nothing requested at all -> fall back to the single best guess of the
    # human player (most decisions). The log never records the player directly.
    if not chosen and top_countries == 0:
        if data["decisions"]:
            add(max(data["decisions"],
                    key=lambda c: sum(data["decisions"][c].values())))
        elif data["activity"]:
            add(data["activity"].most_common(1)[0][0])
    return chosen


def report(data, countries=None, top=15, detail=False):
    out = []
    p = out.append
    s = data["stats"]

    p("=" * 70)
    p(" HOI4 / Millennium Dawn  —  game.log summary")
    p("=" * 70)

    # --- session ---
    if s["game_first"] and s["game_last"]:
        p(f"In-game span : {s['game_first'][1]}  ->  {s['game_last'][1]}")
    if s["wall_first"] and s["wall_last"]:
        wf, wl = s["wall_first"], s["wall_last"]
        secs = (wl[0]*3600+wl[1]*60+wl[2]) - (wf[0]*3600+wf[1]*60+wf[2])
        if secs < 0:
            secs += 24*3600
        p(f"Real session : {wf[0]:02d}:{wf[1]:02d}:{wf[2]:02d} -> "
          f"{wl[0]:02d}:{wl[1]:02d}:{wl[2]:02d}  ({secs//3600}h{(secs%3600)//60:02d}m)")
    p(f"Log lines    : {s['lines']:,}   parsed scripted entries: {s['parsed']:,}")

    cats = data["categories"]
    if cats:
        nice = ", ".join(f"{k} {v:,}" for k, v in cats.most_common())
        p(f"Entry types  : {nice}")

    # --- most active ---
    p("")
    p("-" * 70)
    p(f" Most active countries (scripted log entries)")
    p("-" * 70)
    for c, n in data["activity"].most_common(top):
        f = sum(data["focuses"][c].values())
        d = sum(data["decisions"][c].values())
        p(f"  {c:<32} {n:>7,} entries   ({f} focuses, {d} decisions)")

    # --- conflicts & crises ---
    confl = [r for r in data["conflicts"] if r[4] == "conflict"]
    p("")
    p("-" * 70)
    p(" Conflicts & crises (war / civil-war / terror / raid / coup events)")
    p("-" * 70)
    if not confl and not data["annexations"]:
        p("  (none detected)")
    # group conflict event namespaces
    grp = defaultdict(lambda: {"n": 0, "countries": Counter(), "first": None, "last": None})
    for dk, ymd, c, ns, _ in confl:
        g = grp[ns]
        g["n"] += 1
        g["countries"][c] += 1
        if g["first"] is None:
            g["first"] = ymd
        g["last"] = ymd
    for ns, g in sorted(grp.items(), key=lambda kv: -kv[1]["n"]):
        who = ", ".join(f"{c}({n})" for c, n in g["countries"].most_common(4))
        span = g["first"] if g["first"] == g["last"] else f"{g['first']} -> {g['last']}"
        p(f"  {ns:<28} {g['n']:>4}x   [{span}]   {who}")
    if data["annexations"]:
        p("")
        p("  Annexations:")
        for dk, ymd, actor, target in sorted(data["annexations"])[:40]:
            if actor == target:
                continue
            p(f"    {ymd:>12}   {actor}  ->  {target}")

    # --- politics ---
    pol = [r for r in data["conflicts"] if r[4] == "politics"]
    if pol:
        p("")
        p("-" * 70)
        p(" Politics (elections / recognitions / unions)")
        p("-" * 70)
        pgrp = defaultdict(lambda: {"n": 0, "countries": Counter(), "first": None, "last": None})
        for dk, ymd, c, ns, _ in pol:
            g = pgrp[ns]
            g["n"] += 1
            g["countries"][c] += 1
            if g["first"] is None:
                g["first"] = ymd
            g["last"] = ymd
        for ns, g in sorted(pgrp.items(), key=lambda kv: -kv[1]["n"])[:20]:
            who = ", ".join(f"{c}({n})" for c, n in g["countries"].most_common(4))
            span = g["first"] if g["first"] == g["last"] else f"{g['first']} -> {g['last']}"
            p(f"  {ns:<28} {g['n']:>4}x   [{span}]   {who}")

    # --- national finances ---
    # Sort by DEBT, not treasury: most majors run huge debt on a near-empty
    # treasury, so a treasury sort hides exactly the indebted countries.
    if data["economy"]:
        p("")
        p("-" * 70)
        p(" National finances — most indebted (latest Weekly Economic Update)")
        p("-" * 70)
        p(f"  {'Country':<26} {'Treasury':>12} {'Debt':>12} {'Net':>12}  "
          f"{'Tax p/c':>8}   Infl")
        ranked = sorted(data["economy"].items(),
                        key=lambda kv: kv[1]["debt"], reverse=True)[:top]
        for c, e in ranked:
            inf = data["inflation"].get(c)
            inf_s = f"{inf[2]:+.1f}%" if inf else "—"
            net = e["treasury"] - e["debt"]
            tax = f"{e['pop_tax']:.0f}/{e['corp_tax']:.0f}%"
            p(f"  {c:<26} {money(e['treasury']):>12} {money(e['debt']):>12} "
              f"{money(net):>12}  {tax:>8}   {inf_s}")
        zero = sum(1 for e in data["economy"].values() if e["debt"] == 0)
        p(f"  ({len(data['economy'])} countries tracked; {zero} carry zero debt — "
          "mostly oil/surplus states, omitted above)")

    # --- country deep dives ---
    for c in (countries or []):
        deep_dive(out, data, c, detail=detail)

    p("")
    return "\n".join(out)


def deep_dive(out, data, country, detail=False):
    p = out.append
    # caps grow when --detail is on
    cap_focus = 9999 if detail else 25
    cap_dec = 30 if detail else 15
    cap_evt = 60 if detail else 30

    p("")
    p("=" * 70)
    p(f" Country focus: {country}")
    p("=" * 70)
    if country not in data["activity"]:
        p("  No scripted log entries found for this country.")
        p("  (Pass --country with an exact in-log name, e.g. 'North Korea'.)")
        return

    foc_total = sum(data["focuses"].get(country, {}).values())
    dec_total = sum(data["decisions"].get(country, {}).values())
    p(f"  Scripted entries: {data['activity'][country]:,}   "
      f"focuses: {foc_total}   decisions: {dec_total}   "
      f"events: {sum(data['events_by_country'].get(country, {}).values())}")

    e = data["economy"].get(country)
    if e:
        net = e["treasury"] - e["debt"]
        p("")
        p(f"  Economy (as of {e['date']}):")
        p(f"    Treasury   {money(e['treasury']):>12}   (rate {e['treasury_rate']:+.2f}/wk)")
        p(f"    Debt       {money(e['debt']):>12}   (interest {e['interest']:.2f}%)")
        p(f"    Net        {money(net):>12}")
        p(f"    Tax        population {e['pop_tax']:.0f}%   corporate {e['corp_tax']:.0f}%")
    inf = data["inflation"].get(country)
    if inf:
        p(f"    Inflation  {inf[2]:>+9.2f}%  (as of {inf[1]})")

    foc = data["focuses"].get(country)
    if foc:
        p("")
        p(f"  National focuses completed ({foc_total} total, latest first):")
        fl = [ev for ev in data["country_events"][country] if ev[2] == "focus"]
        shown = fl[-cap_focus:]
        if len(fl) > len(shown):
            p(f"    ... {len(fl) - len(shown)} earlier focuses omitted (use --detail) ...")
        for dk, ymd, _, det in shown:
            p(f"    {ymd:>12}   {det}")

    dec = data["decisions"].get(country)
    if dec:
        p("")
        p(f"  Most-used decisions ({dec_total} total):")
        for name, n in dec.most_common(cap_dec):
            p(f"    {n:>4}x  {name}")

    idea = data["ideas"].get(country)
    if idea:
        p("")
        p(f"  Ideas / laws adopted ({sum(idea.values())} total):")
        for name, n in idea.most_common(cap_dec):
            suffix = f"  x{n}" if n > 1 else ""
            p(f"    {name}{suffix}")

    evns = data["events_by_country"].get(country)
    if evns and detail:
        p("")
        p(f"  Event chains fired (by namespace):")
        for name, n in evns.most_common(20):
            p(f"    {n:>4}x  {name}")

    dip = data["diplomacy"].get(country)
    if dip and detail:
        p("")
        p(f"  Diplomatic actions ({sum(dip.values())} total):")
        for name, n in dip.most_common(15):
            p(f"    {n:>4}x  {name}")

    # conflict / political involvement
    ce = [ev for ev in data["country_events"][country]
          if ev[2] in ("conflict", "politics", "annex")]
    if ce:
        p("")
        p(f"  Notable events involving {country}:")
        seen = set()
        for dk, ymd, kind, det in ce:
            key = (kind, det)
            if key in seen:
                continue
            seen.add(key)
            p(f"    {ymd:>12}   [{kind}] {det}")
            if len(seen) >= cap_evt:
                break


def to_json(data, countries=None, top=15):
    s = data["stats"]
    obj = {
        "session": {
            "game_first": s["game_first"][1] if s["game_first"] else None,
            "game_last": s["game_last"][1] if s["game_last"] else None,
            "wall_first": s["wall_first"], "wall_last": s["wall_last"],
            "lines": s["lines"], "parsed": s["parsed"],
        },
        "categories": dict(data["categories"]),
        "most_active": data["activity"].most_common(top),
        "conflicts": [
            {"date": ymd, "country": c, "namespace": ns}
            for dk, ymd, c, ns, t in data["conflicts"] if t == "conflict"
        ],
        "politics": [
            {"date": ymd, "country": c, "namespace": ns}
            for dk, ymd, c, ns, t in data["conflicts"] if t == "politics"
        ],
        "annexations": [
            {"date": ymd, "actor": a, "target": t}
            for dk, ymd, a, t in sorted(data["annexations"]) if a != t
        ],
        "economy": {
            c: {k: v for k, v in e.items() if not k.startswith("_")}
            for c, e in data["economy"].items()
        },
        "inflation": {c: {"date": v[1], "rate": v[2]} for c, v in data["inflation"].items()},
    }
    obj["focus_countries"] = {}
    for country in (countries or []):
        if country not in data["activity"]:
            continue
        obj["focus_countries"][country] = {
            "entries": data["activity"][country],
            "focuses": dict(data["focuses"][country]),
            "decisions": dict(data["decisions"][country]),
            "ideas": dict(data["ideas"].get(country, {})),
            "events": dict(data["events_by_country"].get(country, {})),
            "diplomacy": dict(data["diplomacy"].get(country, {})),
            "economy": {k: v for k, v in data["economy"].get(country, {}).items()
                        if not k.startswith("_")},
            "inflation": (data["inflation"].get(country) or (None, None, None))[2],
        }
    return json.dumps(obj, indent=2, ensure_ascii=False)


def parse_date_arg(s):
    if not s:
        return None
    parts = s.replace("-", ".").split(".")
    y = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 1
    d = int(parts[2]) if len(parts) > 2 else 1
    return date_key(y, m, d)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Summarize a HOI4 / Millennium Dawn game.log")
    ap.add_argument("logfile", help="path to game.log")
    ap.add_argument("--country", action="append", metavar="NAME",
                    help="country to deep-dive; repeatable or comma-separated "
                         "(e.g. --country Korea,Germany,Iran)")
    ap.add_argument("--top-countries", type=int, default=0, metavar="N",
                    help="also deep-dive the N most active countries")
    ap.add_argument("--detail", action="store_true",
                    help="fuller per-country sections (all focuses, ideas, "
                         "event chains, diplomacy)")
    ap.add_argument("--top", type=int, default=15, help="rows in ranked tables (default 15)")
    ap.add_argument("--since", help="ignore entries before this game date (YYYY.MM.DD)")
    ap.add_argument("--until", help="ignore entries after this game date (YYYY.MM.DD)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    ap.add_argument("--no-deep-dive", action="store_true",
                    help="skip the per-country sections")
    args = ap.parse_args(argv)

    try:
        data = parse(args.logfile,
                     since=parse_date_arg(args.since),
                     until=parse_date_arg(args.until))
    except FileNotFoundError:
        sys.exit(f"error: file not found: {args.logfile}")

    if data["stats"]["parsed"] == 0:
        sys.exit("error: no scripted MD log entries found — is this a Millennium "
                 "Dawn game.log with debug logging enabled?")

    # Flatten comma-separated --country values into a single list.
    requested = []
    for item in (args.country or []):
        requested.extend(part.strip() for part in item.split(",") if part.strip())

    if args.no_deep_dive:
        countries = []
    else:
        countries = pick_countries(data, requested, args.top_countries)

    if args.json:
        print(to_json(data, countries=countries, top=args.top))
    else:
        print(report(data, countries=countries, top=args.top, detail=args.detail))


if __name__ == "__main__":
    main()
