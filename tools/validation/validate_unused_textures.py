#!/usr/bin/env python3
"""Find textures in gfx/ that no .gfx file references, plus references that
point at missing files. Vanilla HoI4 installs are auto-detected so vanilla
sprite refs don't get flagged; pass --hoi4-path to override."""
import glob
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import find_hoi4_install
from validator_common import (
    BaseValidator,
    Colors,
    FileOpener,
    run_validator_main,
    should_skip_file,
)

_TEXTURE_REF_PATTERNS = [
    re.compile(r'portrait\s*=\s*"([^"]+\.(?:dds|tga|png))"', re.IGNORECASE),
    re.compile(r'picture\s*=\s*"([^"]+\.(?:dds|tga|png))"', re.IGNORECASE),
    re.compile(r'"(gfx/[^"]+\.(?:dds|tga|png))"', re.IGNORECASE),
]
_DOUBLE_SLASH = re.compile(r"/{2,}")

TEXTURE_EXTENSIONS = [".dds", ".tga", ".png"]

EXTRA_SKIP_PATTERNS = ["resources", "loadingscreens"]


def find_texture_files(mod_path: str) -> Set[str]:
    """Find all texture files in the gfx/ directory."""
    gfx_path = str(Path(mod_path) / "gfx") + "/"
    texture_files = set()

    for ext in TEXTURE_EXTENSIONS:
        for filename in glob.iglob(gfx_path + f"**/*{ext}", recursive=True):
            # Check only for specific skip patterns (not the default gfx skip)
            skip = False
            for pattern in EXTRA_SKIP_PATTERNS:
                if pattern in filename:
                    skip = True
                    break
            if skip:
                continue

            # Store relative path from mod root for easier comparison
            rel_path = os.path.relpath(filename, mod_path)
            texture_files.add(rel_path)

    return texture_files


def process_gfx_file(args: Tuple[str, str, Set[str], Dict[str, List[str]]]) -> Set[str]:
    """
    Process a single .gfx file and extract all texturefile references.
    Returns a set of texture paths referenced in the file.
    For entity .gfx files, also matches by filename only.
    """
    filename, mod_path, texture_files, filename_lookup = args
    referenced_textures = set()

    try:
        content = FileOpener.open_text_file(
            filename, lowercase=False, strip_comments_flag=True
        )

        # Pattern 1: texturefile = "path/to/file.ext" (interface .gfx files)
        # Pattern 2: texture_diffuse/normal/specular = "file.ext" (entity .gfx files)
        patterns = [
            r'texturefile\s*=\s*"([^"]+)"',
            r'texture_diffuse\s*=\s*"([^"]+)"',
            r'texture_normal\s*=\s*"([^"]+)"',
            r'texture_specular\s*=\s*"([^"]+)"',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                texture_path = match.group(1)
                texture_path = texture_path.replace("\\", "/").lstrip("/")
                while "//" in texture_path:
                    texture_path = texture_path.replace("//", "/")

                # Check if this is a full path match
                if texture_path in texture_files:
                    referenced_textures.add(texture_path)
                else:
                    # Try to match by filename only (common for entity .gfx files)
                    ref_filename = os.path.basename(texture_path)
                    if ref_filename in filename_lookup:
                        # Add all matching paths (there might be duplicates with same filename)
                        for tex_path in filename_lookup[ref_filename]:
                            referenced_textures.add(tex_path)

    except Exception as e:
        # Silently skip files that can't be read
        pass

    return referenced_textures


def _extract_texture_refs(content: str) -> Set[str]:
    refs: Set[str] = set()
    for pat in _TEXTURE_REF_PATTERNS:
        for match in pat.finditer(content):
            ref = match.group(1).replace("\\", "/").lstrip("/")
            refs.add(_DOUBLE_SLASH.sub("/", ref))
    return refs


def process_game_file(
    args: Tuple[str, str, Set[str], Dict[str, List[str]]],
) -> Set[str]:
    # Cached path extraction is keyed on the file alone (no mod path / texture
    # set leak into the cache). Matching against the current texture index
    # runs in the worker after the cache hit.
    filename, mod_path, texture_files, filename_lookup = args
    try:
        content = FileOpener.open_text_file(
            filename, lowercase=False, strip_comments_flag=True
        )
    except Exception:
        content = ""
    refs = disk_cache.per_file_cached_by_content(
        mod_path,
        "unused_textures.refs",
        filename,
        content,
        lambda: _extract_texture_refs(content),
    )
    matched: Set[str] = set()
    for ref in refs:
        if ref in texture_files:
            matched.add(ref)
        else:
            ref_filename = os.path.basename(ref)
            for tex_path in filename_lookup.get(ref_filename, ()):
                matched.add(tex_path)
    return matched


class Validator(BaseValidator):
    TITLE = "UNUSED TEXTURE VALIDATION"
    STAGED_EXTENSIONS = [".gfx", ".dds", ".tga", ".png"]

    def __init__(self, *args, hoi4_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.texture_files = set()
        self.texture_filename_lookup = {}  # Maps filename -> list of full paths
        self.referenced_textures = set()
        self.vanilla_referenced_textures = set()
        self.game_file_textures = set()
        self.unused_count = 0
        self.missing_count = 0
        self.hoi4_path = hoi4_path
        self._detect_hoi4_installation()

    def _detect_hoi4_installation(self):
        """Detect Hearts of Iron IV installation path."""
        if self.hoi4_path:
            # Expand user path (e.g., ~ to home directory)
            self.hoi4_path = os.path.expanduser(self.hoi4_path)
            if os.path.exists(self.hoi4_path):
                self.log(f"Using provided HoI4 path: {self.hoi4_path}")
                return
            else:
                self.log(
                    f"{Colors.YELLOW if self.use_colors else ''}Warning: Provided HoI4 path does not exist: {self.hoi4_path}{Colors.ENDC if self.use_colors else ''}",
                    "warning",
                )
                self.hoi4_path = None

        # Auto-detect (also honours $HOI4_PATH)
        detected = find_hoi4_install()
        if detected:
            self.hoi4_path = detected
            self.log(f"Auto-detected HoI4 installation: {self.hoi4_path}")
            return

        self.log(
            f"{Colors.YELLOW if self.use_colors else ''}Warning: Could not find HoI4 installation. Vanilla .gfx files will not be checked.{Colors.ENDC if self.use_colors else ''}",
            "warning",
        )
        self.log(f"  Use --hoi4-path to specify the installation directory.")

    def _find_all_gfx_files(self, search_path: str = None) -> List[str]:
        """Find all .gfx files in the specified directory (mod or vanilla)."""
        gfx_files = []
        base_path = search_path if search_path else self.mod_path

        # Search in both gfx/ and interface/ directories (common locations for .gfx files)
        search_dirs = [
            str(Path(base_path) / "gfx") + "/",
            str(Path(base_path) / "interface") + "/",
        ]

        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for filename in glob.iglob(search_dir + "**/*.gfx", recursive=True):
                    # Check only for specific skip patterns (not the default gfx skip)
                    skip = False
                    for pattern in EXTRA_SKIP_PATTERNS:
                        if pattern in filename:
                            skip = True
                            break
                    if skip:
                        continue
                    gfx_files.append(filename)

        return gfx_files

    def _get_all_referenced_textures(
        self, search_path: str = None, label: str = "mod"
    ) -> Set[str]:
        """
        Get all texture files referenced in .gfx files using multiprocessing.
        """
        gfx_files = self._find_all_gfx_files(search_path)
        self.log(f"  Found {len(gfx_files)} {label} .gfx files to process")

        args_list = [
            (
                f,
                search_path if search_path else self.mod_path,
                self.texture_files,
                self.texture_filename_lookup,
            )
            for f in gfx_files
        ]

        all_results = self._pool_map(process_gfx_file, args_list, chunksize=10)

        referenced_textures = set()
        for texture_set in all_results:
            referenced_textures.update(texture_set)

        return referenced_textures

    def _get_game_file_references(self) -> Set[str]:
        """
        Scan common/, history/, events/, and portraits/ files for texture references.
        Returns a set of texture paths that are referenced.
        """
        game_files = []
        search_dirs = ["common", "history", "events", "portraits"]

        for dir_name in search_dirs:
            search_path = str(Path(self.mod_path) / dir_name)
            if os.path.exists(search_path):
                for filename in glob.iglob(search_path + "/**/*.txt", recursive=True):
                    if should_skip_file(filename):
                        continue
                    game_files.append(filename)

        self.log(f"  Found {len(game_files)} game files to scan")

        args_list = [
            (f, self.mod_path, self.texture_files, self.texture_filename_lookup)
            for f in game_files
        ]

        all_results = self._pool_map(process_game_file, args_list, chunksize=10)

        matched_textures = set()
        for texture_set in all_results:
            matched_textures.update(texture_set)

        return matched_textures

    def validate_unused_textures(self):
        self._log_section("Finding all texture files in gfx/...")

        self.texture_files = find_texture_files(self.mod_path)
        self.log(f"  Found {len(self.texture_files)} texture files")

        # Build filename lookup for fast matching (basename -> full paths)
        self.texture_filename_lookup = {}
        for tex_path in self.texture_files:
            filename = os.path.basename(tex_path)
            if filename not in self.texture_filename_lookup:
                self.texture_filename_lookup[filename] = []
            self.texture_filename_lookup[filename].append(tex_path)

        self._log_section("Scanning .gfx files for texture references...")

        self.referenced_textures = self._get_all_referenced_textures(label="mod")
        self.log(
            f"  Found {len(self.referenced_textures)} unique texture references in mod"
        )

        if self.hoi4_path:
            self._log_section("Scanning vanilla HoI4 .gfx files...")
            self.vanilla_referenced_textures = self._get_all_referenced_textures(
                search_path=self.hoi4_path, label="vanilla"
            )
            self.log(
                f"  Found {len(self.vanilla_referenced_textures)} unique texture references in vanilla"
            )

        self._log_section(
            "Scanning game files (common/history/events/portraits) for texture references..."
        )
        self.game_file_textures = self._get_game_file_references()
        self.log(
            f"  Found {len(self.game_file_textures)} textures referenced in game files"
        )

        self._log_section("Checking for unused textures...")

        # Find unused textures (not in .gfx files OR game files)
        unused_textures = []
        for texture_path in sorted(self.texture_files):
            if (
                texture_path not in self.referenced_textures
                and texture_path not in self.game_file_textures
            ):
                unused_textures.append(texture_path)

        self.unused_count = len(unused_textures)

        self._report(
            unused_textures,
            "✓ All texture files are referenced in .gfx or game files",
            "Texture files not referenced in any .gfx or game files:",
        )

    def validate_missing_textures(self):
        """Check for texture references in .gfx files that point to missing files."""
        self._log_section("Checking for missing texture files...")

        missing_textures = []
        for texture_ref in sorted(self.referenced_textures):
            # Check if the referenced texture exists in mod
            full_path = os.path.join(self.mod_path, texture_ref)
            if not os.path.exists(full_path):
                # If not in mod, check if it's referenced in vanilla .gfx
                if texture_ref not in self.vanilla_referenced_textures:
                    missing_textures.append(texture_ref)

        self.missing_count = len(missing_textures)

        if self.hoi4_path:
            msg = "Referenced textures that do not exist in mod or vanilla .gfx files:"
        else:
            msg = "Referenced textures that do not exist (vanilla not checked):"

        self._report(
            missing_textures,
            "✓ All referenced textures exist",
            msg,
        )

    def run_validations(self):
        self.validate_unused_textures()
        self.validate_missing_textures()

        # Add summary
        self._log_section("SUMMARY")
        self.log(f"  Total texture files in gfx/: {len(self.texture_files)}")
        self.log(
            f"  Texture references in mod .gfx files: {len(self.referenced_textures)}"
        )
        self.log(f"  Texture references in game files: {len(self.game_file_textures)}")
        if self.hoi4_path:
            self.log(
                f"  Texture references in vanilla .gfx files: {len(self.vanilla_referenced_textures)}"
            )
        self.log(f"  Unused texture files: {self.unused_count}")
        self.log(f"  Missing texture references: {self.missing_count}")

        if self.unused_count > 0:
            self.log(
                f"\n  {Colors.YELLOW if self.use_colors else ''}Note: Unused textures may be legacy files that can be removed to reduce mod size.{Colors.ENDC if self.use_colors else ''}"
            )

        if self.missing_count > 0:
            if self.hoi4_path:
                self.log(
                    f"  {Colors.YELLOW if self.use_colors else ''}Note: Missing textures are not found in mod, vanilla textures, or vanilla .gfx files.{Colors.ENDC if self.use_colors else ''}"
                )
            else:
                self.log(
                    f"  {Colors.YELLOW if self.use_colors else ''}Note: Missing textures check is incomplete. Use --hoi4-path to check vanilla .gfx files.{Colors.ENDC if self.use_colors else ''}"
                )
        self.log(f"{'='*80}")


def add_extra_args(parser):
    """Add extra command-line arguments specific to this validator."""
    parser.add_argument(
        "--hoi4-path",
        type=str,
        default=None,
        help="Path to Hearts of Iron IV installation (auto-detected if not provided)",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Find unused texture files in Millennium Dawn mod",
        extra_args_fn=add_extra_args,
    )
