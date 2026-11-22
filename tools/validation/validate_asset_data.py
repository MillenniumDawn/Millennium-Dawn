#!/usr/bin/env python3
"""Catch broken 3D model meshes and texture data.

Every `.dds` under gfx/ and map/ must hold DDS data. The folder's format and
mipmap rules block staged or PR-changed textures and warn in a manual scan.
The DDS checks only read headers and need no third-party packages.

The commit hook also runs the checks of tools/assets/audit_models.py for
files under gfx/models. Broken mesh data is an ERROR; triangle counts and
model texture sizes are WARNINGs. Those checks need numpy (`pip install
--group analysis`). CI checks only changed DDS files, not meshes.
"""

import os
import shlex
import struct
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "assets"))

import model_standards as standards
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
DDS_HEADER_SIZE = 128
BGRA_MASKS = (0xFF0000, 0xFF00, 0xFF, 0xFF000000)
DXT = (b"DXT1", b"DXT5")
RAW = "uncompressed 32-bit A8R8G8B8"
COMPRESSED = "DXT1 or DXT5 (DXT5 if alpha carries data)"


def foreign_format(head):
    """What a `.dds` header holds instead of DDS data, or None when it is DDS."""
    if head.startswith(b"DDS ") and len(head) >= DDS_HEADER_SIZE:
        return None
    for magic, name in FOREIGN_FORMATS:
        if head.startswith(magic):
            return name
    return "TGA, truncated or unknown"


def _format_problem(head, rule, short_side):
    flags, code, bits, *masks = struct.unpack_from("<I4s5I", head, 80)
    fourcc = code if flags & 4 else b""
    if fourcc == b"DX10":
        return "use a legacy DDS header, not DX10"
    is_raw = not fourcc and flags & 0x41 == 0x41 and bits == 32
    is_raw = is_raw and tuple(masks) == BGRA_MASKS
    if rule == standards.FORMAT_ICON or (
        rule == standards.FORMAT_PORTRAIT and short_side < standards.SMALL_PORTRAIT_SIZE
    ):
        return None if is_raw else f"use {RAW}"
    if rule == standards.FORMAT_DXT5:
        return (
            None if is_raw or fourcc == b"DXT5" else f"use DXT5 or {RAW} for flat art"
        )
    if rule == standards.FORMAT_PORTRAIT:
        if not (is_raw or fourcc in DXT):
            return f"use {COMPRESSED}, or {RAW} for flat art"
    elif rule == standards.FORMAT_COMPRESSED:
        return None if fourcc in DXT else f"use {COMPRESSED}"
    elif not (is_raw or fourcc in (*DXT, b"DXT3")):
        return f"use {RAW}, or legacy DXT for large art that passes the quality check"
    return None


def _standard_problems(head, rel_path):
    format_rule = standards.texture_format(rel_path)
    mip_rule = standards.mipmap_rule(rel_path)
    if format_rule == standards.FORMAT_KEEP and mip_rule == standards.MIPMAP_KEEP:
        return []
    flags, height, width, _pitch, _depth, count = struct.unpack_from("<6I", head, 8)
    header_size = struct.unpack_from("<I", head, 4)[0]
    pixel_format_size = struct.unpack_from("<I", head, 76)[0]
    if (header_size, pixel_format_size) != (124, 32) or not min(width, height):
        return ["invalid DDS header size, pixel format size or image dimensions"]
    problems = []
    if format_rule != standards.FORMAT_KEEP:
        problem = _format_problem(head, format_rule, min(width, height))
        if problem:
            problems.append(problem)
    has_mipmaps = flags & 0x20000 and count > 1
    if (
        mip_rule == standards.MIPMAP_NEEDED
        and not has_mipmaps
        and max(width, height) > 4
    ):
        problems.append("add mipmaps")
    elif mip_rule == standards.MIPMAP_NONE and has_mipmaps:
        problems.append("remove mipmaps")
    return problems


class Validator(BaseValidator):
    TITLE = "ASSET DATA"
    # Filter locally so mixed-case extensions reach the same checks as the hook.
    STAGED_EXTENSIONS = [""]
    # The shared collector includes rename destinations only in this mode.
    STAGED_INCLUDE_MISSING = True

    def __init__(self, mod_path, *, texture_paths_from=None, **kwargs):
        super().__init__(mod_path, **kwargs)
        self.texture_paths_from = texture_paths_from

    def _files(self):
        """Explicit PR paths, staged paths, or the full asset scan."""
        mod = Path(self.mod_path).resolve()
        if self.texture_paths_from is not None:
            names = self.texture_paths_from.read_bytes().split(b"\0")
            return [mod / os.fsdecode(name) for name in names if name]
        if self.staged_only:
            return [
                mod / name
                for name in self.staged_files or []
                if Path(name).suffix.lower() in (".mesh", ".dds")
            ]
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
            if not path.is_file() and self.texture_paths_from is None:
                continue
            rel_path = path.relative_to(mod).as_posix()
            is_texture = path.suffix.lower() == ".dds"
            if is_texture and rel_path.split("/")[0].lower() in TEXTURE_DIRS:
                if not self._check_dds(path, rel_path):
                    continue
            if self.texture_paths_from is None and path.is_relative_to(mod / MODEL_DIR):
                models.append(path)
        if models:
            self._audit_models(models)

    def _check_dds(self, path, rel_path):
        try:
            with path.open("rb") as handle:
                head = handle.read(DDS_HEADER_SIZE)
        except OSError as exc:
            self.add_error("texture-unreadable", str(exc), rel_path)
            return False
        preview = f"python3 tools/assets/dds_standardize.py {shlex.quote(rel_path)}"
        holds = foreign_format(head)
        if holds:
            self.add_error(
                "texture-not-dds-data",
                f"holds {holds} data under a .dds name; save it as DDS. Preview: {preview}",
                rel_path,
            )
            return False
        problems = _standard_problems(head, rel_path)
        if problems:
            report = (
                self.add_error
                if self.staged_only or self.texture_paths_from is not None
                else self.add_warning
            )
            report(
                "texture-art-standard",
                f"{'; '.join(problems)}. Re-export from source if needed. Preview: {preview}",
                rel_path,
            )
        return True

    def _audit_models(self, paths):
        if audit_models is None:
            self.log(
                "  numpy is not installed; skipping the mesh and model texture "
                "checks (pip install --group analysis)",
                "warning",
            )
            return
        checked, report = audit_models.run(paths, root=Path(self.mod_path))
        for rel_path, findings in report.items():
            kind = "mesh" if rel_path.lower().endswith(".mesh") else "texture"
            for finding in findings:
                name = finding.split(" ")[0].rstrip(":")
                if kind == "texture" and name in (
                    "dx10_header",
                    "uncompressed",
                    "no_mipmaps",
                ):
                    continue  # Already covered by the folder's DDS rule.
                category = f"{kind}-{name.replace('_', '-')}"
                if name == "triangles" or (kind == "texture" and name != "unreadable"):
                    self.add_warning(category, finding, rel_path)
                else:
                    self.add_error(category, finding, rel_path)
        self.log(f"  Checked {checked} model files | {len(report)} with findings")
        if any(Path(path).suffix.lower() == ".mesh" for path in report):
            self.log(
                "  Fix one model at a time and check it in game: "
                "see gfx/models/README.md",
                "warning",
            )


def _extra_args(parser):
    parser.add_argument(
        "--texture-paths-from",
        type=Path,
        help="validate only DDS files in a NUL-separated list of changed paths",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate DDS textures and staged model data", _extra_args
    )
