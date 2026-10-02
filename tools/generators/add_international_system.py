#!/usr/bin/env python3
"""Add a tab to the International Systems screen.

Wires the tab button, icon, open/close logic and header title into the shared
screen files, then writes a stub window, scripted GUI and English loc for the
new system. Build the system's content inside the generated stub files.

Usage:
    python tools/generators/add_international_system.py forums "Economic Forums" \
        --description "Track the world's economic forums." --after un --icon handshake

--icon takes a premade icon name (--list-icons) or an image with a transparent
background, such as a logo, and writes it in the tab style. Without it, the tool
expects a 28x27 icon at gfx/interface/scripted_gui/missiles/ledger_icon_small_<key>.dds.
--preview draws the resulting tab strip to a PNG and changes nothing else.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared.paths import REPO_ROOT
from shared_utils import atomic_write_bytes, read_text_strict

SCREEN_GUI = "interface/MD_countrymissilesview.gui"
SCREEN_GFX = "interface/MD_countrymissilesview.gfx"
SCREEN_SCRIPT = "common/scripted_guis/00_missiles_scripted_guis.txt"
TITLE_LOC = "common/scripted_localisation/01_international_scripted_localisation.txt"
ART_DIR = "gfx/interface/scripted_gui/missiles"

STRIP_WIDTH = 530
ICON_WIDTH = 28
WIDE_SPRITE = "GFX_missiles_gui_ledger_btn"
NARROW_SPRITE = "GFX_missiles_gui_ledger_btn_narrow"
# (sprite, frame width, step between tabs). The narrow frame drops the middle
# of the wide one; the step keeps the wide sprite's overlap.
LAYOUTS = ((WIDE_SPRITE, 90, 84), (NARROW_SPRITE, 68, 62))

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
BUTTON_NAME_RE = re.compile(r'name\s*=\s*"(\w+)_gui_ledger_button"')
FRAME_RE = re.compile(r"(\w+)_gui_ledger_button\s*=\s*\{\s*frame\s*=\s*(\w+)\s*\}")
TAB_CLEAR_RE = re.compile(r"^\t*clear_variable = var_open_MD_\w+_gui\n", re.M)
OPENER_RE = re.compile(r"set_variable = \{ (var_open_MD_\w+_gui) = 2 \}")
# Loc tokens whose case matters: [scope.Function], $key$, £sprite, §colour codes
# and backslash escapes such as \n.
LOC_TOKEN_RE = re.compile(r"(\[[^\]]*\]|\$[^$]*\$|£\w+|§.|\\.)")
LOC_KEY_RE = re.compile(r"^\s*([\w.]+):\d*\s", re.M)


class ToolError(Exception):
    pass


@dataclass
class Tab:
    key: str
    button: str
    icon: str


def find_block(text, header, start=0):
    """Return (start, end) of the brace block opened by `header`, end exclusive."""
    match = re.compile(header).search(text, start)
    if not match:
        raise ToolError(f"could not find {header!r}")
    depth = 0
    for index in range(text.index("{", match.start()), len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return match.start(), index + 1
    raise ToolError(f"unbalanced braces after {header!r}")


def line_start(text, index):
    return text.rfind("\n", 0, index) + 1


def element_blocks(text, kind):
    """Yield (start, end) for each top-level `kind = {` block in `text`."""
    pos = 0
    while True:
        match = re.compile(rf"\b{kind}\s*=\s*\{{").search(text, pos)
        if not match:
            return
        start, end = find_block(text, rf"\b{kind}\s*=\s*\{{", match.start())
        yield line_start(text, start), end
        pos = end


def choose_layout(count):
    for sprite, width, step in LAYOUTS:
        if (count - 1) * step + width <= STRIP_WIDTH:
            return sprite, width, step
    raise ToolError(
        f"{count} tabs do not fit the {STRIP_WIDTH}px strip; add a second row first"
    )


def set_x(block, x):
    return re.sub(r"position\s*=\s*\{\s*x\s*=\s*-?\d+", f"position = {{ x = {x}", block)


def layout_strip(gui, key, after):
    """Insert the new tab into the ledger strip and re-lay out every tab."""
    start, end = find_block(
        gui, r'containerWindowType\s*=\s*\{\s*name\s*=\s*"missiles_gui_ledger_menu"'
    )
    menu = gui[start:end]
    buttons = list(element_blocks(menu, "buttonType"))
    icons = [
        span
        for span in element_blocks(menu, "iconType")
        if "trade_divider" not in menu[span[0] : span[1]]
    ]
    if len(buttons) != len(icons):
        raise ToolError("ledger strip has a tab button without an icon")
    tabs = []
    for (b_start, b_end), (i_start, i_end) in zip(buttons, icons):
        name = BUTTON_NAME_RE.search(menu[b_start:b_end])
        if not name:
            raise ToolError("ledger strip has an unnamed tab button")
        tabs.append(Tab(name.group(1), menu[b_start:b_end], menu[i_start:i_end]))
    keys = [tab.key for tab in tabs]
    if key in keys:
        raise ToolError(f"tab {key!r} already exists")
    if after is not None and after not in keys:
        raise ToolError(f"--after {after!r} is not a tab; tabs are {', '.join(keys)}")

    indent = "\t\t\t"
    upper = key.upper()
    new_tab = Tab(
        key,
        f"{indent}buttonType = {{\n"
        f'{indent}\tname = "{key}_gui_ledger_button"\n'
        f"{indent}\tposition = {{ x = 0 y = 0 }}\n"
        f'{indent}\tquadTextureSprite ="{WIDE_SPRITE}"\n'
        f'{indent}\tpdx_tooltip = "{upper}_GUI_LEDGER_TT"\n'
        f'{indent}\tpdx_tooltip_delayed = "{upper}_GUI_LEDGER_TT_DELAYED"\n'
        f"{indent}\tclicksound = click_checkbox\n"
        f"{indent}}}",
        f"{indent}iconType = {{\n"
        f'{indent}\tname ="icon_{key}_gui_ledger"\n'
        f'{indent}\tspriteType = "GFX_ledger_icon_small_{key}"\n'
        f"{indent}\tposition = {{ x = 0 y = 12 }}\n"
        f"{indent}\talwaystransparent = yes\n"
        f"{indent}}}",
    )
    slot = keys.index(after) + 1 if after is not None else len(tabs)
    tabs.insert(slot, new_tab)

    sprite, width, step = choose_layout(len(tabs))
    blocks = []
    for index, tab in enumerate(tabs):
        x = index * step
        button = set_x(tab.button, x)
        button = re.sub(
            r'quadTextureSprite\s*=\s*"\w+"', f'quadTextureSprite ="{sprite}"', button
        )
        blocks.append(button)
        blocks.append(set_x(tab.icon, x + (width - ICON_WIDTH) // 2))
    head = menu[: buttons[0][0]]
    tail = menu[max(buttons[-1][1], icons[-1][1]) :]
    menu = head + "\n\n".join(blocks) + tail
    return gui[:start] + menu + gui[end:], [tab.key for tab in tabs], sprite


def wire_script(script, key, order, var):
    """Add the click handler, frame property and clears to MD_missiles_gui."""
    gui_start, gui_end = find_block(script, r"\bMD_missiles_gui\s*=\s*\{")
    body = script[gui_start:gui_end]
    frames = dict(FRAME_RE.findall(body))
    missing = [tab for tab in order if tab != key and tab not in frames]
    if missing:
        raise ToolError(f"no frame property for tab(s): {', '.join(missing)}")
    frames[key] = var

    eff_start, eff_end = find_block(body, r"\beffects\s*=\s*\{")
    effects = body[eff_start:eff_end]
    for tab in reversed(order):
        if tab == key:
            continue
        h_start, h_end = find_block(
            effects, rf"\b{tab}_gui_ledger_button_click\s*=\s*\{{"
        )
        handler = effects[h_start:h_end]
        clears = list(TAB_CLEAR_RE.finditer(handler))
        if clears:
            insert_at = clears[-1].end()
            indent = re.match(r"\t*", clears[-1].group(0)).group(0)
        else:
            insert_at = handler.index("\n") + 1
            indent = "\t\t\t\t"
        handler = (
            handler[:insert_at]
            + f"{indent}clear_variable = {var}\n"
            + handler[insert_at:]
        )
        effects = effects[:h_start] + handler + effects[h_end:]

    clears = "".join(
        f"\t\t\t\tclear_variable = {frames[tab]}\n" for tab in order if tab != key
    )
    handler = (
        f"\t\t\t{key}_gui_ledger_button_click = {{\n"
        f"\t\t\t\tset_variable = {{ {var} = 2 }}\n"
        f"{clears}"
        f"\t\t\t\tinternational_systems_update = yes\n"
        f"\t\t\t}}\n"
    )
    effects = insert_after_previous(
        effects, key, order, "_gui_ledger_button_click", handler
    )

    body = body[:eff_start] + effects + body[eff_end:]
    prop_start, prop_end = find_block(body, r"\bproperties\s*=\s*\{")
    properties = body[prop_start:prop_end]
    prop = f"\t\t\t{key}_gui_ledger_button = {{\n\t\t\t\tframe = {var}\n\t\t\t}}\n"
    properties = insert_after_previous(
        properties, key, order, "_gui_ledger_button", prop
    )
    body = body[:prop_start] + properties + body[prop_end:]
    return script[:gui_start] + body + script[gui_end:]


def insert_after_previous(block, key, order, suffix, new_text):
    """Insert `new_text` after the entry of the tab before the new one."""
    previous = order[order.index(key) - 1]
    _, end = find_block(block, rf"\b{previous}{suffix}\s*=\s*\{{")
    at = block.index("\n", end) + 1
    return block[:at] + new_text + block[at:]


def add_title(loc_script, key, var):
    name = re.search(r"\bname\s*=\s*name_of_menu\b", loc_script)
    if not name:
        raise ToolError("could not find the name_of_menu title dispatcher")
    start, end = find_block(
        loc_script,
        r"defined_text\s*=\s*\{",
        loc_script.rfind("defined_text", 0, name.start()),
    )
    block = loc_script[start:end]
    fallback = block.rfind("\ttext = {")
    branch = (
        "\ttext = {\n"
        "\t\ttrigger = {\n"
        f"\t\t\tcheck_variable = {{ {var} = 2 }}\n"
        "\t\t}\n"
        f"\t\tlocalization_key = IS_title_{key}\n"
        "\t}\n"
    )
    at = line_start(block, fallback)
    return loc_script[:start] + block[:at] + branch + block[at:] + loc_script[end:]


def add_sprites(gfx, key, sprite):
    icon = (
        "\tspriteType = {\n"
        f'\t\tname = "GFX_ledger_icon_small_{key}"\n'
        f'\t\ttexturefile = "{ART_DIR}/ledger_icon_small_{key}.dds"\n'
        "\t\tnoOfFrames = 1\n"
        "\t}\n"
    )
    last = [m.start() for m in re.finditer(r'name = "GFX_ledger_icon_small_\w+"', gfx)][
        -1
    ]
    _, end = find_block(gfx, r"spriteType\s*=\s*\{", gfx.rfind("spriteType", 0, last))
    at = gfx.index("\n", end) + 1
    gfx = gfx[:at] + icon + gfx[at:]
    if sprite == NARROW_SPRITE and f'"{NARROW_SPRITE}"' not in gfx:
        narrow = (
            "\tspriteType = {\n"
            f'\t\tname = "{NARROW_SPRITE}"\n'
            f'\t\ttexturefile = "{ART_DIR}/missiles_gui_ledger_btn_narrow.dds"\n'
            "\t\tnoOfFrames = 2\n"
            "\t}\n"
        )
        wide = gfx.index(f'"{WIDE_SPRITE}"')
        _, end = find_block(
            gfx, r"spriteType\s*=\s*\{", gfx.rfind("spriteType", 0, wide)
        )
        at = gfx.index("\n", end) + 1
        gfx = gfx[:at] + narrow + gfx[at:]
    return gfx


def make_narrow_sprite(repo):
    """Build the narrow tab sprite from the wide one, once."""
    from international_system_art import narrow_frames

    target = os.path.join(repo, ART_DIR, "missiles_gui_ledger_btn_narrow.dds")
    if os.path.exists(target):
        return None
    (_, wide, _), (_, narrow, _) = LAYOUTS
    narrow_frames(repo, wide, narrow).save(target)
    return f"{ART_DIR}/missiles_gui_ledger_btn_narrow.dds"


def resolve_icon(repo, key, icon):
    """Return the converted icon for --icon, or None to use the one on disk."""
    target = os.path.join(repo, ART_DIR, f"ledger_icon_small_{key}.dds")
    if icon is None:
        if not os.path.exists(target):
            raise ToolError(
                f"add the tab icon first ({ART_DIR}/ledger_icon_small_{key}.dds) or pass --icon"
            )
        return None
    if os.path.exists(target):
        raise ToolError(
            f"{ART_DIR}/ledger_icon_small_{key}.dds already exists; drop --icon to use it"
        )
    from international_system_art import PREMADE_ICONS, tab_icon

    if icon not in PREMADE_ICONS and not os.path.isfile(os.path.join(repo, icon)):
        raise ToolError(
            f"unknown icon {icon!r}: use a premade name (--list-icons) or an image path"
        )
    try:
        return tab_icon(repo, icon)
    except (OSError, ValueError) as error:
        raise ToolError(f"cannot use icon {icon!r}: {error}") from error


def write_preview(repo, key, gui, gfx, sprite, icon, preview):
    """Draw the new strip to `preview` without touching the repo."""
    from international_system_art import narrow_frames, render_strip
    from PIL import Image

    start, end = find_block(
        gui, r'containerWindowType\s*=\s*\{\s*name\s*=\s*"missiles_gui_ledger_menu"'
    )
    (_, wide, _), (_, narrow, _) = LAYOUTS
    art = os.path.join(repo, ART_DIR)
    if sprite == WIDE_SPRITE:
        frames, width = (
            Image.open(os.path.join(art, "missiles_gui_ledger_btn.dds")),
            wide,
        )
    elif os.path.exists(os.path.join(art, "missiles_gui_ledger_btn_narrow.dds")):
        frames = Image.open(os.path.join(art, "missiles_gui_ledger_btn_narrow.dds"))
        width = narrow
    else:
        frames, width = narrow_frames(repo, wide, narrow), narrow
    if icon is None:
        icon = Image.open(os.path.join(art, f"ledger_icon_small_{key}.dds"))
    strip = render_strip(
        repo,
        gui[start:end],
        gfx,
        frames.convert("RGBA"),
        width,
        key,
        icon.convert("RGBA"),
    )
    strip.save(preview)


def loc_value(text):
    """Quote-escape a localisation value; a newline cannot be written into one."""
    if "\n" in text or "\r" in text:
        raise ToolError("tab text must be a single line")
    if re.search(r"\\(?!n)", text):
        raise ToolError("the only backslash escape tab text may use is \\n")
    return text.replace('"', '\\"')


def stub_files(key, name, title, description, var):
    upper = key.upper()
    name, title, description = loc_value(name), loc_value(title), loc_value(description)
    gui = (
        "guiTypes = {\n"
        "\tcontainerWindowType = {\n"
        f'\t\tname = "MD_{key}_system_window"\n'
        "\t\tposition = { x = 20 y = 110 }\n"
        "\t\tsize = { width = 510 height = 700 }\n"
        "\n"
        "\t\tinstantTextboxType = {\n"
        f'\t\t\tname = "{key}_system_placeholder"\n'
        "\t\t\tposition = { x = 0 y = 0 }\n"
        '\t\t\tfont = "hoi_18mbs"\n'
        f'\t\t\ttext = "IS_{key}_placeholder"\n'
        "\t\t\tmaxWidth = 510\n"
        "\t\t\tmaxHeight = 30\n"
        "\t\t\tformat = left\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    script = (
        "scripted_gui = {\n"
        f"\tMD_{key}_system_gui = {{\n"
        f"\t\twindow_name = MD_{key}_system_window\n"
        "\t\tcontext_type = player_context\n"
        "\t\tparent_window_name = MD_countrymissilesview\n"
        "\n"
        "\t\tdirty = global.international_systems_updated\n"
        "\n"
        "\t\tvisible = {\n"
        f"\t\t\tcheck_variable = {{ {var} = 2 }}\n"
        "\t\t\thas_country_flag = open_MD_countrymissilesview\n"
        "\t\t}\n"
        "\n"
        "\t\tai_enabled = { always = no }\n"
        "\t}\n"
        "}\n"
    )
    loc = (
        "﻿l_english:\n"
        f' {upper}_GUI_LEDGER_TT: "§Y{name}§!"\n'
        f' {upper}_GUI_LEDGER_TT_DELAYED: "{description}"\n'
        f' IS_title_{key}: "{title}"\n'
        f' IS_{key}_placeholder: "{name}"\n'
    )
    return {
        f"interface/MD_international_{key}.gui": gui,
        f"common/scripted_guis/01_international_{key}_gui.txt": script,
        f"localisation/english/MD_international_{key}_l_english.yml": loc,
    }


def default_title(name):
    """Capitalise the name for the header, leaving loc tokens as written."""
    parts = LOC_TOKEN_RE.split(name)
    return "".join(
        part if index % 2 else part.upper() for index, part in enumerate(parts)
    )


def taken_loc_keys(repo, keys):
    """Return the keys already defined in English localisation."""
    folder = os.path.join(repo, "localisation", "english")
    taken = set()
    for folder_path, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".yml"):
                path = os.path.join(folder_path, file)
                taken.update(LOC_KEY_RE.findall(read_text_strict(path)))
    return sorted(set(keys) & taken)


def taken_gui_names(repo, key):
    """Return the stub's window and scripted GUI names that already exist."""
    window, gui = f"MD_{key}_system_window", f"MD_{key}_system_gui"
    taken = set()
    for folder, suffix, pattern, name in (
        ("interface", ".gui", rf'name\s*=\s*"{window}"', window),
        (os.path.join("common", "scripted_guis"), ".txt", rf"\b{gui}\s*=\s*\{{", gui),
    ):
        for folder_path, _, files in os.walk(os.path.join(repo, folder)):
            for file in files:
                path = os.path.join(folder_path, file)
                if file.endswith(suffix) and re.search(pattern, read_text_strict(path)):
                    taken.add(name)
    return sorted(taken)


def direct_openers(repo):
    """List script lines outside the ledger strip that open a tab directly."""
    found = []
    for folder, _, files in os.walk(os.path.join(repo, "common")):
        for file in files:
            path = os.path.join(folder, file)
            relative = os.path.relpath(path, repo).replace(os.sep, "/")
            if not file.endswith(".txt") or relative == SCREEN_SCRIPT:
                continue
            for number, line in enumerate(read_text_strict(path).splitlines(), 1):
                if OPENER_RE.search(line):
                    found.append((relative, number))
    return found


def add_system(
    repo, key, name, description, title=None, after=None, icon=None, preview=None
):
    if not KEY_RE.match(key):
        raise ToolError(f"key {key!r} must be lower_snake_case")
    new_icon = resolve_icon(repo, key, icon)
    var = f"var_open_MD_{key}_gui"
    files = {
        path: read_text_strict(os.path.join(repo, path), "utf-8")
        for path in (SCREEN_GUI, SCREEN_GFX, SCREEN_SCRIPT, TITLE_LOC)
    }
    stubs = stub_files(key, name, title or default_title(name), description, var)
    upper = key.upper()
    loc_keys = (
        f"{upper}_GUI_LEDGER_TT",
        f"{upper}_GUI_LEDGER_TT_DELAYED",
        f"IS_title_{key}",
        f"IS_{key}_placeholder",
    )
    taken = taken_loc_keys(repo, loc_keys)
    if taken:
        raise ToolError(f"loc key(s) already defined: {', '.join(taken)}")
    for path in stubs:
        if os.path.exists(os.path.join(repo, path)):
            raise ToolError(f"{path} already exists")
    taken = taken_gui_names(repo, key)
    if taken:
        raise ToolError(f"GUI name(s) already defined: {', '.join(taken)}")

    files[SCREEN_GUI], order, sprite = layout_strip(files[SCREEN_GUI], key, after)
    if re.search(rf"\b{var}\b", files[SCREEN_SCRIPT] + files[TITLE_LOC]):
        raise ToolError(f"{var} is already used by the screen")
    if f'"GFX_ledger_icon_small_{key}"' in files[SCREEN_GFX]:
        raise ToolError(f"sprite GFX_ledger_icon_small_{key} is already defined")
    files[SCREEN_SCRIPT] = wire_script(files[SCREEN_SCRIPT], key, order, var)
    files[TITLE_LOC] = add_title(files[TITLE_LOC], key, var)
    files[SCREEN_GFX] = add_sprites(files[SCREEN_GFX], key, sprite)
    files.update(stubs)
    openers = direct_openers(repo)
    if preview is not None:
        write_preview(
            repo, key, files[SCREEN_GUI], files[SCREEN_GFX], sprite, new_icon, preview
        )
        return [preview], order, openers
    written = sorted(files)
    if new_icon is not None:
        new_icon.save(os.path.join(repo, ART_DIR, f"ledger_icon_small_{key}.dds"))
        written.append(f"{ART_DIR}/ledger_icon_small_{key}.dds")
    if sprite == NARROW_SPRITE:
        narrow = make_narrow_sprite(repo)
        if narrow:
            written.append(narrow)
    for path, text in files.items():
        atomic_write_bytes(os.path.join(repo, path), text.encode("utf-8"))
    return written, order, openers


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("key", nargs="?", help="lower_snake_case id, e.g. forums")
    parser.add_argument(
        "name", nargs="?", help='tab tooltip name, e.g. "Economic Forums"'
    )
    parser.add_argument("--description", help="delayed tooltip text")
    parser.add_argument(
        "--title", help="screen header; defaults to the name in capitals"
    )
    parser.add_argument(
        "--after", help="existing tab key to place the new tab after; defaults to last"
    )
    parser.add_argument(
        "--icon",
        help="premade icon name or a transparent image path, converted to the tab style",
    )
    parser.add_argument(
        "--preview",
        metavar="PNG",
        help="draw the new tab strip here; write nothing else",
    )
    parser.add_argument(
        "--list-icons", action="store_true", help="print the premade icons as JSON"
    )
    args = parser.parse_args(argv)
    if args.list_icons:
        from international_system_art import icon_catalog

        print(json.dumps(icon_catalog(str(REPO_ROOT))))
        return 0
    if not (args.key and args.name and args.description):
        parser.error("key, name and --description are required")
    try:
        written, order, openers = add_system(
            str(REPO_ROOT),
            args.key,
            args.name,
            args.description,
            args.title,
            args.after,
            args.icon,
            args.preview,
        )
    except ToolError as error:
        sys.exit(f"ERROR: {error}")
    print(f"Tabs: {', '.join(order)}")
    for path in written:
        print(f"  wrote {path}")
    if openers:
        print(
            f"These lines open a tab directly; clear var_open_MD_{args.key}_gui there if the new tab can be open at the time:"
        )
        for path, number in openers:
            print(f"  {path}:{number}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
