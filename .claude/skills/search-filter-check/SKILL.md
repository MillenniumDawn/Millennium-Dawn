Validate `search_filters` on every focus in a file against the approved filter list and two-layer convention.

**Syntax:** `/search-filter-check [file_path]`

- With `file_path`: check that focus tree file.
- Without argument: check all focus tree files changed on the current branch.

Authoritative filter reference: `.claude/docs/search-filters.md`. Read it before starting.

## Execution

### 1. Gather scope

**File mode:** Read the file directly.

**Branch mode:** Run `git diff origin/main...HEAD --name-only`, filter for `common/national_focus/*.txt`, check each.

### 2. Extract all focuses

For each `focus = { ... }` block, extract:

- `id` — the focus ID
- `search_filters = { ... }` — the filter values (may be absent)

### 3. Apply validation rules

**Rule 1 — Filter present:** Every focus must have at least one `search_filters` value. Flag any focus with no `search_filters` line.

**Rule 2 — Valid filter names:** Each filter must be a known filter from `.claude/docs/search-filters.md`. Flag any not in the generic list, the Israel-specific list, or the other-country custom filter list.

**Rule 3 — Legacy alias:** `FOCUS_FILTER_MILITARY` is legacy/unused. Correct filter is `FOCUS_FILTER_MILITARY_LAWS`. Flag any use of the old name.

**Rule 4 — Two-layer convention:** For trees using country-specific custom filters (ISR, Russia, Ukraine, Armenia, Brazil, Iran, Korea, etc.), each focus with a custom filter must also have the correct paired generic filter (see pairing tables in `.claude/docs/search-filters.md`).

- Israel (`FOCUS_FILTER_ISRPOLIT`, `FOCUS_FILTER_ISRMILITARY`, etc.): check the ISRMILITARY and ISRECON subcategory mapping tables to verify the correct generic is paired.
- Other countries: verify a generic filter is present alongside the custom filter.

**Rule 5 — Cross-assignment:** Country-specific custom filters must not appear in another country's file. E.g., `FOCUS_FILTER_ISRPOLIT` must not appear in a non-Israel file. Use the country prefix to detect this.

**Rule 6 — Expenditure + bankruptcy guard:** Any focus with `FOCUS_FILTER_EXPENDITURE` should have a `factor = 0` modifier in `ai_will_do` conditioned on `has_active_mission = bankruptcy_incoming_collapse`. AI-only — the guard must be in `ai_will_do`, not `available` (which would block the player). Flag expenditure-filter focuses with no such modifier in `ai_will_do`.

### 4. Output

Report issues in a table:

| Focus ID        | Issue               | Current Filters          | Recommendation                                             |
| --------------- | ------------------- | ------------------------ | ---------------------------------------------------------- |
| TAG_some_focus  | Missing filter      | (none)                   | Add appropriate filter                                     |
| TAG_other_focus | Legacy alias        | FOCUS_FILTER_MILITARY    | Use FOCUS_FILTER_MILITARY_LAWS                             |
| TAG_big_focus   | Missing generic     | FOCUS_FILTER_ISRPOLIT    | Add FOCUS_FILTER_POLITICAL                                 |
| TAG_expensive   | No bankruptcy guard | FOCUS_FILTER_EXPENDITURE | Add factor = 0 / has_active_mission modifier in ai_will_do |

End with a count: `N issues found across M focuses` or `All N focuses pass filter validation`.

### 5. Fix (if user confirms)

Apply in place using Edit:

- Add missing generic filters to the `search_filters` line
- Replace `FOCUS_FILTER_MILITARY` with `FOCUS_FILTER_MILITARY_LAWS`
- Add `modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse }` to the `ai_will_do` block of expenditure-tagged focuses
- Do not invent country-specific custom filters — flag those as needing human judgment
