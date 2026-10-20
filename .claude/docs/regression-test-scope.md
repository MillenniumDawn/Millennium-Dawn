# Economic regression test scope

This branch implements the three main-compatible candidates from the fifteen-test
audit. It changes tests and test support only. No open feature branch is imported.

Main was rechecked on October 18, 2026 at
`532b046fd6fb8c19089a52b4a53b2578816a704d`. The audit searched all 227 Python test
files and the 18 empty native scenario files. Existing generic building guards,
decision cost checks, startup reserve defaults and helper parameter contracts do
not exercise the new economic contracts.

## Implemented contracts

| Audit candidate                  | Coverage                                                                                                | Behavioral authority                                                                                                                                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Debt partition                | `bankruptcy_contract_test.py::test_default_partitions_debt_without_spending_treasury`                   | [#5873](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5873), `docs/src/content/tutorials/economy-guide.md:1230`: 10% regular debt, 50% deferred, 40% forgiven                                     |
| 2. Default and settlement policy | Three parametrized tests in `bankruptcy_contract_test.py`                                               | Same guide and PR: wartime AI default, player cash gate, wartime IMF veto, positive influencer AI weights; the final $50B and 80% GDP boundaries are AI weights, not player availability                   |
| 3. ROI conservation              | `international_roi_contract_test.py::test_roi_rate_splits_one_weekly_return_without_changing_principal` | [#5879](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5879), `docs/src/content/tutorials/investments-guide.md:81`: 3% annual base, modifiers and cap; collected plus reinvested equals one return |

The ROI tests preserve the existing approximate `0.019` annual-to-weekly convention.
They do not assert an exact `1/52` conversion or native weekly payout timing.
Debt fixtures use integral settlement amounts and a wartime country with no cartel.
Depression, mission activation and timed-idea requests are recorded native boundaries;
their engine behavior is not simulated. Fiscal distress is an explicit owner input,
not a reproduction of the full economic crisis system.

`EconomicScriptFixture` in `tools/shared/suite.py` reuses the existing script parser.
It executes only the numeric assignments, expressions, conditional branches and
weights needed by these contracts. Missing inputs and unsupported statements fail.
Its own tests exercise mutation-sensitive branch ordering and rejection behavior.
It does not implement country scopes, arrays, native scheduling, construction,
equipment delivery, timed modifiers or campaign performance.

## Deferred dependencies

All listed PRs were still open at the recheck. These are dependencies, not skipped
or expected-failing tests. Recheck source and coverage again when each lands.

| Audit candidate                    | PR and rechecked head                                                                                                   | Reason deferred                                                                                                                                                                            |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 4. Domestic sales budget           | [#5672](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5672), `08e04d7aa75344f7ff467c465140e72f3300832c`        | Main lacks the corrected shared sales receipt path                                                                                                                                         |
| 5. Independent export reservations | #5672, same head                                                                                                        | Frozen per-buyer generations and quote settlement are unmerged                                                                                                                             |
| 6. Bosnia/Montenegro destination   | [#5884](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5884), `c7b144915d97158e63ab84f334643604b6d40fdf`        | Shared EUevent.23 and direct investment helper are unmerged; source scope fixtures would not prove native ROOT/FROM behavior                                                               |
| 7. Iranian assistance progression  | [#5859](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5859), `69941aa0f55cdeecfe8faf99977d24856fc12d64`, draft | Project-aware assistance branches are unmerged                                                                                                                                             |
| 8. Bomber repair family lock       | [#5834](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5834), `bcb8a7a1306ba9ef0bb5cb48cc736e07d1a353bc`, draft | Repair chain is unmerged. `UKR_tu95_repair_2` sets the Tu-160 flag at `common/decisions/Ukraine.txt:15596`; availability/removal use Tu-95. No gameplay repair or failing test is included |
| 9. Reactor-material conservation   | [#5404](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5404), `c525dc43324f67a57fdc0b53d1a1a843d5c853a6`        | Revised acceptance guard and AI Race test fixtures are unmerged                                                                                                                            |
| 10. Facility query ROOT rebinding  | #5404, same head                                                                                                        | Needs unmerged hidden event plus native HOI4 execution; Python fixtures rebind ROOT themselves                                                                                             |
| 11. Iranian fleet placement        | [#5883](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5883), `7a8562eea6228c574fda210966a2933f94dc36d0`        | Needs unmerged OOBs plus native placement/count assertions                                                                                                                                 |
| 12. FIS government transition      | [#5882](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5882), `def61fb0c3b2b857509d2473790fbc9d04d9073a`        | Needs unmerged government/leadership changes plus native election transitions                                                                                                              |
| 13. Skif export economics          | [#5867](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5867), `a25000713df9c7105d59b6a854257ad96ee1adb9`, ready | Rechecked the moved head and events .10-.12; these exports are absent on main. No stale `7b63af1` dependency is used                                                                       |
| 14. Weekly factory work budget     | #5672, same head                                                                                                        | Weekly factory-calculation move is unmerged; future source call counts would not establish CPU improvement                                                                                 |
| 15. Discovery traversal budget     | #5404, same head                                                                                                        | AI Race dispatch is absent on main; future operation counts would not establish native frame-time gains                                                                                    |

Native candidates 10-12 also need a working runner. The scenario directory currently
contains only empty placeholders. No game launch, native test or performance claim
is made by this branch. Already-covered tooling regressions in #5851, #5856, #5858
and #5860 were not duplicated.

## Local verification

- Focused content and fixture checks: 64 passed, including 34 new content cases and
  15 new fixture cases. Mutation probes rejected the previous debt retention and
  ROI rates, inverted sale eligibility, a weakened GDP floor and malformed source.
- Aggregate suite, also rerun with branch coverage: 7,979 passed, 2 skipped,
  2 failed. Both failures are `publish_workshop_test.py` process-group cases
  (`wrapper_exits_first`, `child_ignores_term`), reproduced from an unchanged
  archive of the main commit above. No tests were skipped or weakened to hide them.
- The repository coverage gate passed at 95%. Ruff, Black, Pylint, mypy, jscpd,
  whitespace checks and pinned Prettier passed. Independent Sol review's parser
  consumption finding was corrected and the final re-review had no findings.
- Normal pre-commit bootstrap could not install its Prettier Git package because
  npm rejected it with `EALLOWGIT`. All remaining hooks passed using an external
  temporary configuration, and Prettier 3.8.3 passed directly. The repository hook
  configuration is unchanged.
