#!/usr/bin/env python3
"""Warn about broken mesh data and model texture formats.

Runs the checks of tools/assets/audit_models.py on `.mesh` and `.dds` files
under gfx/models: invalid normals, tangents and skinning, zero-area triangles,
triangle counts over the art-standard target, and textures that are not
compressed DDS with mipmaps at a power-of-two size. Every finding is a WARNING
while the existing backlog is fixed one model at a time.

The CI workspace ships no meshes or textures, so this runs on commit. It needs
numpy (`pip install --group analysis`) and skips with a notice without it.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "assets"))

from validator_common import BaseValidator, run_validator_main

try:
    import audit_models
except ModuleNotFoundError as exc:
    if exc.name != "numpy":
        raise
    audit_models = None

SCOPE = "gfx/models"


class Validator(BaseValidator):
    TITLE = "MODEL ASSETS"
    STAGED_EXTENSIONS = [".mesh", ".dds"]

    def _paths(self):
        """The staged files under gfx/models, or the whole folder."""
        mod = Path(self.mod_path).resolve()
        if not self.staged_only:
            return [mod / SCOPE] if (mod / SCOPE).is_dir() else []
        paths = [(mod / name).resolve() for name in self.staged_files or []]
        return [
            path
            for path in paths
            if path.is_relative_to(mod / SCOPE) and path.is_file()
        ]

    def run_validations(self):
        paths = self._paths()
        if not paths:
            return
        if audit_models is None:
            self.log(
                "  numpy is not installed; skipping model asset checks "
                "(pip install --group analysis)",
                "warning",
            )
            return
        checked, report = audit_models.run(paths, root=self.mod_path)
        for rel_path, findings in report.items():
            for finding in findings:
                name = finding.split(" ")[0].rstrip(":").replace("_", "-")
                self.add_warning(f"model-{name}", finding, rel_path)
        self.log(f"  Checked {checked} model files | {len(report)} with findings")
        if report:
            self.log(
                "  Fix one model at a time and check it in game: "
                "see gfx/models/README.md",
                "warning",
            )


if __name__ == "__main__":
    run_validator_main(Validator, "Warn about broken 3D model meshes and textures")
