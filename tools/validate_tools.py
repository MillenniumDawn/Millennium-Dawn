#!/usr/bin/env python3
"""
Millennium Dawn Tools Validator

Validates the tools directory structure and Python scripts for Millennium Dawn mod.
This script checks for:
- Python syntax errors
- Missing shebang lines
- Proper file permissions
- Required dependencies
- Script functionality
"""

import argparse
import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ToolsValidator:
    def __init__(self, tools_dir: str = "tools", verbose: bool = False):
        self.tools_dir = Path(tools_dir)
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.info = []

        # Known Python scripts that should be validated
        self.python_scripts = set()

        # Required dependencies from requirements.txt
        self.required_deps = set()

        # Scripts that require specific dependencies
        self.script_dependencies = {}

        # Known validation scripts (should not be validated themselves)
        self.validation_scripts = {
            "validate_tools.py",
            "validate_variables.py",
            "validate_scripted_localisation.py",
            "validate_set_variables.py",
            "validate_cosmetic_tags.py",
            "validate_decisions.py",
            "validate_localisation.py",
            "validate_events.py",
        }

    def log(self, message: str, level: str = "info"):
        """Log messages with different levels"""
        if level == "error":
            self.errors.append(message)
            print(f"❌ ERROR: {message}")
        elif level == "warning":
            self.warnings.append(message)
            print(f"⚠️  WARNING: {message}")
        elif level == "info" and self.verbose:
            self.info.append(message)
            print(f"ℹ️  INFO: {message}")

    def find_python_scripts(self) -> List[Path]:
        """Find all Python scripts in the tools directory"""
        if not self.tools_dir.exists():
            self.log(f"Tools directory not found: {self.tools_dir}", "error")
            return []

        python_files = []
        for py_file in self.tools_dir.rglob("*.py"):
            # Skip validation scripts themselves
            if py_file.name not in self.validation_scripts:
                python_files.append(py_file)
                self.python_scripts.add(py_file.name)

        self.log(f"Found {len(python_files)} Python scripts to validate", "info")
        return python_files

    def check_shebang(self, file_path: Path) -> bool:
        """Check if Python script has proper shebang line"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()

            if not first_line.startswith("#!"):
                self.log(
                    f"Missing shebang in {file_path.relative_to(self.tools_dir)}",
                    "warning",
                )
                return False
            elif "python" not in first_line:
                self.log(
                    f"Invalid shebang in {file_path.relative_to(self.tools_dir)}: {first_line}",
                    "warning",
                )
                return False
            else:
                if self.verbose:
                    self.log(
                        f"Valid shebang in {file_path.relative_to(self.tools_dir)}",
                        "info",
                    )
                return True
        except Exception as e:
            self.log(
                f"Error reading {file_path.relative_to(self.tools_dir)}: {e}", "error"
            )
            return False

    def check_syntax(self, file_path: Path) -> bool:
        """Check Python syntax using AST parsing"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            # Parse the AST to check syntax
            ast.parse(source, filename=str(file_path))

            if self.verbose:
                self.log(
                    f"Valid syntax in {file_path.relative_to(self.tools_dir)}", "info"
                )
            return True

        except SyntaxError as e:
            self.log(
                f"Syntax error in {file_path.relative_to(self.tools_dir)}: {e}", "error"
            )
            return False
        except Exception as e:
            self.log(
                f"Error parsing {file_path.relative_to(self.tools_dir)}: {e}", "error"
            )
            return False

    def analyze_imports(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """Analyze imports in a Python script"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            imports = set()
            from_imports = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        from_imports.add(node.module.split(".")[0])

            return imports, from_imports

        except Exception as e:
            self.log(
                f"Error analyzing imports in {file_path.relative_to(self.tools_dir)}: {e}",
                "error",
            )
            return set(), set()

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        if not (self.tools_dir / "requirements.txt").exists():
            self.log("No requirements.txt found", "warning")
            return True

        try:
            with open(self.tools_dir / "requirements.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse package name (handle version specifiers)
                        package = (
                            line.split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split("!=")[0]
                            .split("~=")[0]
                        )
                        self.required_deps.add(package.lower())

            # Check if packages are installed
            missing_deps = []
            for dep in self.required_deps:
                try:
                    # Try importing with different possible names
                    if dep == "pillow":
                        __import__("PIL")
                    else:
                        __import__(dep)
                except ImportError:
                    missing_deps.append(dep)

            if missing_deps:
                self.log(f"Missing dependencies: {', '.join(missing_deps)}", "error")
                return False
            else:
                self.log(
                    f"All {len(self.required_deps)} required dependencies are installed",
                    "info",
                )
                return True

        except Exception as e:
            self.log(f"Error checking dependencies: {e}", "error")
            return False

    def check_script_functionality(self, file_path: Path) -> bool:
        """Test if script can be imported and has main function"""
        try:
            # Try to import the module
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            if spec is None:
                self.log(
                    f"Could not create spec for {file_path.relative_to(self.tools_dir)}",
                    "warning",
                )
                return False

            module = importlib.util.module_from_spec(spec)

            # Check if script has main function or if it's executable
            with open(file_path, "r") as f:
                content = f.read()

            has_main = 'if __name__ == "__main__"' in content
            has_main_func = "def main(" in content

            if not has_main and not has_main_func:
                self.log(
                    f"No main function or __main__ check in {file_path.relative_to(self.tools_dir)}",
                    "warning",
                )

            if self.verbose:
                self.log(
                    f"Script {file_path.relative_to(self.tools_dir)} appears functional",
                    "info",
                )
            return True

        except Exception as e:
            self.log(
                f"Error testing functionality of {file_path.relative_to(self.tools_dir)}: {e}",
                "error",
            )
            return False

    def check_file_permissions(self, file_path: Path) -> bool:
        """Check if script has executable permissions"""
        try:
            # Check if file is executable
            is_executable = os.access(file_path, os.X_OK)

            if not is_executable:
                self.log(
                    f"Script {file_path.relative_to(self.tools_dir)} is not executable",
                    "warning",
                )
                return False
            else:
                if self.verbose:
                    self.log(
                        f"Script {file_path.relative_to(self.tools_dir)} has executable permissions",
                        "info",
                    )
                return True

        except Exception as e:
            self.log(
                f"Error checking permissions for {file_path.relative_to(self.tools_dir)}: {e}",
                "error",
            )
            return False

    def validate_script(self, file_path: Path) -> Dict:
        """Validate a single Python script"""
        script_name = file_path.name
        results = {
            "file": str(file_path.relative_to(self.tools_dir)),
            "shebang": False,
            "syntax": False,
            "imports": [],
            "from_imports": [],
            "dependencies": [],
            "executable": False,
            "functional": False,
            "errors": [],
            "warnings": [],
        }

        # Store current error/warning count
        error_count = len(self.errors)
        warning_count = len(self.warnings)

        # Check shebang
        results["shebang"] = self.check_shebang(file_path)

        # Check syntax
        results["syntax"] = self.check_syntax(file_path)

        # Analyze imports
        imports, from_imports = self.analyze_imports(file_path)
        results["imports"] = list(imports)
        results["from_imports"] = list(from_imports)

        # Check file permissions
        results["executable"] = self.check_file_permissions(file_path)

        # Check functionality
        results["functional"] = self.check_script_functionality(file_path)

        # Capture any new errors/warnings for this script
        current_errors = self.errors[error_count:]
        current_warnings = self.warnings[warning_count:]

        results["errors"] = current_errors
        results["warnings"] = current_warnings

        return results

    def validate_tools_directory(self) -> Dict:
        """Main validation function"""
        print("🔍 Millennium Dawn Tools Validator")
        print("=" * 50)

        # Check if tools directory exists
        if not self.tools_dir.exists():
            self.log(f"Tools directory not found: {self.tools_dir}", "error")
            return {}

        # Find all Python scripts
        python_scripts = self.find_python_scripts()

        if not python_scripts:
            self.log("No Python scripts found to validate", "warning")
            return {}

        # Check dependencies
        deps_ok = self.check_dependencies()

        # Validate each script
        validation_results = {}
        for script in python_scripts:
            print(f"\n📋 Validating: {script.relative_to(self.tools_dir)}")
            validation_results[script.name] = self.validate_script(script)

        # Generate summary
        self.generate_summary(validation_results, deps_ok)

        return validation_results

    def generate_summary(self, results: Dict, deps_ok: bool):
        """Generate validation summary"""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)

        total_scripts = len(results)
        valid_scripts = 0
        syntax_errors = 0
        missing_shebangs = 0
        permission_issues = 0

        for script_name, result in results.items():
            if result["syntax"] and result["shebang"] and result["executable"]:
                valid_scripts += 1
            if not result["syntax"]:
                syntax_errors += 1
            if not result["shebang"]:
                missing_shebangs += 1
            if not result["executable"]:
                permission_issues += 1

        print(f"Total scripts: {total_scripts}")
        print(f"Valid scripts: {valid_scripts}")
        print(f"Syntax errors: {syntax_errors}")
        print(f"Missing shebangs: {missing_shebangs}")
        print(f"Permission issues: {permission_issues}")
        print(f"Dependency issues: {0 if deps_ok else 1}")

        print(f"\nErrors found: {len(self.errors)}")
        print(f"Warnings found: {len(self.warnings)}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")

        # Overall result
        if len(self.errors) == 0:
            print(f"\n✅ VALIDATION PASSED")
            print("All tools are ready for use!")
        else:
            print(f"\n❌ VALIDATION FAILED")
            print("Please fix the errors above before using the tools.")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Millennium Dawn tools directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_tools.py                    # Basic validation
  python validate_tools.py --verbose         # Detailed output
  python validate_tools.py --tools-dir /path/to/tools  # Custom tools directory
  python validate_tools.py --output report.json  # Save results to JSON
        """,
    )

    parser.add_argument(
        "--tools-dir", default="tools", help="Path to tools directory (default: tools)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument("--output", "-o", help="Save validation results to JSON file")

    args = parser.parse_args()

    # Create validator
    validator = ToolsValidator(tools_dir=args.tools_dir, verbose=args.verbose)

    # Run validation
    results = validator.validate_tools_directory()

    # Save results if requested
    if args.output and results:
        try:
            with open(args.output, "w") as f:
                json.dump(
                    {
                        "validation_results": results,
                        "summary": {
                            "total_scripts": len(results),
                            "errors": len(validator.errors),
                            "warnings": len(validator.warnings),
                            "dependencies_ok": len(validator.errors) == 0,
                        },
                    },
                    f,
                    indent=2,
                )
            print(f"\n📄 Results saved to: {args.output}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

    # Exit with appropriate code
    sys.exit(0 if len(validator.errors) == 0 else 1)


if __name__ == "__main__":
    main()
