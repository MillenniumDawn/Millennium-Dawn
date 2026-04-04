#!/usr/bin/env python3
"""Validate Python scripts in the Millennium Dawn tools directory."""

import ast
import importlib.util
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "validation"))
from validator_common import BaseValidator, Colors, run_validator_main

# Prevent self-validation
_SKIP_SCRIPTS = frozenset({"validate_tools.py"})


class ToolsValidator(BaseValidator):
    TITLE = "TOOLS VALIDATION"
    STAGED_EXTENSIONS = [".py"]

    def __init__(self, mod_path: str, **kwargs):
        super().__init__(mod_path, **kwargs)
        self.tools_dir = Path(mod_path) / "tools"

    def _find_scripts(self) -> List[Path]:
        try:
            return sorted(
                p for p in self.tools_dir.rglob("*.py") if p.name not in _SKIP_SCRIPTS
            )
        except (FileNotFoundError, NotADirectoryError):
            self.log(
                f"  Warning: tools directory not found at {self.tools_dir}", "warning"
            )
            return []

    def _validate_script(self, path: Path) -> Tuple[Optional[str], bool, bool]:
        """Read file once; return (syntax_error, has_shebang, has_main)."""
        rel = str(path.relative_to(self.tools_dir))
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"{rel}: {e}", False, False

        syntax_err = None
        try:
            ast.parse(content, filename=str(path))
        except SyntaxError as e:
            syntax_err = f"{rel}: {e}"
        except Exception as e:
            syntax_err = f"{rel}: {e}"

        first_line = content.split("\n", 1)[0].strip()
        has_shebang = first_line.startswith("#!") and "python" in first_line
        has_main = 'if __name__ == "__main__"' in content or "def main(" in content

        return syntax_err, has_shebang, has_main

    def _is_executable(self, path: Path) -> bool:
        return os.access(path, os.X_OK)

    def _check_dependencies(self) -> List[str]:
        req_file = self.tools_dir / "requirements.txt"
        if not req_file.exists():
            return []
        missing = []
        try:
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    package = re.split(r"[><=!~]+", line)[0].strip()
                    import_name = "PIL" if package.lower() == "pillow" else package
                    if importlib.util.find_spec(import_name) is None:
                        missing.append(package)
        except Exception as e:
            return [f"Error reading requirements.txt: {e}"]
        return missing

    def run_validations(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking Python scripts...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        scripts = self._find_scripts()
        self.log(f"  Found {len(scripts)} Python scripts to validate")

        syntax_errors = []
        missing_shebangs = []
        non_executable = []
        no_main = []

        for path in scripts:
            rel = str(path.relative_to(self.tools_dir))
            syntax_err, has_shebang, has_main = self._validate_script(path)

            if syntax_err:
                syntax_errors.append(syntax_err)
            if not has_shebang:
                missing_shebangs.append(rel)
            if not self._is_executable(path):
                non_executable.append(rel)
            if not has_main:
                no_main.append(rel)

        self._report(
            syntax_errors,
            "✓ No syntax errors found",
            "Scripts with syntax errors:",
        )

        for name in missing_shebangs:
            self.log(f"  Warning: missing python shebang — {name}", "warning")
        for name in non_executable:
            self.log(f"  Warning: not executable — {name}", "warning")
        for name in no_main:
            self.log(f"  Warning: no main guard or main() — {name}", "warning")

        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking dependencies...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        missing_deps = self._check_dependencies()
        self._report(
            missing_deps,
            "✓ All required dependencies are installed",
            "Missing dependencies:",
        )


if __name__ == "__main__":
    run_validator_main(ToolsValidator, "Validate Millennium Dawn tools directory")
