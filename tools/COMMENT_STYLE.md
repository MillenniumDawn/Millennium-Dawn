# Comment Style — Python tooling

These rules apply to every Python script under `tools/` (validators, linters,
standardizers, helpers). The HOI4 scripting equivalent lives in
`.claude/rules/general-rules.md` under the **Comments** section; this file is
its Python counterpart.

## The rule

**Default to writing no comments.** Only add one when the **why** is
non-obvious. The code already says what it does — comments should say why
that choice was made when the choice itself is the surprising part.

A comment earns its place if removing it would force the next reader to
re-derive a hidden constraint, dig through commit history, or grep for the
callers to understand the trade-off you made.

When in doubt: delete the comment, rename the function, or extract a helper.
Self-documenting code beats documented code.

## Add a comment when

- A hidden constraint isn't visible from the surrounding code
  (e.g., "must run before the pool is closed", "key length capped by the
  filesystem, not the algorithm").
- A subtle invariant must hold for the next edit to be safe
  (e.g., "callers rely on insertion order — don't switch to a set").
- A deliberate workaround for a specific bug or library quirk
  (e.g., "Python re alternation slows down beyond ~3000 alternatives").
- Behaviour that would genuinely surprise a competent reader
  (e.g., "atomic via os.replace; tmp suffix includes pid to avoid worker collisions").

## Never write a comment that

- **Restates the code in prose.**
  ```python
  # Wrong — restates the assignment
  x = 0  # initialize x to zero
  count: int = 0  # this is an integer
  ```
- **Explains what a well-named function does.** If you need a sentence to
  describe `validate_unused_decisions()`, the name or signature should be
  doing that work.
- **Narrates the change or references a ticket.**
  ```python
  # Wrong — belongs in the commit message
  # Added for the false-positive fix in #1234
  # Refactored to use multiprocessing
  ```
- **Points at callers or downstream consumers.**
  ```python
  # Wrong — rots as the codebase evolves
  # Used by validate_variables and validate_decisions
  # Called from main() during startup
  ```
- **Decorates obvious blocks with section headers.**
  ```python
  # Wrong — visual noise, no information
  # ---- Setup ----
  config = load_config()
  # ---- Main loop ----
  for item in items: ...
  ```

## Docstrings

- **One-line** for most functions. The signature plus a clear name usually
  carries the meaning.
- **Multi-line** only when the function has non-obvious **why** — invariants
  on the arguments, a trade-off the reader has to know, or a cross-reference
  to a paired function.
- Don't write "Returns a dict of X" — type hints already say that.
- Don't write a multi-paragraph essay. If the function needs a long
  explanation, it probably needs to be split.

## Examples from this repo

```python
# Good — flags a non-obvious invariant
# Pool workers must be defined at module level (multiprocessing pickles them).
def process_file_for_flags(args): ...

# Good — points at a hidden constraint
# Cache key includes tracked_vars hash so the alternation regex's output is
# only reused when the input set is unchanged.
def count_all_variables_in_file(args): ...

# Bad — restates the code
# Build the args list
args_list = [(f, lowercase) for f in files]

# Bad — narrates history
# Switched from glob.glob to glob.iglob for memory efficiency
for filename in glob.iglob(...): ...

# Bad — empty docstring noise
def get_workers():
    """Get the number of workers."""
    return self.workers
```

## When code needs explanation, prefer code

```python
# Bad
# Check if the cache entry is older than the source file
if cache_mtime < source_mtime: ...

# Good — extract and name
def cache_is_stale(cache_mtime: int, source_mtime: int) -> bool:
    return cache_mtime < source_mtime

if cache_is_stale(cache_mtime, source_mtime): ...
```

```python
# Bad — comment to explain magic
# 25 chars covers the 'set_variable = {' prefix plus a short variable name
ctx = text[max(0, m.start() - 25):m.end() + 25]

# Good — named constant
SET_CONTEXT_WINDOW = 25
ctx = text[max(0, m.start() - SET_CONTEXT_WINDOW):m.end() + SET_CONTEXT_WINDOW]
```
