"""Tests for the vanilla-override downgrade in validate_gfx_references.

An undefined sprite ref in a .gui file is an ERROR, except in a vanilla-override
file (its own dead vanilla refs) or an MD-authored nation variant that inherits
a ref from the specific vanilla file it copies. The downgrade must be tied to
that parent file — a genuinely broken MD ref that merely shares a name with an
unrelated vanilla dead ref elsewhere in the repo must stay an ERROR.
"""

import os

from validate_gfx_references import (
    GfxReferenceValidator,
    Severity,
    _vanilla_parent_basename,
)

# Real vanilla designer GUIs (present in vanilla_gui_files.txt); the `_isr`
# variant basename is MD-authored (absent from the manifest).
VANILLA_BASE = "tank_chassis_super_heavy_tank.gui"
MD_VARIANT = "tank_chassis_super_heavy_tank_isr.gui"


def _validator(tmp_path):
    v = GfxReferenceValidator(str(tmp_path), use_colors=False)
    v._vanilla_defs_loaded = True
    return v


def _iface(tmp_path, basename):
    return os.path.join(str(tmp_path), "interface", basename)


def _severity_by_file(v):
    return {os.path.basename(i.file): i.severity for i in v._issues}


def test_vanilla_parent_basename_resolves_variant():
    assert _vanilla_parent_basename("a/b/" + MD_VARIANT) == VANILLA_BASE


def test_vanilla_parent_basename_none_for_unrelated_md_file():
    assert _vanilla_parent_basename("a/b/MD_unique_feature.gui") is None
    assert _vanilla_parent_basename("a/b/nounderscore.gui") is None


def test_inherited_ref_from_parent_is_downgraded(tmp_path):
    v = _validator(tmp_path)
    sprite = "GFX_dead_vanilla_ref"
    refs = [
        (sprite, _iface(tmp_path, VANILLA_BASE), 10),
        (sprite, _iface(tmp_path, MD_VARIANT), 20),
    ]
    v._check_undefined_refs(
        refs,
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    sev = _severity_by_file(v)
    assert sev[VANILLA_BASE] == Severity.WARNING
    assert sev[MD_VARIANT] == Severity.WARNING


def test_coincidental_ref_in_unrelated_md_file_stays_error(tmp_path):
    # Same dead sprite name appears in a vanilla-override file, but the MD file
    # is not a variant of it — the old repo-wide downgrade wrongly silenced this.
    v = _validator(tmp_path)
    sprite = "GFX_dead_vanilla_ref"
    refs = [
        (sprite, _iface(tmp_path, VANILLA_BASE), 10),
        (sprite, _iface(tmp_path, "MD_unique_feature.gui"), 20),
    ]
    v._check_undefined_refs(
        refs,
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    sev = _severity_by_file(v)
    assert sev[VANILLA_BASE] == Severity.WARNING
    assert sev["MD_unique_feature.gui"] == Severity.ERROR


def test_variant_ref_not_carried_by_parent_stays_error(tmp_path):
    # The MD file is a variant of a real vanilla file, but the parent does not
    # reference this sprite — so it is not inherited and must stay an ERROR.
    v = _validator(tmp_path)
    refs = [
        ("GFX_only_in_variant", _iface(tmp_path, MD_VARIANT), 20),
    ]
    v._check_undefined_refs(
        refs,
        set(),
        source_label=".gui files",
        category="undefined-sprite",
        gui_mode=True,
    )
    sev = _severity_by_file(v)
    assert sev[MD_VARIANT] == Severity.ERROR
