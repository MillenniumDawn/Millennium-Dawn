---
name: search-filter-check
description: "Validate search_filters on every focus in a file (or all focus files changed on the branch) against the approved filter list and the two-layer custom+generic convention. Use when asked to check or fix search filters on a focus tree."
---

**Syntax:** `/search-filter-check [file_path]`. Without a path, check every
`common/national_focus/*.txt` file in `git diff origin/main...HEAD --name-only`.

Read `.claude/docs/search-filters.md` first. It is the filter list and the pairing
reference.

## Checks

For each `focus = { ... }` block, take its `id` and `search_filters`, then flag:

1. No `search_filters` line.
2. A filter that is not in the generic list, the Israel list, or the other-country
   list.
3. `FOCUS_FILTER_MILITARY`. The filter is `FOCUS_FILTER_MILITARY_LAWS`.
4. A custom filter with no generic alongside it. For Israel, check the generic against
   the `ISRMILITARY` and `ISRECON` mappings.
5. A country's custom filter in another country's file.
6. `FOCUS_FILTER_EXPENDITURE` with no bankruptcy guard in `ai_will_do`. The guard must
   not be in `available`.

## Output

| Focus ID      | Issue               | Current filters          | Recommendation                 |
| ------------- | ------------------- | ------------------------ | ------------------------------ |
| TAG_focus_b   | Legacy alias        | FOCUS_FILTER_MILITARY    | Use FOCUS_FILTER_MILITARY_LAWS |
| TAG_focus_c   | Missing generic     | FOCUS_FILTER_ISRPOLIT    | Add FOCUS_FILTER_POLITICAL     |
| TAG_expensive | No bankruptcy guard | FOCUS_FILTER_EXPENDITURE | Add the ai_will_do guard       |

End with `N issues found across M focuses` or `All N focuses pass filter validation`.

## Fix when asked

Add missing generic filters, replace the legacy alias, and add the bankruptcy guard. Do
not invent a custom filter. Flag those for human judgment.
