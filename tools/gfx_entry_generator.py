#!/usr/bin/env python3
import re
from pathlib import Path

###########################
###
### HOI 4 GFX file generator by AngriestBird, originally for Millennium Dawn Mod
###
### Copyright (c) 2023 Ken McCormick (AngriestBird)
### Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
### The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###
### Works on Linux, macOS, and Windows. Run from anywhere inside the repo:
### usage: python3 tools/gfx_entry_generator.py
### Follow the prompts. Options 1-6 scan a gfx/ subfolder and merge the results into
### the matching interface/*.gfx file: unchanged entries are left byte-identical in
### place, and names no longer found on disk are reported as orphaned, never deleted.
###
###########################

IMAGE_EXTENSIONS = {".dds", ".png", ".tga"}

TITLEBAR_REL = "gfx/interface/focusview/titlebar"

GFX_BEGIN = (
    "# === BEGIN GENERATED JOINT TITLE BARS (managed by gfx_entry_generator.py) ==="
)
GFX_END = "# === END GENERATED JOINT TITLE BARS ==="
STYLE_BEGIN = "# === BEGIN GENERATED JOINT TITLE BAR STYLES (managed by gfx_entry_generator.py) ==="
STYLE_END = "# === END GENERATED JOINT TITLE BAR STYLES ==="

TITLEBAR_FILE_RE = re.compile(
    r"^focus_(unavailable|can_start|completed)_joint_(?P<suffix>.+)_bg\.dds$"
)
_JOINT_NAME_RE = re.compile(
    r"^GFX_focus_(unavailable|can_start|current|completed)_joint_(.+)$"
)
_COMMENT_LINE_RE = re.compile(r"^[ \t]*#.*$", re.MULTILINE)
_SPRITETYPE_RE = re.compile(r"[sS]priteType\s*=\s*\{")
_NAME_RE = re.compile(r'name\s*=\s*"([^"]+)"')
_TEXTUREFILE_RE = re.compile(r'texture[fF]ile\s*=\s*"([^"]+)"')
_TAG_HEADER_RE = re.compile(r"^#+\s*([A-Za-z0-9_]+)\s*#+$")


class bcolors:
    OK = "\033[92m"  # GREEN
    WARNING = "\033[93m"  # YELLOW
    FAIL = "\x1b[31;1m"  # RED
    RESET = "\033[0m"  # RESET COLOR
    INFO = "\x1b[33;25m"  # INFO COLOR


def main():
    mod_root = Path(__file__).resolve().parent.parent

    while True:
        try:
            selection_input = input(
                "Main Menu:\n1. Retrieve and generate goals.gfx\n2. Retrieve and generate event pictures\n3. Retrieve and generate MD_ideas.gfx. This also generates defence company entries.\n4. Retrieve and generate MD_parties_icons.gfx.\n5. Retrieve and generate intelligence agency icons\n6. Retrieve and generate MD_decisions.gfx\n7. Retrieve and generate Focus Title Bars (This also updates the titlebar_styles.txt file)\nPlease enter the number of the option you'd like: "
            ).strip()

            if not selection_input:
                print(
                    f"{bcolors.WARNING}Input cannot be empty. Please enter a number between 1 and 7.{bcolors.RESET}\n"
                )
                continue

            selection = int(selection_input)
            if selection < 1 or selection > 7:
                print(
                    f"{bcolors.FAIL}Invalid selection: {bcolors.RESET}{bcolors.INFO}{selection}{bcolors.RESET}{bcolors.FAIL} is not an option. Please enter a number between 1 and 7.\n{bcolors.RESET}"
                )
                continue
            break
        except ValueError:
            print(
                f"{bcolors.WARNING}Invalid input. Please enter a number between 1 and 7.{bcolors.RESET}\n"
            )
            continue

    if selection == 1:
        generate_goals(mod_root)
    elif selection == 2:
        generate_event_pictures(mod_root)
    elif selection == 3:
        generate_ideas(mod_root)
    elif selection == 4:
        generate_party_icons(mod_root)
    elif selection == 5:
        generate_intelligence_icons(mod_root)
    elif selection == 6:
        generate_decisions(mod_root)
    elif selection == 7:
        generate_focus_titlebars(mod_root)


# --- Filesystem scanning ----------------------------------------------------


def scan_images(scan_dir):
    """Recursively find image files under scan_dir, sorted case-insensitively by POSIX path."""
    files = [
        p
        for p in scan_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    files.sort(key=lambda p: p.as_posix().lower())
    return files


def rel_texture_path(file_path, mod_root):
    return file_path.relative_to(mod_root).as_posix()


def interface_path(mod_root, filename):
    return mod_root / "interface" / filename


def check_duplicate(name, seen_names, texture_path):
    """Check if a sprite name has already been seen this run. Returns True if duplicate."""
    if name in seen_names:
        print(
            f"{bcolors.WARNING}WARNING: Duplicate icon name '{name}' "
            f"from file '{texture_path}'. Skipping.{bcolors.RESET}"
        )
        return True
    seen_names.add(name)
    return False


def _describe_scan(files):
    png = sum(1 for f in files if f.suffix.lower() == ".png")
    tga = sum(1 for f in files if f.suffix.lower() == ".tga")
    print(
        f"{bcolors.OK}There are {bcolors.RESET}{len(files)}"
        f"{bcolors.OK} .dds, .png or .tga files available in this directory{bcolors.RESET}\n"
    )
    print(f"There are {png} that are PNG.\nThere are {tga} that are TGA.\n")


# --- Generic spriteType block parsing and merging ---------------------------


def _match_brace(text, open_idx):
    depth = 0
    i = open_idx
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError(f"Unmatched opening brace at offset {open_idx}")


def _parse_named_blocks(text):
    """Yield (name, texturefile, start, end) for every spriteType block in text."""
    for m in _SPRITETYPE_RE.finditer(text):
        open_idx = m.end() - 1
        try:
            end = _match_brace(text, open_idx) + 1
        except ValueError:
            continue
        nm = _NAME_RE.search(text, m.start(), end)
        tx = _TEXTUREFILE_RE.search(text, m.start(), end)
        yield nm.group(1) if nm else None, tx.group(1) if tx else None, m.start(), end


def _format_names(names, cap=30):
    names = sorted(names)
    if len(names) <= cap:
        return ", ".join(names)
    return f"{', '.join(names[:cap])}, +{len(names) - cap} more"


def _print_merge_report(filename, new, changed, orphaned, written):
    print(
        f"{bcolors.OK}{filename}: {len(new)} new, {len(changed)} updated, "
        f"{len(orphaned)} orphaned.{bcolors.RESET}"
    )
    if new:
        print(f"{bcolors.OK}  New: {_format_names(new)}{bcolors.RESET}")
    if changed:
        print(f"{bcolors.WARNING}  Updated: {_format_names(changed)}{bcolors.RESET}")
    if orphaned:
        print(
            f"{bcolors.INFO}  Orphaned (referenced in {filename}, missing on disk, left untouched): "
            f"{_format_names(orphaned)}{bcolors.RESET}"
        )
    if not written:
        print(
            f"{bcolors.OK}  {filename} already up to date; no write performed.{bcolors.RESET}"
        )


def merge_gfx_entries(path, entries, render, header="", protected=frozenset()):
    """Merge freshly scanned name -> texture_path entries into an existing spriteTypes .gfx file.

    Entries already present with an unchanged texturefile are left byte-identical in
    place. Entries whose texturefile changed are replaced in place. Names not yet
    present are appended, sorted, before the final closing brace. Names present on
    disk but no longer produced by the scan are reported as orphaned and never removed.
    Returns (new_names, changed_names, orphaned_names, written).
    """
    if path.exists():
        original = _read_lf(path)
        newline = _newline_of(original)
        original = original.replace("\r\n", "\n").replace("\r", "\n")
    else:
        original = f"{header}}}\n"
        newline = "\n"

    existing = {}
    for name, texfile, start, end in _parse_named_blocks(original):
        if name and name not in existing:
            existing[name] = (texfile, start, end)

    new_names = []
    changed_names = []
    edits = []
    for name in sorted(entries, key=lambda n: entries[n].lower()):
        texture_path = entries[name]
        if name in existing:
            old_texfile, start, end = existing[name]
            if old_texfile != texture_path:
                edits.append((start, end, render(name, texture_path)))
                changed_names.append(name)
        else:
            new_names.append(name)

    orphaned = sorted(set(existing) - set(entries) - set(protected))

    if edits:
        edits.sort(key=lambda e: e[0])
        pieces = []
        cursor = 0
        for start, end, full_block in edits:
            core = full_block[1:] if full_block.startswith("\t") else full_block
            pieces.append(original[cursor:start])
            pieces.append(core.rstrip("\n"))
            cursor = end
        pieces.append(original[cursor:])
        text = "".join(pieces)
    else:
        text = original

    if new_names:
        insert_at = text.rfind("}")
        appended = "".join(render(name, entries[name]) for name in new_names)
        text = text[:insert_at] + appended + text[insert_at:]

    written = text != original
    if written:
        _write_with_newline(path, text, newline)

    return new_names, changed_names, orphaned, written


# --- Content generators -------------------------------------------------


def generate_goals(mod_root, gfxbool=None):
    scan_dir = mod_root / "gfx" / "interface" / "goals"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = scan_images(scan_dir)
    _describe_scan(files)

    if gfxbool is None:
        while True:
            try:
                gfxbool_input = input(
                    'Would you like me to append "GFX_" to the front of the icon?\n1 for yes, 0 for no.\n'
                ).strip()

                if not gfxbool_input:
                    print(
                        f"{bcolors.WARNING}Input cannot be empty. Please enter 1 or 0.{bcolors.RESET}\n"
                    )
                    continue

                gfxbool = int(gfxbool_input)
                if gfxbool not in (0, 1):
                    print(
                        f"{bcolors.WARNING}Please enter either 1 or 0.{bcolors.RESET}\n"
                    )
                    continue
                break
            except ValueError:
                print(
                    f"{bcolors.WARNING}Invalid input. Please enter 1 or 0.{bcolors.RESET}\n"
                )
                continue

    prefix = "GFX_" if gfxbool == 1 else ""

    seen = set()
    entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        name = f"{prefix}{f.stem}"
        if check_duplicate(name, seen, texture_path):
            continue
        entries[name] = texture_path

    def render(name, texture_path):
        return (
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{texture_path}"\n'
            "\t}\n"
        )

    header = (
        "spriteTypes = {\n"
        "\t#Vanilla DO NOT DELETE\n"
        '\tspriteType = {\n\t\tname = "GFX_goal_unknown"\n\t\ttexturefile = "gfx/interface/goals/goal_unknown.dds"\n\t\tlegacy_lazy_load = no\n\t}\n'
    )

    print(f"{bcolors.OK}Generating goals.gfx...{bcolors.RESET}\n")
    result = merge_gfx_entries(
        interface_path(mod_root, "goals.gfx"),
        entries,
        render,
        header=header,
        protected={"GFX_goal_unknown"},
    )
    _print_merge_report("goals.gfx", *result)

    seen_shine = set()
    shine_entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        name = f"{prefix}{f.stem}_shine"
        if check_duplicate(name, seen_shine, texture_path):
            continue
        shine_entries[name] = texture_path

    def render_shine(name, texture_path):
        return (
            f'\tspriteType = {{ \n\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{texture_path}"\n'
            '\t\teffectfile = "gfx/FX/buttonstate.lua"\n'
            "\t\tanimation = {\n"
            f'\t\t\tanimationmaskfile = "{texture_path}"\n'
            '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n'
            "\t\t\tanimationrotation = -90.0\n"
            "\t\t\tanimationlooping = no\n"
            "\t\t\tanimationtime = 0.75\n"
            "\t\t\tanimationdelay = 0\n"
            '\t\t\tanimationblendmode = "add"\n'
            '\t\t\tanimationtype = "scrolling"\n'
            "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
            "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
            "\t\t}\n"
            "\t\tanimation = {\n"
            f'\t\t\tanimationmaskfile = "{texture_path}"\n'
            '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n'
            "\t\t\tanimationrotation = 90.0\n"
            "\t\t\tanimationlooping = no\n"
            "\t\t\tanimationtime = 0.75\n"
            "\t\t\tanimationdelay = 0\n"
            '\t\t\tanimationblendmode = "add"\n'
            '\t\t\tanimationtype = "scrolling"\n'
            "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
            "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
            "\t\t}\n"
            "\t\tlegacy_lazy_load = no\n"
            "\t}\n"
        )

    shine_header = (
        "spriteTypes = {\n"
        "\t#Vanilla DO NOT DELETE \n"
        '\tspriteType = {\n\t\tname = "GFX__shine"\n\t\ttexturefile = "gfx/interface/goals/goal_unknown.dds"\n'
        '\t\teffectFile = "gfx/FX/buttonstate.lua"\n\t\tanimation = {\n'
        '\t\t\tanimationmaskfile = "gfx/interface/goals/goal_unknown.dds"\n'
        '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n'
        "\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n"
        "\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n"
        '\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\n\t\tanimation = {\n"
        '\t\t\tanimationmaskfile = "gfx/interface/goals/goal_unknown.dds"\n'
        '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n'
        "\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n"
        "\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n"
        '\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n"
    )

    print(f"{bcolors.OK}Generating goals_shine.gfx...{bcolors.RESET}\n")
    result_shine = merge_gfx_entries(
        interface_path(mod_root, "goals_shine.gfx"),
        shine_entries,
        render_shine,
        header=shine_header,
        protected={"GFX__shine"},
    )
    _print_merge_report("goals_shine.gfx", *result_shine)

    print(
        f"\ngoals.gfx and goals_shine.gfx have been processed for {len(files)} icons."
    )


def generate_event_pictures(mod_root):
    scan_dir = mod_root / "gfx" / "event_pictures"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = scan_images(scan_dir)
    _describe_scan(files)

    print(f"{bcolors.OK}Generating MD_eventpictures.gfx...{bcolors.RESET}")
    seen = set()
    entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        stem = f.stem
        name = stem if "GFX_" in stem else f"GFX_{stem}"
        if check_duplicate(name, seen, texture_path):
            continue
        entries[name] = texture_path

    def render(name, texture_path):
        return (
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{texture_path}"\n'
            "\t}\n"
        )

    result = merge_gfx_entries(
        interface_path(mod_root, "MD_eventpictures.gfx"),
        entries,
        render,
        header="spriteTypes = {\n",
    )
    _print_merge_report("MD_eventpictures.gfx", *result)
    print(f"\nMD_eventpictures.gfx has been processed for {len(files)} event pictures.")


def generate_ideas(mod_root):
    scan_dir = mod_root / "gfx" / "interface" / "ideas"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = scan_images(scan_dir)
    _describe_scan(files)

    print(f"{bcolors.OK}Generating MD_ideas.gfx...{bcolors.RESET}")
    seen = set()
    entries = {}
    for f in files:
        if "traits_strip" in f.stem:
            print("Utility Idea GFX... skipping")
            continue
        texture_path = rel_texture_path(f, mod_root)
        util = f.stem
        if "idea_" in util:
            util = util.replace("idea_", "")
        name = f"GFX_idea_{util}"
        if check_duplicate(name, seen, texture_path):
            continue
        entries[name] = texture_path

    def render(name, texture_path):
        return (
            "\tspriteType ={\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{texture_path}"\n'
            "\t}\n"
        )

    header = (
        "spriteTypes = {\n"
        '\n\t## DO NOT REMOVE\n\tspriteType={\n\t\tname = "GFX_idea_traits_strip"\n'
        '\t\ttexturefile = "gfx/interface/ideas/idea_traits_strip.dds"\n\t\tnoOfFrames = 18\n\t}\n'
    )

    result = merge_gfx_entries(
        interface_path(mod_root, "MD_ideas.gfx"),
        entries,
        render,
        header=header,
        protected={"GFX_idea_traits_strip"},
    )
    _print_merge_report("MD_ideas.gfx", *result)
    print(f"\nMD_ideas.gfx has been processed for {len(files)} idea pictures.")


def generate_party_icons(mod_root):
    scan_dir = mod_root / "gfx" / "texticons" / "parties_icons"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = scan_images(scan_dir)
    _describe_scan(files)

    print(f"{bcolors.OK}Generating MD_parties_icons.gfx...{bcolors.RESET}")
    seen = set()
    entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        name = f"GFX_{f.stem}"
        if check_duplicate(name, seen, texture_path):
            continue
        entries[name] = texture_path

    def render(name, texture_path):
        return (
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{texture_path}"\n'
            "\t\tlegacy_lazy_load = no\n"
            "\t}\n"
        )

    result = merge_gfx_entries(
        interface_path(mod_root, "MD_parties_icons.gfx"),
        entries,
        render,
        header="spriteTypes = {\n",
    )
    _print_merge_report("MD_parties_icons.gfx", *result)
    print(f"\nMD_parties_icons.gfx has been processed for {len(files)} party icons.")


def generate_intelligence_icons(mod_root):
    scan_dir = mod_root / "gfx" / "interface" / "operatives" / "agencies"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = scan_images(scan_dir)
    _describe_scan(files)

    print(f"{bcolors.OK}Generating MD_intelligence_icons.gfx...{bcolors.RESET}")
    agency_prefix = "agency_logo_"
    seen = set()
    entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        stem = f.stem
        tag = stem[len(agency_prefix) :] if stem.startswith(agency_prefix) else stem
        name = f"GFX_intelligence_agency_logo_{tag}"
        if check_duplicate(name, seen, texture_path):
            continue
        entries[name] = texture_path

    def render(name, texture_path):
        return (
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{texture_path}"\n'
            "\t\tnoOfFrames = 2\n"
            "\t}\n"
        )

    result = merge_gfx_entries(
        interface_path(mod_root, "MD_intelligence_icons.gfx"),
        entries,
        render,
        header="spriteTypes = {\n",
    )
    _print_merge_report("MD_intelligence_icons.gfx", *result)
    print(
        f"\nMD_intelligence_icons.gfx has been processed for {len(files)} intelligence agencies."
    )


DECISION_SELF_PREFIXED = (
    "decision_category_",
    "decision_",
    "decisions_category_",
    "decisions_",
)


def generate_decisions(mod_root):
    scan_dir = mod_root / "gfx" / "interface" / "decisions"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = scan_images(scan_dir)
    _describe_scan(files)

    print(f"{bcolors.OK}Generating MD_decisions.gfx...{bcolors.RESET}")
    seen = set()
    entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        stem = f.stem
        if any(prefix in stem for prefix in DECISION_SELF_PREFIXED):
            name = f"GFX_{stem}"
        else:
            name = f"GFX_decision_{stem}"
        if check_duplicate(name, seen, texture_path):
            continue
        entries[name] = texture_path

    def render(name, texture_path):
        return (
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{texture_path}"\n'
            "\t}\n\n"
        )

    result = merge_gfx_entries(
        interface_path(mod_root, "MD_decisions.gfx"),
        entries,
        render,
        header="spriteTypes = {\n\n\t### categories\n\n\n",
    )
    _print_merge_report("MD_decisions.gfx", *result)
    print(f"\nMD_decisions.gfx has been processed for {len(files)} decision pictures.")


# --- Focus title-bar generation -------------------------------------------


def _titlebar_tex(state, suffix):
    return f"{TITLEBAR_REL}/focus_{state}_joint_{suffix}_bg.dds"


def _basic_sprite(state, suffix):
    name = f"GFX_focus_{state}_joint_{suffix}"
    return (
        "\tspriteType = {\n"
        f'\t\tname = "{name}"\n'
        f'\t\ttextureFile = "{_titlebar_tex(state, suffix)}"\n'
        "\t}\n"
    )


def _current_sprite(suffix):
    # current reuses the can_start background and overlays the ongoing animation.
    return (
        "\tSpriteType = {\n"
        f'\t\tname = "GFX_focus_current_joint_{suffix}"\n'
        f'\t\ttexturefile = "{_titlebar_tex("can_start", suffix)}"\n'
        '\t\teffectFile = "gfx/FX/buttonstate_onlydisable.lua"\n'
        "\t\tanimation = {\n"
        f'\t\t\tanimationmaskfile = "{TITLEBAR_REL}/focus_ongoing_mask2.dds"\n'
        f'\t\t\tanimationtexturefile = "{TITLEBAR_REL}/focus_ongoing_texture.dds"\n'
        "\t\t\tanimationrotation = -90.0\n"
        "\t\t\tanimationlooping = yes\n"
        "\t\t\tanimationtime = 20.0\n"
        "\t\t\tanimationdelay = 0.2\n"
        '\t\t\tanimationblendmode = "add"\n'
        '\t\t\tanimationtype = "rotating"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
        "\t\t}\n"
        "\t\tanimation = {\n"
        f'\t\t\tanimationmaskfile = "{TITLEBAR_REL}/focus_ongoing_mask4.dds"\n'
        f'\t\t\tanimationtexturefile = "{TITLEBAR_REL}/focus_ongoing_texture.dds"\n'
        "\t\t\tanimationrotation = 90.0\n"
        "\t\t\tanimationlooping = yes\n"
        "\t\t\tanimationtime = 15.0\n"
        "\t\t\tanimationdelay = 0.2\n"
        '\t\t\tanimationblendmode = "add"\n'
        '\t\t\tanimationtype = "rotating_ccw"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
        "\t\t}\n"
        "\t\tlegacy_lazy_load = no\n"
        "\t}\n"
    )


def _completed_sprite(suffix):
    return (
        "\tSpriteType = {\n"
        f'\t\tname = "GFX_focus_completed_joint_{suffix}"\n'
        f'\t\ttexturefile = "{_titlebar_tex("completed", suffix)}"\n'
        '\t\teffectFile = "gfx/FX/buttonstate_onlydisable.lua"\n'
        "\t\tanimation = {\n"
        f'\t\t\tanimationmaskfile = "{TITLEBAR_REL}/focus_completed_mask.dds"\n'
        f'\t\t\tanimationtexturefile = "{TITLEBAR_REL}/focus_completed_texture.dds"\n'
        "\t\t\tanimationrotation = 0.0\n"
        "\t\t\tanimationlooping = yes\n"
        "\t\t\tanimationtime = 26.0\n"
        "\t\t\tanimationdelay = 0.0\n"
        '\t\t\tanimationblendmode = "add"\n'
        '\t\t\tanimationtype = "scrolling"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
        "\t\t}\n"
        "\t\tlegacy_lazy_load = no\n"
        "\t}\n"
    )


def _set_block(suffix, present):
    parts = [f"\t### {suffix} ###\n"]
    if "unavailable" in present:
        parts.append(_basic_sprite("unavailable", suffix))
    if "can_start" in present:
        parts.append(_basic_sprite("can_start", suffix))
        parts.append("\n")
        parts.append(_current_sprite(suffix))
    if "completed" in present:
        parts.append("\n")
        parts.append(_completed_sprite(suffix))
    return "".join(parts)


def _style_block(suffix):
    return (
        "style = {\n"
        f"\tname = JOINT_{suffix}_focus_style\n"
        "\n"
        f"\tunavailable = GFX_focus_unavailable_joint_{suffix}\n"
        f"\tcompleted = GFX_focus_completed_joint_{suffix}\n"
        f"\tavailable = GFX_focus_can_start_joint_{suffix}\n"
        f"\tcurrent = GFX_focus_current_joint_{suffix}\n"
        "}\n"
    )


def _read_lf(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _newline_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def _write_with_newline(path, text, newline):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline == "\r\n":
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _remove_block_by_name(text, name):
    needle = f'name = "{name}"'
    idx = text.find(needle)
    if idx == -1:
        return text, False
    kw = max(text.rfind("spriteType", 0, idx), text.rfind("SpriteType", 0, idx))
    if kw == -1:
        return text, False
    line_start = text.rfind("\n", 0, kw) + 1
    open_idx = text.index("{", kw)
    try:
        end = _match_brace(text, open_idx) + 1
    except ValueError:
        return text, False
    if end < len(text) and text[end] == "\n":
        end += 1
    return text[:line_start] + text[end:], True


def _remove_tag_headers(text, suffixes):
    suffix_set = set(suffixes)
    kept = []
    for line in text.split("\n"):
        m = _TAG_HEADER_RE.match(line.strip())
        if m and m.group(1) in suffix_set:
            continue
        kept.append(line)
    return "\n".join(kept)


def _strip_region(text, begin, end):
    s = text.find(begin)
    if s == -1:
        return text
    line_start = text.rfind("\n", 0, s) + 1
    e = text.find(end, s)
    if e == -1:
        # END marker absent: strip from BEGIN to EOF to prevent double-BEGIN on next run.
        return text[:line_start]
    e += len(end)
    if e < len(text) and text[e] == "\n":
        e += 1
    return text[:line_start] + text[e:]


def _collapse_blanks(text):
    return re.sub(r"\n{3,}", "\n\n", text)


def generate_focus_titlebars(mod_root):
    titlebar_dir = mod_root / "gfx" / "interface" / "focusview" / "titlebar"
    gfx_file = mod_root / "interface" / "nationalfocusview.gfx"
    styles_file = mod_root / "common" / "national_focus" / "00_titlebar_styles.txt"

    if not titlebar_dir.is_dir():
        print(
            f"{bcolors.FAIL}Titlebar directory not found: {titlebar_dir}{bcolors.RESET}"
        )
        return
    for required in (gfx_file, styles_file):
        if not required.is_file():
            print(f"{bcolors.FAIL}Missing file: {required}{bcolors.RESET}")
            return

    # 1. Discover sets from the source .dds files.
    folder = {}
    for fn in (p.name for p in titlebar_dir.iterdir()):
        m = TITLEBAR_FILE_RE.match(fn)
        if m:
            folder.setdefault(m.group("suffix"), set()).add(m.group(1))

    # 2. Parse existing joint entries in the .gfx.
    gfx_text = _read_lf(gfx_file)
    gfx_nl = _newline_of(gfx_text)
    gfx_text = gfx_text.replace("\r\n", "\n").replace("\r", "\n")

    existing = {}
    for nm, tx, _start, _end in _parse_named_blocks(_COMMENT_LINE_RE.sub("", gfx_text)):
        if not nm:
            continue
        mm = _JOINT_NAME_RE.match(nm)
        if mm:
            existing.setdefault(mm.group(2), {})[mm.group(1)] = tx

    def is_regular(suffix, states):
        for st in ("unavailable", "can_start", "completed"):
            if st in states and states[st] != _titlebar_tex(st, suffix):
                return False
        if "current" in states and states["current"] != _titlebar_tex(
            "can_start", suffix
        ):
            return False
        return bool(states)

    regular_existing = {s for s, st in existing.items() if is_regular(s, st)}
    irregular_existing = sorted(set(existing) - regular_existing)
    managed = sorted(set(folder) | regular_existing)

    def present_states(suffix):
        p = set(folder.get(suffix, set()))
        ex = existing.get(suffix, {})
        for st in ("unavailable", "can_start", "completed"):
            if st in ex:
                p.add(st)
        if "current" in ex:
            p.add("can_start")
        return p

    # 3. Build the managed .gfx block; skip sets without a can_start source.
    blocks = []
    skipped = set()
    incomplete = []
    for suffix in managed:
        present = present_states(suffix)
        if "can_start" not in present:
            skipped.add(suffix)
            continue
        if present != {"unavailable", "can_start", "completed"}:
            incomplete.append(suffix)
        blocks.append(_set_block(suffix, present))
    emitted = [s for s in managed if s not in skipped]
    body = "\n\n".join(b.rstrip("\n") for b in blocks)
    managed_gfx = f"{GFX_BEGIN}\n\n{body}\n\n{GFX_END}\n"

    # 4. Read and parse styles_file before writing anything, so a read failure
    # does not leave gfx_file already overwritten with no rollback.
    styles_text = _read_lf(styles_file)
    styles_nl = _newline_of(styles_text)
    styles_text = styles_text.replace("\r\n", "\n").replace("\r", "\n")
    styles_text_stripped = _strip_region(styles_text, STYLE_BEGIN, STYLE_END)
    styled = set(
        re.findall(
            r"available\s*=\s*GFX_focus_can_start_joint_(\S+)", styles_text_stripped
        )
    )
    need_style = [s for s in emitted if s not in styled]
    if need_style:
        style_body = "\n\n".join(_style_block(s).rstrip("\n") for s in need_style)
        managed_styles = f"{STYLE_BEGIN}\n\n{style_body}\n\n{STYLE_END}\n"
        styles_text_out = styles_text_stripped.rstrip("\n") + "\n\n" + managed_styles
    else:
        styles_text_out = styles_text_stripped
    styles_text_out = _collapse_blanks(styles_text_out)

    # 5. All source data is ready — now write both files.
    gfx_text = _strip_region(gfx_text, GFX_BEGIN, GFX_END)
    removed = 0
    for suffix in emitted:
        for state in ("unavailable", "can_start", "current", "completed"):
            nm = f"GFX_focus_{state}_joint_{suffix}"
            while True:
                gfx_text, ok = _remove_block_by_name(gfx_text, nm)
                if not ok:
                    break
                removed += 1
    gfx_text = _remove_tag_headers(gfx_text, emitted)
    gfx_text = _collapse_blanks(gfx_text)

    insert_at = gfx_text.rfind("}")
    head = gfx_text[:insert_at].rstrip("\n")
    tail = gfx_text[insert_at:]
    gfx_text = f"{head}\n\n{managed_gfx}{tail}"
    _write_with_newline(gfx_file, gfx_text, gfx_nl)
    _write_with_newline(styles_file, styles_text_out, styles_nl)

    # 6. Report.
    print(
        f"{bcolors.OK}Title bars: {len(emitted)} managed set(s); "
        f"{removed} spriteType block(s) consolidated; "
        f"{len(need_style)} new style(s) added.{bcolors.RESET}"
    )
    if need_style:
        print(f"{bcolors.OK}New styles: {', '.join(need_style)}{bcolors.RESET}")
    if incomplete:
        print(
            f"{bcolors.WARNING}Incomplete sets (missing a state): "
            f"{', '.join(incomplete)}{bcolors.RESET}"
        )
    if skipped:
        print(
            f"{bcolors.FAIL}Skipped (no can_start source): "
            f"{', '.join(sorted(skipped))}{bcolors.RESET}"
        )
    if irregular_existing:
        print(
            f"{bcolors.INFO}Left untouched (irregular, hand-authored): "
            f"{', '.join(irregular_existing)}{bcolors.RESET}"
        )


if __name__ == "__main__":
    main()
