# Archived branches

Snapshot of diverging files from stale upstream branches that we are no longer
maintaining. Each subdirectory is a one-to-one copy of the files that the
branch changed relative to `main`, preserving the original repo path layout
under the branch name.

The source branch tip is recorded in each subdirectory's `<branch>.json`
metadata. The branch refs themselves are deleted; the data lives here so the
work isn't lost if anyone needs to revive or rebase it later.

The `tools/archive_stale_branches.py` script regenerates this tree from the
original branch refs if they still exist locally (`origin/<name>`).

## Layout

- `<branch>/<repo-path>`: file as it appeared on the branch
- `<branch>/<branch>.json`: branch metadata (tip commit, last author,
  last-commit date, diverging file count)

## Branches archived

| Branch                     | Last activity | Diverging files |
|----------------------------|---------------|------------------|
| yemen-development          | 2024-11-20    | 171              |
| Taiwan-dev                 | 2025-09-22    | 3                |
| ASEAN_shared_tree          | 2025-05-22    | 87 (583 nominal) |
| religion-breakdown-chart   | 2025-03-07    | 6                |
| panama-focuses             | 2025-10-13    | 75               |
| danubia                    | 2025-02-17    | 27               |
| iraqi-gui                  | 2025-10-06    | 20               |
| military-strength          | 2025-11-06    | 1                |
| 3D-tank-models-to-check    | 2025-12-13    | 113              |
| md-railway-guns            | 2025-10-09    | 8                |
| didi                       | 2025-11-28    | 146              |
| Irish-Development          | 2025-12-23    | 107              |

ASEAN_shared_tree shows 583 in the 3-dot diff but 496 of those files are
byte-identical to main; only 87 actually differ. The script's identical-skip
filter handles this. didi has 2 files identical to main for the same reason.

yemen-development's `MD_focus_​HOU_l_english.yml` has a zero-width space in
its filename, which `git diff --name-only` quotes and our normal path loop
drops. It is recovered out-of-band via the script's post-step.
