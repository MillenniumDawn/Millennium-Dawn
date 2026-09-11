---
name: md-tick-profiler
description: Visualize and explain MD's recurring per-tick scripted workload (the daily/weekly/monthly on_action hooks and everything they run) as an interactive flamegraph sized by script ops with file:line links, plus a text report and bounded static spot checks. Use for any question about MD performance, lag, tick cost, on_actions, "what runs each day/week/month", why the game is slow, or profiling the mod — even without the word "profiler".
user-invocable: true
allowed-tools:
  - Bash
  - Read
---

# MD Tick Profiler

The base-game `profile` console command is usable for bounded in-game spot tests
and provides measured timing. This skill also gives a drill-down call tree of
what each recurring tick runs and what's causing the load, reconstructed
**statically** from the scripts by `tools/analysis/tick_audit.py`. Native
profiling and static analysis answer different questions and neither replaces
the other.

Three complementary surfaces:

- **Flamegraph** (`--flamegraph`): a self-contained interactive HTML call tree.
  Root → cadence (daily/weekly/monthly) → on_action hook → the
  `scripted_effects` it calls → the events/decisions those fire. Every node is
  sized by **ops** and every node links to its `file:line` in VS Code.
- **Text report** (`--list`): precise, greppable itemization for when the user
  wants exact lists rather than a picture.
- **Static spot checks** (`--spot-check`): context-aware findings for known hot
  patterns, with deterministic JSON and optional severity gating.

## What "ops" means (say this to the user; it's the crux)

HOI4 runs scripts on a clock. Every in-game day/week/month it executes a to-do
list of scripted instructions **for every country**. An **op** is one such
instruction — a `key = ...` statement: set a variable, check a condition
(`limit`/trigger), fire an event, call an effect. A node's op count is its own
statements plus everything it transitively calls. **More ops = more work per
tick = more lag.** It is a _proxy for cost, not measured milliseconds_. Native
`profile` gives measured timing for bounded workloads. Always frame it this way
so the user isn't misled into reading ops as time.

It is a **call tree**, not a call graph: a shared effect called from three
hooks is counted under all three (exactly how a profiler attributes cost), so
the tree totals are larger than the flat per-hook numbers in the text report —
that's expected, not a bug.

## Workflow

### Native measured spot tests

Use native `profile` for short before/after measurements of a specific workload.
Keep the save, game speed, map position, open UI, and observation window the
same. Repeat the sample before drawing conclusions. Use the static report to
identify source locations worth measuring, then use native timing to verify
whether a change matters in game.

### 1. Generate the flamegraph

Run from the mod root. Write to a temp path so you don't clutter the repo, then
open it in the user's browser.

```bash
# from the Millennium_Dawn mod root
python tools/run.py tick_audit --flamegraph "$TMPDIR/md_ticks.html" --tree "$TMPDIR/md_ticks.json"
```

On Windows the temp dir is `%TEMP%` (in the Bash tool, `"$TEMP"` or
`/tmp`-style paths under it). A reliable cross-platform choice: write to the
system temp directory. Then open it:

- Windows: `start "" "<path>"`
- macOS: `open "<path>"`
- Linux: `xdg-open "<path>"`

If the user is working in VS Code, mention they can also right-click the HTML →
"Open with Live Server" or just open the file — and that the `file:line` links
in the page open straight into their editor.

The command prints the total op count. The `--tree` JSON is optional but handy:
read it to pull the headline findings (below) without screenshotting.

### 2. Point the user at the top of each tick

After generating, **read the `--tree` JSON** and tell the user, per cadence, the
one or two heaviest hooks — that's where any optimization pays off. For each
cadence the tree's `children` are already sorted heaviest-first, so:

```text
daily   → children[0]   (name, total ops, file)
weekly  → children[0]
monthly → children[0]
```

Report them plainly, e.g. "Your daily tick is dominated by `on_daily` in
`MD_antarctica_on_actions.txt:426` at N ops — open it and expand to see the
antarctica station-processing effects underneath." Name the file and let them
click in.

### 3. Let them explore

Tell the user the three interactions:

- **Click any row** to open what it calls (lazy, so it stays fast).
- **Click a `file:line`** to jump to that exact spot in VS Code.
- **Type in the filter box** (e.g. a country tag `PER`, a system `money`, an
  event namespace `econvent`) to collapse the tree to just matching nodes with
  the path expanded — great for "show me everything the economy does each
  month" or "what does Persia run".

## Static spot checks

Run the broad defaults or name a file or directory:

```bash
python tools/run.py tick_audit --spot-check
python tools/run.py tick_audit --spot-check common/on_actions --fail-on high
python tools/run.py tick_audit --spot-check common/decisions --format json
```

The static rules carry execution context into findings. Daily global loops rank
higher than monthly tagged loops, focus completion stays one-shot, and startup
loops are suppressed. The report also records conservative assumptions learned
from prior reviews, including cheap `can_staff_*` triggers and the distinction
between fixed-tag scope opens and unbounded loops.

## When the user wants exact lists, not a picture

Use the text report instead of (or alongside) the flamegraph. It shares the
same accuracy guarantees.

```bash
# Daily, weekly, monthly summary plus heaviest countries
python tools/run.py tick_audit
python tools/run.py tick_audit --list hooks --cadence weekly
python tools/run.py tick_audit --list events --cadence monthly
python tools/run.py tick_audit --list decisions --limit 0
python tools/run.py tick_audit --tag USA                # everything USA runs
```

Full detail on the report, the accuracy contract, and every flag lives in
[references/reading-the-flamegraph.md](references/reading-the-flamegraph.md) —
read it before answering questions about _why_ a number looks the way it does
(e.g. "why is every country's daily column the same", "does this event really
fire", global-vs-per-country hooks, staggering).

## Accuracy — the promise to keep

The analysis only counts what genuinely runs on a cadence: work reachable from a
real recurring hook. It never treats an event as "fires weekly" just because it
exists in `events/`, and it does **not** attribute events fired deep inside
shared, tag-gated `scripted_effects`. For example,
`if = { limit = { original_tag = HOL } ... }` is not attributed to every
country. Those effects are counted as work (ops) but not as fires,
because their firing can't be proven statically. If the user asks whether
something "really fires", explain this and open the `file:line` so they can read
the guard themselves. Never oversell ops as measured time. Use native `profile`
for bounded measured spot tests and this static audit for broad source and
reachability coverage.
