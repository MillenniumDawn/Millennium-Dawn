#!/usr/bin/env python3
# Keep replace_path entries in descriptor.mod and Millennium_Dawn.mod
# identical: a divergence changes the loaded file set and breaks the
# multiplayer checksum between dev and workshop installs.
import os
import re
from typing import Dict, List, Tuple

from validator_common import BaseValidator, Colors, FileOpener, run_validator_main

MOD_DESCRIPTOR_FILES = ("descriptor.mod", "Millennium_Dawn.mod")

# Anchored at line start so commented-out entries (`# replace_path = ...`)
# don't match.
REPLACE_PATH_RE = re.compile(r'^\s*replace_path\s*=\s*"([^"]+)"')


def parse_replace_paths(text: str) -> List[Tuple[str, int]]:
    """Return (value, 1-based line number) pairs for replace_path entries."""
    results = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        match = REPLACE_PATH_RE.match(line)
        if match:
            results.append((match.group(1), line_num))
    return results


class Validator(BaseValidator):
    TITLE = "MOD DESCRIPTOR VALIDATION"
    STAGED_EXTENSIONS = [".mod"]

    def run_validations(self):
        if self.staged_only and not any(
            os.path.basename(f) in MOD_DESCRIPTOR_FILES
            for f in (self.staged_files or [])
        ):
            self.log(
                "No descriptor.mod or Millennium_Dawn.mod staged — skipping mod descriptor validation",
                "warning",
            )
            return

        self._validate_descriptors()

    def _validate_descriptors(self):
        parsed: Dict[str, List[Tuple[str, int]]] = {}
        for filename in MOD_DESCRIPTOR_FILES:
            filepath = os.path.join(self.mod_path, filename)
            if not os.path.isfile(filepath):
                self.add_error(
                    "missing-mod-file", f"{filename} missing at mod root", filename
                )
                continue
            parsed[filename] = parse_replace_paths(FileOpener.open_text_file(filepath))
            self.log(
                f"  Found {len(parsed[filename])} replace_path entries in {filename}"
            )

        if len(parsed) != len(MOD_DESCRIPTOR_FILES):
            # Missing-file errors already reported; the remaining checks
            # need both files.
            return

        self._check_duplicates(parsed)
        self._check_sync(parsed)

    def _check_duplicates(self, parsed):
        self._log_section("Checking duplicate replace_path entries...")
        issues = 0
        for filename, entries in parsed.items():
            first_seen: Dict[str, int] = {}
            for value, line_num in entries:
                if value in first_seen:
                    self.add_warning(
                        "duplicate-replace-path",
                        f'duplicate replace_path "{value}" (first at line {first_seen[value]})',
                        filename,
                        line_num,
                    )
                    issues += 1
                else:
                    first_seen[value] = line_num
        if issues == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No duplicate replace_path entries{Colors.ENDC if self.use_colors else ''}"
            )

    def _check_sync(self, parsed):
        self._log_section(
            "Checking replace_path sync between descriptor.mod and Millennium_Dawn.mod..."
        )
        descriptor, launcher = MOD_DESCRIPTOR_FILES
        descriptor_values = {value for value, _ in parsed[descriptor]}
        launcher_values = {value for value, _ in parsed[launcher]}
        issues = 0
        for value, line_num in parsed[descriptor]:
            if value not in launcher_values:
                self.add_error(
                    "replace-path-sync",
                    f'replace_path "{value}" is in {descriptor} but not {launcher}',
                    descriptor,
                    line_num,
                )
                issues += 1
        for value, line_num in parsed[launcher]:
            if value not in descriptor_values:
                self.add_error(
                    "replace-path-sync",
                    f'replace_path "{value}" is in {launcher} but not {descriptor}',
                    launcher,
                    line_num,
                )
                issues += 1
        if issues == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ replace_path entries match in both mod descriptors{Colors.ENDC if self.use_colors else ''}"
            )


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate mod descriptor replace_path sync in Millennium Dawn mod"
    )
