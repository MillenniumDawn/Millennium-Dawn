# File Encoding

- All `.txt` files (focus trees, events, decisions, ideas, etc.) must be saved as **UTF-8 without BOM**.
- Only `.yml` localisation files use UTF-8 **with** BOM.
- When creating or editing `.txt` files, never add a BOM byte sequence (`EF BB BF`).

# HOI4 Scripting — Quick Reference

For the full reference (variables, arrays, loops, collections, formatted loc), read `.claude/docs/hoi4-data-structures.md`.

## Scope Keywords

| Keyword      | Meaning                                                      |
| ------------ | ------------------------------------------------------------ |
| `THIS`       | Current scope (usually implicit)                             |
| `ROOT`       | Original scope at block start (event, focus, decision)       |
| `PREV`       | Previous scope before last scope change (`PREV.PREV` chains) |
| `FROM`       | Sender scope (in events: `FROM` = event sender)              |
| `OWNER`      | Owner of current state scope                                 |
| `CONTROLLER` | Controller of current state scope                            |
| `CAPITAL`    | Capital state of current country scope                       |

## Variables (basics)

- **Persistent:** `set_variable = { var = X value = Y }` — stored on scope, survives saves
- **Temporary:** `set_temp_variable = { var = X value = Y }` — current block only
- **Global:** `set_global_variable = { var = X value = Y }` — read via `global.X`
- **Arrays:** `my_array^0` (literal index), `my_array^i` (dynamic index)
- **Scoping:** `var:my_var = { ... }` or `var:my_array^i = { ... }` — never `var:v^i`

# Documentation References

For more comprehensive HOI4 scripting docs (effects, triggers, modifiers, wiki links), read `.claude/docs/documentation-references.md`.

