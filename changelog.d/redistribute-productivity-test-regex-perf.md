### Performance

- Pre-compiled regular expression `productivity_state_var = (\d+)` at top-level scope in `tools/tests/analysis/redistribute_productivity_test.py` to eliminate redundant regex compilation inside state file iteration loops.
