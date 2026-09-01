# Reading the tick profiler — interpretation & FAQ

Everything here is produced by `tools/analysis/tick_audit.py` (tests in
`tools/tests/tick_audit_test.py`). Read this before explaining *why* a number
looks the way it does.

## Table of contents

1. The engine facts the whole thing rests on
2. What "ops" is and isn't
3. Call tree vs the flat report (why totals differ)
4. The accuracy contract
5. Common "that looks wrong" questions
6. The two parts of the text report (A: on_actions, B: timers)
7. Every flag

## 1. Engine facts

HOI4 natively fires six recurring `on_action` hooks, and only these run on a
clock:

- `on_daily`, `on_weekly`, `on_monthly` — **global**: they run once **per
  country, per period**, and the engine **staggers** them across the period
  (not every country on the same day) to spread load.
- `on_daily_<TAG>`, `on_weekly_<TAG>`, `on_monthly_<TAG>` — run only for that
  one country.

`on_monthly` *is* native (vanilla uses it too) — it is not a custom MD bridge.
Everything that "runs every day/week/month" hangs off one of these six; the tool
finds them by parsing `common/on_actions/` and treats a hook's `scope` as
GLOBAL or the TAG, regardless of which file it's written in (a global
`on_weekly` can live inside `99_LBA_on_actions.txt`, and the tool still reports
it as GLOBAL — file location ≠ scope).

## 2. What "ops" is and isn't

`ops` = count of `key = ...` statements. That deliberately includes both
effects (`set_variable`, `add_to_variable`, `country_event`, ...) **and** the
`limit`/trigger checks the engine evaluates every tick. The user literally asked
about "checks", and checks cost CPU, so counting them is correct.

- A node's `ops` (its "self") = statements directly in its body.
- A node's `total` = self + the total of everything it calls (bar size uses
  `total`).
- It is a **proxy**, not milliseconds. Native `profile` is usable for bounded
  in-game spot tests and measures real timing. Use the static audit for broad
  source and reachability coverage. Never present ops as time.

## 3. Call tree vs the flat report

The **flamegraph** is a call *tree*: a shared effect reached from three hooks is
counted three times (once per path) — this is how a profiler attributes cost and
why flamegraph totals (e.g. ~90k) exceed the flat report's per-hook `work_units`
(which counts each reached effect once). Both are valid; they answer slightly
different questions. Use the tree for "where does the time go", the flat
`work_units`/heaviest-countries table for "who pays the most per tick".

## 4. The accuracy contract

Only work **reachable from a real recurring hook** is counted. Specifically:

- An event is reported as firing on a cadence **only** if a hook fires it
  textually (via `country_event`/`news_event`/`random_events` in the hook body).
- Events fired deep inside shared `scripted_effects` are counted as **ops
  (work)** but **not** attributed as fires, because those fires are usually
  gated by in-effect conditions like `if = { limit = { original_tag = HOL } }`
  that can't be evaluated statically. Attributing Holland's events to every
  country that calls the shared effect would be the classic false positive; the
  tool refuses to do it.
- `country_event = { id = X days = N }` is a one-shot **delay**, not recurrence.
  It only counts as recurring if the event reschedules **itself** in its
  `immediate` block (an automatic loop). A self-fire in an `option` is
  player-driven and is labelled `player`, not bucketed onto a cadence.
- Decision timers are read only from the real fields `days_mission_timeout` /
  `days_remove` / `days_re_enable` as **direct children** of the decision — a
  `days = N` nested inside `set_country_flag = { ... }` is never mistaken for a
  decision timer. Timer values that are variables (e.g. `ROOT.battery_park_time`)
  are bucketed `variable`, not guessed at.

## 5. Common "that looks wrong" questions

**"Every country's daily column is the same (~3934)."** Correct, not a bug. Only
8 of ~150 countries have their own `on_daily_<TAG>`; everyone else's daily cost
is purely the shared global daily hooks, so it's identical for them. The 8 that
differ show up above the floor (ITA, CZE add the most).

**"A hook shows 0 ops but I know it does something."** Older versions counted
only named `scripted_effect` calls, so a hook that just fires events or does
inline work read as 0. The current `ops` metric counts inline statements + event
fires too, so those hooks now register (e.g. `on_daily_GER` fires 2 events → ~25
ops, not 0).

**"Does event X really fire daily?"** "Flagged on a cadence" means *wired into
that tick*, still subject to its own `if`/`limit`. It means "can fire on this
beat", not "fires every time". Open the `def file:line` and read the guard.

## 6. The two report halves

- **A — on_actions**: the recurring hooks, the `scripted_effects` they invoke
  (transitively, as ops), and the events they fire (direct vs weighted
  `random_events` pools).
- **B — timers**: timed decisions bucketed by real timer field, and
  self-rescheduling event loops (`immediate` = automatic tick, `option` =
  player-driven).

## 7. Flags

```text
python tools/run.py tick_audit                     # summary + heaviest countries
  --cadence daily|weekly|monthly                   # restrict to one beat
  --top N                                           # size of heaviest-country table
  --list hooks|events|decisions|loops|all          # itemize, each with file:line
  --tag TAG                                         # country + globals
  --limit N                                         # 0 = unlimited
  --json PATH                                       # full report as JSON
  --flamegraph PATH                                 # interactive HTML call tree
  --tree PATH                                       # raw call tree as JSON
  --spot-check [PATH ...]                           # static hotspot findings
  --format text|json                                # spot-check stdout format
  --fail-on critical|high|medium|low|none           # optional spot-check gate
  --no-color
```

Static findings for bounded source checks:

```bash
python tools/run.py tick_audit --spot-check
python tools/run.py tick_audit --spot-check common/on_actions \
  --format json --fail-on high
```

Spot checks report context-aware source patterns. They complement native
`profile` measurements and do not replace them. Keep the same save, game speed,
map position, open UI, and sample window when comparing native measurements.
