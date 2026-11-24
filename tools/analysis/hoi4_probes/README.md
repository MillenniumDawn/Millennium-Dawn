# HOI4 headless-run probes

Run `headless_run.py probe add TAG` to log one country's numbers or per-state
infrastructure room from a headless run. Each probe is a bare effect body for country
scope (ROOT = THIS = the country) that writes `PROBE_` lines to game.log.

## What each probe logs

- `country_stats.txt` writes one `PROBE_STATS` line per run:
  `tag`, `civ`, `mil`, `dock` (factory counts), `gdp`, `treasury`, `debt`,
  `debt_ratio`, `stability`, `pp`, and `research_slots`. War support is left out
  because it reads 0 when copied into a variable.
- `state_infrastructure.txt` writes one `PROBE_INFRA` line per owned state:
  `state` (name), `id`, `infra` (building level), `free` (1 when a free infrastructure
  slot exists, queued levels counted), and `can_take` (1 when
  `investment_infrastructure_slots_available` passes for one level). `free=1` with
  `can_take=0` marks a state that has room above its controller's railway tech cap.

## Use with headless_run.py

```
python tools/analysis/headless_run.py probe add BRA --every year --kind stats infrastructure
python tools/analysis/headless_run.py probe remove
```

`probe add` writes the gitignored `common/on_actions/zz_md_run_probe.txt`, which holds
the chosen probes under `on_monthly_BRA`. `--kind` takes `stats`, `infrastructure`, or
both (default `stats`). `--every month` is the default. `--every year` counts months in
the country variable `probe_months` and logs once it passes 11, then resets it. Put the
tag first: `--kind` takes several values and would swallow a tag after it.

## Use with another runner

Any runner that wraps a log-effect file as `on_monthly_<TAG> = { effect = { ... } }`
can take a probe file as is. With hlab:

```
hlab hoi4 run --log-effect tools/analysis/hoi4_probes/country_stats.txt --log-every year
```

## Read the lines

Each line starts with its marker and the in-game date, so grep by marker:

```
rg PROBE_STATS game.log
rg PROBE_INFRA game.log
```

## Pair with content_coverage.py

`python tools/analysis/content_coverage.py --tag BRA --log game.log` lists which of the
tag's focuses, decisions, and events fired. The `PROBE_STATS` lines from the same
game.log show what the country's economy did around them.

## Adding a probe

Add a `.txt` body with a fixed `PROBE_` marker in its `log` line, then add it to
`PROBE_KINDS` in `headless_run.py`. Prefix temp variables with `probe_`: a bare
three-letter name such as `[?fao]` resolves to a country tag.
