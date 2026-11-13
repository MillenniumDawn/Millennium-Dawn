#!/usr/bin/env python3
"""Catch broken 3D model meshes and texture data.

Every `.dds` under gfx/ and map/ must hold DDS data, not a PNG, JPEG or TGA
file renamed. `.mesh` and `.dds` files under gfx/models also get the checks of
tools/assets/audit_models.py. Broken mesh data is an ERROR: invalid or
zero-length normals and tangents, zero-area triangles, and skinning with
unweighted vertices, weights that do not sum to 1 or bones outside the
skeleton. Triangle counts over the art-standard target and texture formats
(compression, mipmaps, power-of-two sizes) are WARNINGs, since the standards
call them targets.

The CI workspace ships no meshes or textures, so this runs on commit over the
staged files. The model checks need numpy (`pip install --group analysis`)
and skip with a notice without it; the DDS data check does not.
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

MODEL_DIR = "gfx/models"
TEXTURE_DIRS = ("gfx", "map")
# TGA has no magic number, so it reads as unknown.
FOREIGN_FORMATS = ((b"\x89PNG", "PNG"), (b"\xff\xd8\xff", "JPEG"))


def foreign_format(path):
    """What a `.dds` file holds instead of DDS data, or None when it is DDS."""
    with open(path, "rb") as handle:
        head = handle.read(128)
    if head.startswith(b"DDS ") and len(head) == 128:
        return None
    for magic, name in FOREIGN_FORMATS:
        if head.startswith(magic):
            return name
    return "TGA, truncated or unknown"


class Validator(BaseValidator):
    TITLE = "ASSET DATA"
    STAGED_EXTENSIONS = [".mesh", ".dds", ".DDS"]

    def _files(self):
        """The staged files, or every mesh and texture under the asset folders."""
        mod = Path(self.mod_path).resolve()
        if self.staged_only:
            return [(mod / name).resolve() for name in self.staged_files or []]
        return [
            Path(folder, name)
            for top in TEXTURE_DIRS
            for folder, _dirs, names in os.walk(mod / top)
            for name in names
            if name.lower().endswith((".mesh", ".dds"))
        ]

    def run_validations(self):
        mod = Path(self.mod_path).resolve()
        models = []
        for path in self._files():
            if not path.is_file():
                continue
            rel_path = path.relative_to(mod).as_posix()
            is_texture = path.suffix.lower() == ".dds"
            if is_texture and rel_path.split("/")[0] in TEXTURE_DIRS:
                if not self._holds_dds_data(path, rel_path):
                    continue
            if path.is_relative_to(mod / MODEL_DIR):
                models.append(path)
        if models:
            self._audit_models(models)

    def _holds_dds_data(self, path, rel_path):
        """Report a `.dds` that holds other data. True when it is DDS."""
        try:
            holds = foreign_format(path)
        except OSError as exc:
            self.add_error("texture-unreadable", str(exc), rel_path)
            return False
        if holds:
            self.add_error(
                "texture-not-dds-data",
                f"holds {holds} data under a .dds name; save it as DDS",
                rel_path,
            )
        return holds is None

    def _audit_models(self, paths):
        if audit_models is None:
            self.log(
                "  numpy is not installed; skipping the mesh and model texture "
                "checks (pip install --group analysis)",
                "warning",
            )
            return
        checked, report = audit_models.run(paths, root=self.mod_path)
        for rel_path, findings in report.items():
            kind = "mesh" if rel_path.lower().endswith(".mesh") else "texture"
            for finding in findings:
                name = finding.split(" ")[0].rstrip(":")
                category = f"{kind}-{name.replace('_', '-')}"
                if name == "triangles" or (kind == "texture" and name != "unreadable"):
                    self.add_warning(category, finding, rel_path)
                else:
                    self.add_error(category, finding, rel_path)
        self.log(f"  Checked {checked} model files | {len(report)} with findings")
        if report:
            self.log(
                "  Fix one model at a time and check it in game: "
                "see gfx/models/README.md",
                "warning",
            )


if __name__ == "__main__":
    run_validator_main(Validator, "Catch broken 3D model meshes and texture data")
