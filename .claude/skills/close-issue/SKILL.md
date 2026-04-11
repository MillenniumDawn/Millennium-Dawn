Close a GitHub issue with a brief comment summarizing the fix that was applied.

Supported arguments: an issue number (required), and optionally a short description of the fix. If no description is provided, infer the fix from the current branch's diff against main.

Requested arguments: $ARGUMENTS

Steps:

1. **Parse arguments**

   Extract the issue number from `$ARGUMENTS`. If a description is also provided, use it as the comment body. Otherwise, proceed to step 2 to infer one.

2. **Infer the fix summary** (skip if a description was provided)

   Fetch the issue title for context, then look at the current branch diff:

   ```
   gh issue view <number> --json title,body
   git log origin/main..HEAD --oneline
   git diff origin/main...HEAD --stat
   ```

   Write a 1-3 sentence comment covering:
   - What the root cause was
   - What was changed to fix it

   Keep it concise and factual. Do not repeat the issue title back.

3. **Post the comment and close the issue**

   ```
   gh issue close <number> --comment "<summary>"
   ```

4. **Report back**

   Output the issue URL and confirm it was closed.
