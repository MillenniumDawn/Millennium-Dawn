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
                "Main Menu:\n1. Retrieve and generate goals.gfx\n2. Retrieve and generate event pictures\n3. Retrieve and generate MD_ideas.gfx. This also generates defence company entries.\n4. Retrieve and generate MD_parties_icons.gfx.\n5. Retrieve and generate intelligence agency icons\n6. Retrieve and generate MD_decisions.gfx\n7. Retrieve and generate Focus Title Bars (This also updates the titlebar_styles.txt file)\n8. Retrieve and generate MD_scripted_gui.gfx (scans scripted_gui/countries/<TAG>/)\n9. Retrieve and generate MD_decisions_desc.gfx (text icons from decisions/**/decision_text/)\n10. Retrieve and generate modifiericons_texticons.gfx (text icons from gfx/texticons/modifier_icons/)\nPlease enter the number of the option you'd like: "
            ).strip()

            if not selection_input:
                print(
                    f"{bcolors.WARNING}Input cannot be empty. Please enter a number between 1 and 10.{bcolors.RESET}\n"
                )
                continue

            selection = int(selection_input)
            if selection < 1 or selection > 10:
                print(
                    f"{bcolors.FAIL}Invalid selection: {bcolors.RESET}{bcolors.INFO}{selection}{bcolors.RESET}{bcolors.FAIL} is not an option. Please enter a number between 1 and 10.\n{bcolors.RESET}"
                )
                continue
            break
        except ValueError:
            print(
                f"{bcolors.WARNING}Invalid input. Please enter a number between 1 and 10.{bcolors.RESET}\n"
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
    elif selection == 8:
        generate_scripted_gui(mod_root)
    elif selection == 9:
        generate_decisions_desc(mod_root)
    elif selection == 10:
        generate_modifier_icons(mod_root)


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


def _print_merge_report(
    filename, new, changed, orphaned, deduped, written, conflicts=()
):
    print(
        f"{bcolors.OK}{filename}: {len(new)} new, {len(changed)} updated, "
        f"{len(deduped)} de-duplicated, {len(orphaned)} orphaned.{bcolors.RESET}"
    )
    if new:
        print(f"{bcolors.OK}  New: {_format_names(new)}{bcolors.RESET}")
    if changed:
        print(f"{bcolors.WARNING}  Updated: {_format_names(changed)}{bcolors.RESET}")
    if deduped:
        print(
            f"{bcolors.WARNING}  De-duplicated (removed extra name blocks): "
            f"{_format_names(deduped)}{bcolors.RESET}"
        )
    if conflicts:
        print(
            f"{bcolors.FAIL}  De-duplicated with TEXTURE MISMATCH (kept first block, "
            f"verify the survivor is the intended icon):{bcolors.RESET}"
        )
        for name, kept, dropped in conflicts:
            print(
                f"{bcolors.FAIL}    {name}: kept {kept} — dropped {dropped}{bcolors.RESET}"
            )
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
    A name defined by more than one spriteType block is consolidated to its first
    block (the extra blocks are removed); the survivor is still reconciled to the
    scanned texturefile, so the kept block ends up pointing at the current source.
    Duplicates whose dropped block pointed at a *different* texturefile than the
    survivor are collected separately so the report can flag the silent swap.
    Returns (new_names, changed_names, orphaned_names, deduped_names, written,
    deduped_conflicts) where deduped_conflicts is a list of
    (name, kept_texfile, dropped_texfile).
    """
    if path.exists():
        original = _read_lf(path)
        newline = _newline_of(original)
        original = original.replace("\r\n", "\n").replace("\r", "\n")
    else:
        original = f"{header}}}\n"
        newline = "\n"

    existing = {}
    dup_spans = []
    deduped_names = []
    deduped_conflicts = []
    for name, texfile, start, end in _parse_named_blocks(original):
        if not name:
            continue
        if name not in existing:
            existing[name] = (texfile, start, end)
        else:
            kept_texfile = existing[name][0]
            if texfile and kept_texfile and texfile != kept_texfile:
                deduped_conflicts.append((name, kept_texfile, texfile))
            line_start = original.rfind("\n", 0, start) + 1
            # Consume the whole physical line so a trailing inline comment after
            # the block's closing brace is removed with the block, not orphaned.
            line_end = original.find("\n", end)
            span_end = line_end + 1 if line_end != -1 else len(original)
            dup_spans.append((line_start, span_end))
            deduped_names.append(name)

    new_names = []
    changed_names = []
    splices = [(ls, se, "") for ls, se in dup_spans]
    for name in sorted(entries, key=lambda n: entries[n].lower()):
        texture_path = entries[name]
        if name in existing and name not in protected:
            old_texfile, start, end = existing[name]
            if old_texfile != texture_path:
                block = render(name, texture_path)
                core = block[1:] if block.startswith("\t") else block
                splices.append((start, end, core.rstrip("\n")))
                changed_names.append(name)
        elif name in existing:
            # Protected: the existing block points at a non-modifier_icons path
            # (e.g. a vanilla role icon) and must keep its current texturefile.
            # The new entry is still added below so the file lives in the .gfx.
            pass
        else:
            new_names.append(name)

    orphaned = sorted(set(existing) - set(entries) - set(protected))

    if splices:
        splices.sort(key=lambda s: s[0])
        pieces = []
        cursor = 0
        for start, end, replacement in splices:
            pieces.append(original[cursor:start])
            pieces.append(replacement)
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

    return (
        new_names,
        changed_names,
        orphaned,
        sorted(set(deduped_names)),
        written,
        deduped_conflicts,
    )


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
        # decision_text/ art is text-icon material handled by MD_decisions_desc.gfx
        # (option 9); scanning it here would emit dead GFX_decision_* duplicates.
        if "decision_text" in f.relative_to(scan_dir).parts:
            continue
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


# Text icons hand-placed directly in a country folder (not under decision_text/);
# left untouched by the scan so the merge does not report them as orphans.
DECISIONS_DESC_LOOSE = frozenset(
    {"GFX_AFG_menu1", "GFX_MAIN_arab_kabyle", "GFX_ISR_desctext_blockade"}
)


def generate_decisions_desc(mod_root):
    scan_dir = mod_root / "gfx" / "interface" / "decisions"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = [
        f
        for f in scan_images(scan_dir)
        if "decision_text" in f.relative_to(scan_dir).parts
    ]
    _describe_scan(files)

    print(f"{bcolors.OK}Generating MD_decisions_desc.gfx...{bcolors.RESET}")
    seen = set()
    entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        # Bare GFX_<stem>: these are text icons drawn via £<stem> in loc, which
        # strips only the GFX_ prefix. Never add a decision_ prefix here.
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
        interface_path(mod_root, "MD_decisions_desc.gfx"),
        entries,
        render,
        header="spriteTypes = {\n",
        protected=DECISIONS_DESC_LOOSE,
    )
    _print_merge_report("MD_decisions_desc.gfx", *result)
    print(f"\nMD_decisions_desc.gfx has been processed for {len(files)} text icons.")


# Modifier-texticon files that exist in the .gfx but point at non-modifier_icons
# paths. These must be protected from the orphan sweep: the role-icon entries
# (anti_tank, artillery, etc.) are vanilla faction/role references, and a
# future modifier_icons file with a matching stem (e.g. rocket_texticon.dds)
# must not be allowed to silently overwrite them.
MODIFIER_ICONS_EXTERNAL = frozenset(
    {
        "GFX_no_order_texticon",
        "GFX_pops",
        "GFX_anti_tank_texticon",
        "GFX_artillery_texticon",
        "GFX_anti_air_texticon",
        "GFX_rocket_texticon",
        "GFX_motorized_texticon",
        "GFX_amphibious_texticon",
        "GFX_light_tank_chassis_texticon",
        "GFX_medium_tank_chassis_texticon",
        "GFX_heavy_tank_chassis_texticon",
        "GFX_super_heavy_tank_chassis_texticon",
        "GFX_modern_tank_chassis_texticon",
        "GFX_amphibious_tank_chassis_texticon",
        "GFX_flame_texticon",
        "GFX_select_headquarters_texticon",
    }
)


def generate_modifier_icons(mod_root):
    scan_dir = mod_root / "gfx" / "texticons" / "modifier_icons"
    print(scan_dir)
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return
    files = scan_images(scan_dir)
    _describe_scan(files)

    out_path = interface_path(mod_root, "modifiericons_texticons.gfx")
    # Map texturefile -> existing GFX name in the .gfx, so files that are
    # already wired keep their existing GFX name (preserving any non-standard
    # suffixes used by older hand-rolled entries).
    existing_names_by_path = {}
    if out_path.exists():
        original = _read_lf(out_path)
        original = original.replace("\r\n", "\n").replace("\r", "\n")
        for nm, tx, _s, _e in _parse_named_blocks(original):
            if nm and tx:
                existing_names_by_path.setdefault(tx, nm)

    print(f"{bcolors.OK}Generating modifiericons_texticons.gfx...{bcolors.RESET}")
    seen = set()
    entries = {}
    for f in files:
        texture_path = rel_texture_path(f, mod_root)
        # Default: GFX_<full_stem>, matching the workshop "Modifier Icons"
        # submod convention. If a GFX block already exists for this texture
        # (including hand-rolled entries with a redundant `_texticon` suffix
        # in the GFX name), reuse its name so existing .gui / localisation
        # references keep resolving.
        name = existing_names_by_path.get(texture_path, f"GFX_{f.stem}")
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
        interface_path(mod_root, "modifiericons_texticons.gfx"),
        entries,
        render,
        header="spriteTypes = {\n",
        protected=MODIFIER_ICONS_EXTERNAL,
    )
    _print_merge_report("modifiericons_texticons.gfx", *result)
    print(
        f"\nmodifiericons_texticons.gfx has been processed for {len(files)} text icons."
    )


# --- Scripted-GUI sprite generation ---------------------------------------

SG_MANUAL_BEGIN = (
    "# === BEGIN MANUAL (hand-maintained: progressbars, effects, non-stem sprites) ==="
)
SG_MANUAL_END = "# === END MANUAL ==="
SG_GEN_BEGIN = (
    "# === BEGIN GENERATED (managed by gfx_entry_generator.py, do not edit) ==="
)
SG_GEN_END = "# === END GENERATED ==="


def _extract_manual_body(text):
    """Return the verbatim body between the MANUAL markers, or '' if absent."""
    s = text.find(SG_MANUAL_BEGIN)
    if s == -1:
        return ""
    s = text.find("\n", s)
    e = text.find(SG_MANUAL_END, s if s != -1 else 0)
    if s == -1 or e == -1:
        return ""
    line_start = text.rfind("\n", 0, e) + 1
    return text[s + 1 : line_start].strip("\n")


def _build_scripted_gui_text(per_tag, manual_body):
    parts = ["spriteTypes = {\n\n", f"\t{SG_MANUAL_BEGIN}\n"]
    if manual_body.strip():
        parts.append(f"{manual_body}\n")
    parts.append(f"\t{SG_MANUAL_END}\n\n\t{SG_GEN_BEGIN}\n")
    for tag in sorted(per_tag):
        parts.append(f"\n\t# {tag}\n")
        for name, tex in per_tag[tag]:
            parts.append(
                f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{tex}"\n\t}}\n'
            )
    parts.append(f"\n\t{SG_GEN_END}\n}}\n")
    return "".join(parts)


def generate_scripted_gui(mod_root):
    """Generate interface/MD_scripted_gui.gfx from gfx/interface/scripted_gui/countries/<TAG>/.

    Each TAG folder's images become GFX_<stem> sprites under a `# TAG` section in the
    GENERATED region. A hand-maintained MANUAL region (progressbars, effect sprites,
    anything a bare texturefile scan can't express) is preserved verbatim across runs.
    """
    scan_dir = mod_root / "gfx" / "interface" / "scripted_gui" / "countries"
    if not scan_dir.is_dir():
        print(f"{bcolors.FAIL}Directory does not exist: {scan_dir}{bcolors.RESET}")
        return

    seen = set()
    per_tag = {}
    total = 0
    for tag_dir in sorted(
        (p for p in scan_dir.iterdir() if p.is_dir()), key=lambda p: p.name
    ):
        rows = []
        for f in scan_images(tag_dir):
            # `_`-prefixed folders (e.g. _manual/) hold textures wired by hand in the
            # MANUAL region (progressbars, effect sprites); the scan skips them.
            if any(part.startswith("_") for part in f.relative_to(tag_dir).parts):
                continue
            name = f"GFX_{f.stem}"
            texture_path = rel_texture_path(f, mod_root)
            if check_duplicate(name, seen, texture_path):
                continue
            rows.append((name, texture_path))
            total += 1
        if rows:
            rows.sort(key=lambda r: r[0].lower())
            per_tag[tag_dir.name] = rows

    out = interface_path(mod_root, "MD_scripted_gui.gfx")
    original = _read_lf(out) if out.exists() else ""
    newline = _newline_of(original) if original else "\n"
    original = original.replace("\r\n", "\n").replace("\r", "\n")
    text = _build_scripted_gui_text(per_tag, _extract_manual_body(original))

    if text != original:
        _write_with_newline(out, text, newline)
        print(
            f"{bcolors.OK}MD_scripted_gui.gfx: {total} sprites across "
            f"{len(per_tag)} tags ({', '.join(sorted(per_tag))}).{bcolors.RESET}"
        )
    else:
        print(
            f"{bcolors.OK}MD_scripted_gui.gfx already up to date; no write performed.{bcolors.RESET}"
        )


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
