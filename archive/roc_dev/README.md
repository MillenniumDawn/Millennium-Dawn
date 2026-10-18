# RoC-development archive (AUG's Taiwan focus tree)

This folder preserves AUG's original RoC-development work exactly as it was imported, so nothing is lost while it is merged into the unified Operation Blue Tiger Taiwan tree.

## Provenance

|                          |                                                      |
| ------------------------ | ---------------------------------------------------- |
| Author                   | AUG                                                  |
| Branch                   | `upstream/RoC-development`                           |
| Commit archived          | `ceb1a0c1f5`                                         |
| Original import          | `cc578de16f7` "Taiwan Focus import" (23 August 2025) |
| Merge base with `main`   | `05d24e8044` (3 July 2026)                           |
| History after the import | merges from `main` only                              |

## Contents

- `roc_dev_original_ceb1a0c1f5.zip`: the ten files AUG's branch adds or changes compared with its merge base, byte-exact from `git show ceb1a0c1f5:<path>`, plus the full diff against the merge base (`roc_dev_vs_merge_base_05d24e8044.patch`).
- `checksums.txt`: SHA-256 of every file in the zip.
- `ROC_DEV_MAPPING.md`: where each of AUG's 92 focuses lives in the unified tree.
- `INTEGRATION_CHANGELOG.md`: exactly what was integrated, reworked, kept optional, fixed or held back, with the balance changes and the open questions.

The ten original files:

| File                                                         | What it holds                                                            |
| ------------------------------------------------------------ | ------------------------------------------------------------------------ |
| `common/national_focus/taiwan.txt`                           | The 92-focus tree (`taiwan_focus`)                                       |
| `localisation/english/MD_focus_TAI_l_english.yml`            | Focus, spirit, decision and event text                                   |
| `common/decisions/taiwan.txt`                                | Economic Policy, Army Mobilization and Project National Glory decisions  |
| `common/decisions/categories/99_TAI_decision_categories.txt` | Three decision categories                                                |
| `common/ideas/Chinese.txt`                                   | 29 national spirits                                                      |
| `events/Taiwan.txt`                                          | Events `taiwan.18` to `taiwan.28` and an edit to the 2000 election event |
| `common/opinion_modifiers/TAI_opinion_modifiers.txt`         | `tai_92`, `tai_ait`, `tai_resist`                                        |
| `common/game_rules/00_game_rules.txt`                        | `ROC_ai_behavior` rule                                                   |
| `history/countries/TAI - Taiwan.txt`                         | `TAI_921_earthquake` starting spirit                                     |
| `gfx/leaders/TAI/John_Chiang.dds`                            | Leader portrait                                                          |

## How the integration is built

The unified tree is generated, not hand-edited. In the Operation Blue Tiger tools (`tools/` in the backup repository):

- `roc/roc_spec.py` adds AUG's focuses to the OBT specification, folds the integrated rewards into OBT focuses and holds the 92-row mapping, which the build checks.
- `roc/build_roc.py` writes AUG's spirits, decisions, events, opinion modifiers, game rules and localisation into their own files.
- `roc/apply_roc.py` applies the result to a Millennium Dawn checkout with exact, idempotent edits and refuses to run if any target file has changed since the build.
- `roc/rebuild.sh` runs the whole build.

Nothing in this folder is loaded by the game.
