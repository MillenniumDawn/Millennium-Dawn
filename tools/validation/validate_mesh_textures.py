#!/usr/bin/env python3
"""Validate the textures each 3D model actually renders with.

A `.mesh` names its diffuse, normal and specular textures per material, and a
`pdxmesh` block may replace them with `meshsettings`. The engine finds those
names anywhere under gfx/, so only two things are real defects: a rendered
material whose texture name is an empty string, and a name no texture file
carries. `Collision` materials never render and carry empty slots by design.
A slot absent from the material is not reported: vanilla ships helper shapes
(`dummyShape` in the bomber meshes) that way. A name that several MD files
under gfx/ carry with different content is a warning: the game may load any
of them.

The CI workspace ships no meshes or textures, so this runs on commit.
"""

import os
import re
import struct
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import find_hoi4_install, find_unquoted_block_end, list_files
from validator_common import BaseValidator, run_validator_main, strip_comments

SLOTS = {"diff": "texture_diffuse", "n": "texture_normal", "spec": "texture_specular"}
TEXTURE_EXTENSIONS = (".dds", ".tga", ".png")
# A staged texture anywhere under gfx/ can clash with a model's texture name.
SCOPE_DIRS = ("gfx",)

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
    return text[open_brace_end : find_unquoted_block_end(text, open_brace_end)[0] - 1]


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


def _texture_files(root: str) -> Dict[str, List[str]]:
    """Each texture file name under gfx/, lower-cased, with the paths carrying it."""
    files: Dict[str, List[str]] = {}
    for dirpath, _dirs, names in os.walk(os.path.join(root, "gfx")):
        for name in names:
            if name.lower().endswith(TEXTURE_EXTENSIONS):
                files.setdefault(name.lower(), []).append(os.path.join(dirpath, name))
    return files


def _contents_differ(paths: List[str]) -> bool:
    contents = set()
    for path in paths:
        with open(path, "rb") as fh:
            contents.add(fh.read())
    return len(contents) > 1


class Validator(BaseValidator):
    TITLE = "MESH TEXTURES"
    STAGED_EXTENSIONS = [""]
    STAGED_INCLUDE_MISSING = True

    def run_validations(self):
        mod = Path(self.mod_path)
        if self.staged_only and not self.staged_touches(SCOPE_DIRS):
            return
        meshes = {
            Path(p).relative_to(mod).as_posix().lower(): p
            for p in list_files(mod / "gfx", ("*.mesh",))
        }
        if not meshes:
            return

        mod_textures = _texture_files(self.mod_path)
        textures = set(mod_textures)
        install = find_hoi4_install()
        if install:
            textures |= set(_texture_files(install))
        else:
            self.log(
                "  No HoI4 install found; skipping unresolved-name checks "
                "(set HOI4_PATH to enable them)"
            )

        parsed: Dict[str, List[Material]] = {}
        clash_checked: Set[str] = set()
        entries = findings = 0
        for gfx in list_files(mod / "gfx", ("*.gfx", "*.asset")):
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
                    for slot, texture in material.textures.items():
                        key = texture.lower()
                        if install and texture and key not in textures:
                            findings += 1
                            self.add_error(
                                "mesh-texture-missing",
                                f"{where} {slot} '{texture}' matches no texture file",
                                rel_gfx,
                                line,
                            )
                        paths = mod_textures.get(key, [])
                        if len(paths) < 2 or key in clash_checked:
                            continue
                        clash_checked.add(key)
                        findings += self._report_name_clash(
                            f"{where} {slot} '{texture}'", paths, rel_gfx, line
                        )
        self.log(
            f"  Scanned {entries} pdxmesh entries | {len(parsed)} meshes | "
            f"{findings} findings"
        )

    def _report_name_clash(self, what, paths, rel_gfx, line) -> int:
        mod = Path(self.mod_path)
        names = ", ".join(sorted(Path(p).relative_to(mod).as_posix() for p in paths))
        try:
            differ = _contents_differ(paths)
        except OSError as exc:
            self.add_error("mesh-read-error", f"cannot read {names}: {exc}", rel_gfx)
            return 1
        if not differ:
            return 0
        self.add_warning(
            "mesh-texture-name-clash",
            f"{what} is carried by {len(paths)} files with different content "
            f"({names}); the game may load any of them, so rename the ones the "
            "model should not use",
            rel_gfx,
            line,
        )
        return 1


if __name__ == "__main__":
    run_validator_main(Validator, "Validate textures rendered by 3D models")
