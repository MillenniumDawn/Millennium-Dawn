Run the Millennium Dawn validation tools and summarize the results.

Supported arguments: `staged` (only validate git-staged files), `strict` (fail on errors), or both.
Requested arguments: $ARGUMENTS

Steps:
1. Build the command flags from the arguments:
   - If "staged" is present, add `--staged`
   - If "strict" is present, add `--strict`
2. Run from the project root:
   ```
   ./tools/validation/run_all_validators.sh <flags>
   ```
3. Present results grouped by validator category (variables/flags, scripted localisation, decisions, events, etc.)
4. For each category with errors, show each error as: `file:line — description`
5. End with a summary line: total error count, or "All validators passed" if clean
