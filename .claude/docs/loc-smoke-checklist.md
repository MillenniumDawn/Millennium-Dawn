# Localisation Smoke Checklist

Python tests and CI prove that tokens, scopes, and formats in English strings match
what we expect. Only the game proves they render. Run this list by hand after a change
to dynamic localisation, and report the result apart from the Python and CI results.

The automated side lives in `tools/tests/content/localisation_contract_test.py` and
`tools/tests/validation/localisation_regression_fixtures_test.py`.

## What to record

Write one block per run in the PR or issue:

```text
Commit:        <git rev-parse --short HEAD>
Game version:  <bottom-left of the main menu, e.g. 1.17.x>
Playset:       Millennium Dawn (+ any test mod)
Date:          <YYYY-MM-DD>

| Row | Expected text | Observed text | Pass |
|-----|---------------|---------------|------|

error.log: <lines that name a key, "loc", "color", or "unknown", or "none">
```

`error.log` is in `Documents/Paradox Interactive/Hearts of Iron IV/logs/`. Delete it
before the run so it holds only this session. Attach a screenshot for every failed row.

## Setup

1. Start a 2000 game with the country named in the row.
2. Open the console (the key left of `1`). `focus.autocomplete` finishes focuses in a
   day, `tag <TAG>` switches the played country, and `event <id>` fires an event for
   the played country.
3. A console-fired event has no real FROM or PREV. Use it only for strings that read
   no other scope.

## Rows

| Row                          | Where to look                                                                        | Expected                                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| 1. Percentage points         | COM: hover the `Federalist Campaign` decision                                        | `Change the Federalist Constitution Support by 5%`. A number like `500%` fails.                    |
| 2. Points on another country | COM: hover `[French] Support Campaign`                                               | Both values end in a plain `%` (for example `4%`, `15%`).                                          |
| 3. Money, not an icon        | Any war you win: open the conditional peace deal and hover a reparations deal        | `Projected transfer for this deal: $1.25B per week`. A missing amount or a broken icon fails.      |
| 4. Getters with a flag       | PER: open the decisions tab, find `Industrial Aid To` Iraq, Syria, and the Houthis   | Flag followed by the full country name. A raw `[IRQ.GetName]` fails.                               |
| 5. Prose section sign        | Any country: `event USA_econ_event.22`                                               | The citation ends `(15 U.S.C. § 1).` with the `§` visible and no color change.                     |
| 6. Sender side               | EGY: `focus.autocomplete`, complete `EGY_negot_iraq`, then `tag IRQ` within two days | IRQ receives `Egypt Demands Submission`. Pick either option.                                       |
| 7. Recipient side            | Right after row 6: `tag EGY`                                                         | EGY receives `Iraq Submits` or `Iraq Resists`. `Egypt Submits` means FROM did not flip and fails.  |
| 8. Fallen ace                | Long test game with air wars: wait for one of your aces to die in a duel             | Title `<your ace> Shot Down By <enemy callsign>`; the winner's pronoun and wing are the enemy's.   |
| 9. Winning ace               | Same game: one of your aces kills an enemy ace                                       | Title `<your ace> Shot Down <enemy callsign>`; `on <pronoun> conscience` refers to the dead enemy. |

Rows 8 and 9 need a real ace duel. Mark them `not reached` rather than firing the
event from the console.
