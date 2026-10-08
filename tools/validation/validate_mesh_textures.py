#!/usr/bin/env python3
"""Validate the textures each 3D model actually renders with.

A `.mesh` names its diffuse, normal and specular textures per material, and a
`pdxmesh` block may replace them with `meshsettings`. The engine finds those
names anywhere under gfx/, so only two things are real defects: a rendered
material whose texture name is an empty string, and a name no texture file
carries. `Collision` materials never render and carry empty slots by design.
A slot absent from the material is not reported: vanilla ships helper shapes
(`dummyShape` in the bomber meshes) that way.

The CI workspace ships no gfx/models or gfx/entities, so this runs on commit.
"""

import glob
import os
import re
import struct
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import find_hoi4_install
from validator_common import BaseValidator, run_validator_main, strip_comments

SLOTS = {"diff": "texture_diffuse", "n": "texture_normal", "spec": "texture_specular"}
TEXTURE_EXTENSIONS = (".dds", ".tga", ".png")
SCOPE_DIRS = ("gfx/models", "gfx/entities")

PDXMESH_RE = re.compile(r"\bpdxmesh\s*=\s*\{", re.IGNORECASE)
MESHSETTINGS_RE = re.compile(r"\bmeshsettings\s*=\s*\{", re.IGNORECASE)
FILE_RE = re.compile(r'\bfile\s*=\s*"([^"]+)"', re.IGNORECASE)
NAME_RE = re.compile(r'\bname\s*=\s*"([^"]*)"', re.IGNORECASE)
INDEX_RE = re.compile(r"\bindex\s*=\s*(\d+)")
TEXTURE_RE = re.compile(r'\b(texture_\w+)\s*=\s*"([^"]*)"', re.IGNORECASE)


class MeshParseError(ValueError):
    pass


@dataclass
class Material:
    shape: str
    index: int
    shader: str = ""
    textures: Dict[str, str] = field(default_factory=dict)


def parse_mesh_materials(data: bytes) -> List[Material]:
    """Walk a binary PDX mesh and return its materials in file order.

    Objects are `[`-depth markers with a NUL-terminated name. Properties are
    `!`, a length-prefixed name, a type byte and a u32 count; `i` and `f` hold
    4-byte values, `s` holds u32-length strings.
    """
    if not data.startswith(b"@@b@"):
        raise MeshParseError("missing @@b@ header")
    materials: List[Material] = []
    shape, mesh_index = "", -1
    current: Optional[Material] = None
    pos, end = 4, len(data)
    while pos < end:
        marker = data[pos]
        if marker == ord("["):
            depth = 0
            while pos < end and data[pos] == ord("["):
                depth += 1
                pos += 1
            stop = data.find(b"\0", pos)
            if stop < 0:
                raise MeshParseError(f"unterminated object name at byte {pos}")
            name = data[pos:stop].decode("latin-1")
            pos = stop + 1
            current = None
            if depth == 2:
                shape, mesh_index = name, -1
            elif depth == 3 and name == "mesh":
                mesh_index += 1
            elif depth == 4 and name == "material":
                current = Material(shape, mesh_index)
                materials.append(current)
        elif marker == ord("!"):
            length = data[pos + 1]
            key = data[pos + 2 : pos + 2 + length].decode("latin-1")
            pos += 2 + length
            kind = data[pos : pos + 1]
            (count,) = struct.unpack_from("<I", data, pos + 1)
            pos += 5
            if kind in (b"i", b"f"):
                pos += 4 * count
                continue
            if kind != b"s":
                raise MeshParseError(f"unknown property type {kind!r} at byte {pos}")
            values = []
            for _ in range(count):
                (size,) = struct.unpack_from("<I", data, pos)
                values.append(data[pos + 4 : pos + 4 + size].rstrip(b"\0"))
                pos += 4 + size
            if current is None or not values:
                continue
            value = values[0].decode("latin-1")
            if key == "shader":
                current.shader = value
            elif key in SLOTS:
                current.textures[SLOTS[key]] = value
        else:
            raise MeshParseError(f"unexpected byte {marker:#x} at {pos}")
    return materials


def _block_body(text: str, open_brace_end: int) -> str:
    depth, pos = 1, open_brace_end
    while depth and pos < len(text):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
        pos += 1
    return text[open_brace_end : pos - 1]


def parse_pdxmeshes(text: str) -> List[Tuple[int, str, str, List[dict]]]:
    """(line, name, mesh file, meshsettings) for each pdxmesh definition."""
    clean = strip_comments(text)
    result = []
    for match in PDXMESH_RE.finditer(clean):
        body = _block_body(clean, match.end())
        file_match = FILE_RE.search(body)
        if not file_match:
            continue
        settings = []
        for ms in MESHSETTINGS_RE.finditer(body):
            ms_body = _block_body(body, ms.end())
            name = NAME_RE.search(ms_body)
            index = INDEX_RE.search(ms_body)
            settings.append(
                {
                    "name": name.group(1) if name else None,
                    "index": int(index.group(1)) if index else 0,
                    "textures": {
                        k.lower(): v
                        for k, v in TEXTURE_RE.findall(ms_body)
                        if k.lower() in SLOTS.values()
                    },
                }
            )
        # The pdxmesh's own name, not a meshsettings shape name.
        first_setting = MESHSETTINGS_RE.search(body)
        name = NAME_RE.search(body[: first_setting.start()] if first_setting else body)
        line = clean.count("\n", 0, match.start()) + 1
        result.append(
            (line, name.group(1) if name else "?", file_match.group(1), settings)
        )
    return result


def effective_materials(
    materials: List[Material], settings: List[dict]
) -> List[Material]:
    """Rendered materials with meshsettings applied.

    A named setting targets that shape's mesh `index`; an unnamed one targets
    the `index`-th rendered material, which is how MD writes single-shape
    overrides.
    """
    result = [
        replace(m, textures=dict(m.textures))
        for m in materials
        if m.shader.lower() != "collision"
    ]
    for setting in settings:
        if setting["name"] is not None:
            targets = [
                m
                for m in result
                if m.shape == setting["name"] and m.index == setting["index"]
            ]
        elif setting["index"] < len(result):
            targets = [result[setting["index"]]]
        else:
            targets = []
        for target in targets:
            target.textures.update(setting["textures"])
    return result


def _texture_names(root: str) -> Set[str]:
    names: Set[str] = set()
    for _dirpath, _dirs, files in os.walk(os.path.join(root, "gfx")):
        names.update(f.lower() for f in files if f.lower().endswith(TEXTURE_EXTENSIONS))
    return names


class Validator(BaseValidator):
    TITLE = "MESH TEXTURES"
    STAGED_EXTENSIONS = [".mesh", ".gfx", ".asset", ".dds", ".tga"]

    def run_validations(self):
        mod = Path(self.mod_path)
        if self.staged_only and not self.staged_touches(SCOPE_DIRS):
            return
        meshes = {
            Path(p).relative_to(mod).as_posix().lower(): p
            for p in glob.glob(str(mod / "gfx" / "**" / "*.mesh"), recursive=True)
        }
        if not meshes:
            return

        textures = _texture_names(self.mod_path)
        install = find_hoi4_install()
        if install:
            textures |= _texture_names(install)
        else:
            self.log(
                "  No HoI4 install found; skipping unresolved-name checks "
                "(set HOI4_PATH to enable them)"
            )

        parsed: Dict[str, List[Material]] = {}
        entries = findings = 0
        for gfx in sorted(
            glob.glob(str(mod / "gfx" / "**" / "*.gfx"), recursive=True)
            + glob.glob(str(mod / "gfx" / "**" / "*.asset"), recursive=True)
        ):
            rel_gfx = Path(gfx).relative_to(mod).as_posix()
            try:
                with open(gfx, encoding="utf-8-sig") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as exc:
                self.add_error("mesh-read-error", f"cannot read: {exc}", rel_gfx)
                continue
            for line, name, mesh_file, settings in parse_pdxmeshes(text):
                key = mesh_file.replace("\\", "/").lstrip("/").lower()
                if key not in meshes:
                    continue
                entries += 1
                if key not in parsed:
                    try:
                        with open(meshes[key], "rb") as fh:
                            parsed[key] = parse_mesh_materials(fh.read())
                    except (OSError, MeshParseError, struct.error) as exc:
                        self.add_error(
                            "mesh-read-error",
                            f"cannot read {mesh_file}: {exc}",
                            rel_gfx,
                            line,
                        )
                        parsed[key] = []
                for material in effective_materials(parsed[key], settings):
                    where = (
                        f"pdxmesh '{name}': {mesh_file} shape '{material.shape}' "
                        f"mesh {material.index}"
                    )
                    empty = [
                        s for s, texture in material.textures.items() if not texture
                    ]
                    if empty:
                        findings += 1
                        self.add_error(
                            "mesh-texture-empty",
                            f"{where} has no {', '.join(empty)}; "
                            "add a meshsettings block that names them",
                            rel_gfx,
                            line,
                        )
                    if not install:
                        continue
                    for slot, texture in material.textures.items():
                        if texture and texture.lower() not in textures:
                            findings += 1
                            self.add_error(
                                "mesh-texture-missing",
                                f"{where} {slot} '{texture}' matches no texture file",
                                rel_gfx,
                                line,
                            )
        self.log(
            f"  Scanned {entries} pdxmesh entries | {len(parsed)} meshes | "
            f"{findings} findings"
        )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate textures rendered by 3D models")
