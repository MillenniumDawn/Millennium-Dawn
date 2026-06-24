> **Deprecated — merged into `/audit`.**

`/review-branch` no longer exists as a separate command. The branch-review orchestration (correctness, edge cases, performance, simplification, content) now lives in `/audit`.

Run `/audit` with no argument to review the whole branch diff vs `main`, or `/audit <file_path>` for a single file. Then follow the `/audit` workflow.
