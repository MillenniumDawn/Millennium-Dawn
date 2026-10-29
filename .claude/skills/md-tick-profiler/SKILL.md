---
name: md-tick-profiler
description: Profile MD's recurring per-tick scripted workload (the daily/weekly/monthly on_action hooks and everything they run) as a flamegraph sized by script ops, plus a text report. Use for any question about MD performance, lag, tick cost, on_actions, or why the game is slow, even without the word "profiler".
user-invocable: true
allowed-tools:
  - Bash
  - Read
---

# MD Tick Profiler

`tools/analysis/tick_audit.py` reconstructs, statically, what each recurring tick runs.
The game's own `profile` console command measures real time for a bounded workload.
They answer different questions. Use the static report to find what to measure, and
native timing to confirm a change matters.

## What an op is

Say this to the user. An op is one scripted statement: set a variable, check a
condition, fire an event, call an effect. A node's count is its own statements plus
everything it calls. More ops means more work per tick. It is a proxy for cost, not
measured milliseconds.

The output is a call tree, not a call graph. An effect called from three hooks is
counted under all three, so tree totals exceed the flat per-hook numbers. That is
expected.

## Flamegraph

Write to a temp path, then open the HTML (`xdg-open`, `open`, or `start ""`):

```bash
python tools/run.py tick_audit --flamegraph "$TMPDIR/md_ticks.html" --tree "$TMPDIR/md_ticks.json"
```

The tree runs root, cadence, on_action hook, scripted effects, then the events and
decisions those fire. Each node is sized by ops and links to its `file:line`.

Read the `--tree` JSON and tell the user the heaviest one or two hooks per cadence.
Each cadence's `children` are sorted heaviest first. Name the file and line.

The user can click a row to expand it, click a `file:line` to open it in VS Code, and
type in the filter box (a tag, a system, an event namespace) to collapse the tree to
matching nodes.

## Text report

For exact lists:

```bash
python tools/run.py tick_audit
python tools/run.py tick_audit --list hooks --cadence weekly
python tools/run.py tick_audit --list events --cadence monthly
python tools/run.py tick_audit --list decisions --limit 0
python tools/run.py tick_audit --tag USA
```

## Spot checks

```bash
python tools/run.py tick_audit --spot-check
python tools/run.py tick_audit --spot-check common/on_actions --fail-on high
python tools/run.py tick_audit --spot-check common/decisions --format json
```

Findings carry execution context: a daily global loop ranks above a monthly tagged
loop, focus completion is one-shot, and startup loops are suppressed.

## Accuracy

The analysis counts only work reachable from a real recurring hook. It does not treat
an event as recurring because it exists, and it does not attribute events fired inside
shared, tag-gated effects to every country. Those count as ops, not as fires. When the
user asks whether something really fires, say this and open the `file:line`.

Before explaining why a number looks the way it does, read
[references/reading-the-flamegraph.md](references/reading-the-flamegraph.md).

## Native spot tests

For a before and after measurement, use `profile` with the same save, game speed, map
position, open UI, and observation window. Repeat the sample before concluding.
