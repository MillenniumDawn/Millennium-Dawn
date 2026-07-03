Standardize a Millennium Dawn mod file using the standardization tools.

File to standardize: $ARGUMENTS

Steps:
1. Determine the file type from the path:
   - `common/national_focus/` or filename contains "focus" → `focus`
   - `events/` → `event`
   - `common/decisions/` → `decision`
   - `common/ideas/` → `idea`
   - `common/military_industrial_organization/organizations/` → `mio`
   If the type cannot be determined, ask the user to clarify.

2. Run from the `tools/standardization/` directory:
   ```
   python3 standardize.py <type> <absolute_file_path> --backup --verbose
   ```

3. Report what changed: list each block that was reformatted and what was fixed (missing logging, property reordering, removed performance-hurting patterns, etc.)

4. If any issues were warned about but not auto-fixed, list them so the user can address them manually.
