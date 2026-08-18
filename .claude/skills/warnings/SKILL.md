---
name: warnings
description: 'Print the complete, untruncated list of issues from a Millennium Dawn validator, optionally filtered to one category. Use when the user asks for all warnings/errors from a validator, e.g. "/warnings events unreferenced-triggered-only". Args: validator name, optional category, optional "errors"/"warnings"/"staged".'
disable-model-invocation: true
model: haiku
---

Print every issue a validator reports, with no truncation.

The validators' console output caps each category at 50 findings and then prints
`... and N more (full list in the JSON sidecar)`. This skill reads the sidecar instead, so
the list is always complete. `/validate` remains the command for a summarized suite run.

Requested arguments: $ARGUMENTS

Grammar (all optional, order-independent): `<validator> [category] [errors|warnings] [staged]`

## Step 1 — resolve the validator

Map the name to `tools/validation/validate_<name>.py`, converting `-` to `_`. Accept
`events`, `validate_events`, `validate_events.py`, and `focus-tree`/`focus_tree` alike.

Valid names:

```
agency-upgrades  ai-equipment  ai-navy  ai-roles  cosmetic-tags  decisions  defines
events  factions  file-paths  focus-tree  gfx-references  history  ideas  localisation
mios  mod-descriptors  modifiers  on-actions  oob-units  scripted-gui
scripted-localisation  scripted-params  set-variables  simplifications  style
unused-scripted  unused-textures  variables
```

If the arguments name no validator, call **AskUserQuestion** before running anything.
Offer: `events`, `focus-tree`, `decisions`, `ideas` as options, plus
"All validators (full dump)". The automatic "Other" choice covers the rest of the list.
Never guess a validator.

If the name is not in the list, print the list and stop. Run nothing.

## Step 2 — run the validator

One validator (append `--staged` when the `staged` token is present):

```bash
python tools/validation/validate_<name>.py --path . --no-color -o "<scratchpad>/warnings-<name>.txt"
```

The run writes `warnings-<name>.json` alongside the `.txt`. That sidecar is the input for
step 3 — it holds every finding, uncapped.

`gfx-references` skips its unused-sprite check unless `--report-unused` is passed. Append
that flag when the requested category is `unused-sprite`, `unused-sprite-case`,
`duplicate-sprite` or `case-variant-sprite`. For the latter three, also set
`MD_GFX_HIDE_UNUSED=1` so the ~8.6k orphan warnings stay out of the report.

All validators:

```bash
python tools/validation/run_all_validators.py --path . --no-color --format json -o "<scratchpad>/warnings-all.json"
```

Suite entries carry an extra `validator` field; single-validator entries do not.

These scans take minutes. Do not add a timeout below 600000.

## Step 3 — dump the sidecar

Pass the category and severity filters as arguments, empty string for "no filter". Severity
is `error` when the `errors` token is present, `warning` when `warnings` is present, empty
otherwise (both).

```bash
python - "<json path>" "<category or empty>" "<severity or empty>" <<'PY'
import json, sys
p, cat, sev = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.load(open(p, encoding="utf-8"))
issues = data["issues"] if isinstance(data, dict) else data
if cat: issues = [i for i in issues if i.get("category") == cat]
if sev: issues = [i for i in issues if i.get("severity") == sev]
print(f"TOTAL {len(issues)}")
for n, i in enumerate(issues, 1):
    loc = i.get("file", "")
    if loc and i.get("line"): loc += f":{i['line']}"
    tag = "E" if i.get("severity") == "error" else "W"
    print(f"{n}. [{tag}] " + (f"{loc} - " if loc else "") + i.get("message", ""))
PY
```

When no category was given, get the index with the same file:

```bash
python - "<json path>" <<'PY'
import collections, json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
issues = data["issues"] if isinstance(data, dict) else data
c = collections.Counter((i.get("category", "?"), i.get("severity", "?")) for i in issues)
agg = collections.defaultdict(lambda: [0, 0])
for (cat, sev), n in c.items(): agg[cat][0 if sev == "error" else 1] += n
for cat, (e, w) in sorted(agg.items(), key=lambda kv: -sum(kv[1])):
    print(f"{sum((e, w)):6d}  {e:5d}E {w:5d}W  {cat}")
PY
```

## Step 4 — present

Copy the command's stdout through verbatim inside one fenced block.

- Lead with the total and which validator/category it came from, and name the current branch.
- Category given → the flat numbered list, nothing else.
- No category → the index first, then the full list beneath it.
- **Never truncate, summarize, sample, re-order, or re-word a line, and never write
  "and N more".** Removing the 50-cap is the entire purpose of this skill. A long list stays
  long.

Then state these caveats:

- A warning is not automatically a bug. Reference-scanning categories such as
  `unreferenced-triggered-only` only grep `.txt` under `common/`, `events/`, and `history/`,
  so an event fired from a `.gui`, a scripted GUI, or an unresolved interpolated ID reads as
  unreferenced. Each entry needs a look before anything is deleted.
- Counts drift with the worktree, since the scans re-read the working tree on every run.
  Report the count from the run just performed; never reuse a number from earlier in the
  conversation.
- Say so explicitly when `--staged` was applied, so a short list is not mistaken for a clean
  repo.
