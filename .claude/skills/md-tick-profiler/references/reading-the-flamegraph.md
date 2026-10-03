# Reading the tick profiler

Output of `tools/analysis/tick_audit.py`. Read this before explaining why a number looks
the way it does.

## Engine facts

Only six `on_action` hooks run on a clock:

- `on_daily`, `on_weekly`, `on_monthly` are global. They run once per country per
  period, and the engine staggers them across the period.
- `on_daily_<TAG>`, `on_weekly_<TAG>`, `on_monthly_<TAG>` run for that country only.

`on_monthly` is native. The tool finds hooks by parsing `common/on_actions/` and scopes
each as GLOBAL or the TAG whichever file it sits in. A global `on_weekly` inside
`99_LBA_on_actions.txt` is still GLOBAL.

## Ops

`ops` counts `key = ...` statements: effects and the `limit` and trigger checks the
engine evaluates each tick.

- A node's `ops` is the statements directly in its body.
- A node's `total` is its own ops plus everything it calls. Bar size uses `total`.
- It is a proxy, never time. Native `profile` measures time for a bounded workload.

## Tree against the flat report

The flamegraph is a call tree. A shared effect reached from three hooks is counted three
times, so its totals exceed the flat report's per-hook `work_units`, which count each
reached effect once. Use the tree for "where does the work go" and the flat
heaviest-countries table for "who pays the most per tick".

## Accuracy contract

Only work reachable from a real recurring hook is counted.

- An event is reported as firing on a cadence only when a hook fires it directly, through
  `country_event`, `news_event`, or `random_events` in the hook body.
- Events fired inside shared scripted effects count as ops, not fires. Those fires are
  usually gated by conditions such as `original_tag = HOL` that cannot be evaluated
  statically.
- `country_event = { id = X days = N }` is a one-shot delay. It is recurring only when
  the event reschedules itself in `immediate`. A self-fire in an `option` is labelled
  `player`.
- Decision timers are read only from `days_mission_timeout`, `days_remove`, and
  `days_re_enable` as direct children of the decision. A variable timer value is
  bucketed `variable`.

## Common questions

- "Every country's daily column is the same." Correct. Only a few countries have their
  own `on_daily_<TAG>`. Everyone else's daily cost is the shared global hooks.
- "Does event X really fire daily?" Flagged on a cadence means wired into that tick and
  still subject to its own `if` and `limit`. Open the `file:line` and read the guard.

## Report halves

- A, on_actions: the recurring hooks, the scripted effects they invoke, and the events
  they fire, directly or through weighted `random_events` pools.
- B, timers: timed decisions by timer field, and self-rescheduling event loops.

## Flags

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
