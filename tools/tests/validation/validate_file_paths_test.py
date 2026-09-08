"""Unit tests for validate_file_paths — cross-platform path hazards."""

import pytest
import validate_file_paths as vfp

_MANIFEST_SAMPLE = """
directory
name = common
sub_directories = yes
file_extension = .txt

directory
name = map
sub_directories = no
file_extension = .bmp
"""

_DESCRIPTOR = """version="2.0.0"
replace_path = "common/ai_focuses"
replace_path = "history/countries/"
replace_path = "history/countries"
"""


def _validator(tmp_path, tracked, vanilla, monkeypatch, descriptor=_DESCRIPTOR):
    (tmp_path / "descriptor.mod").write_text(descriptor, encoding="utf-8")
    monkeypatch.setattr(vfp, "tracked_content_paths", lambda _p: tracked)
    monkeypatch.setattr(vfp, "find_hoi4_install", lambda: None)
    monkeypatch.setattr(vfp, "load_paths_manifest", lambda: set(vanilla))
    validator = vfp.Validator(mod_path=str(tmp_path), use_colors=False)
    validator.run_validations()
    return validator


def test_parse_checksum_manifest_reads_directory_blocks():
    assert vfp.parse_checksum_manifest(_MANIFEST_SAMPLE) == [
        ("common", ".txt", True),
        ("map", ".bmp", False),
    ]


def test_parse_checksum_manifest_ignores_extension_without_directory():
    assert vfp.parse_checksum_manifest("file_extension = .txt\n") == []


def test_replaced_dirs_normalises_trailing_slash(tmp_path):
    (tmp_path / "descriptor.mod").write_text(_DESCRIPTOR, encoding="utf-8")
    assert vfp.replaced_dirs(str(tmp_path)) == {
        "common/ai_focuses",
        "history/countries",
    }


def test_replaced_dirs_without_descriptor(tmp_path):
    assert vfp.replaced_dirs(str(tmp_path)) == set()


def test_case_collision_groups_pairs_only_case_variants():
    groups = vfp.case_collision_groups(
        ["common/a/Foo.txt", "common/a/foo.txt", "common/a/bar.txt"]
    )
    assert groups == [["common/a/Foo.txt", "common/a/foo.txt"]]


def test_case_collision_groups_ignores_unique_paths():
    assert vfp.case_collision_groups(["common/a.txt", "common/b.txt"]) == []


@pytest.mark.parametrize(
    "path",
    [
        "common/units/names.txt",
        "history/countries/TUR - Turkey.txt",
        "gfx/leaders/GER/Rüdiger_Drews.dds",
    ],
)
def test_windows_name_problem_accepts_shipped_names(path):
    assert vfp.windows_name_problem(path) is None


@pytest.mark.parametrize(
    "path",
    [
        "common/ideas/what?.txt",
        "common/ideas/a<b>.txt",
        "common/trailing /file.txt",
        "common/ideas/trailing.",
        "common/NUL/file.txt",
        "common/ideas/aux.txt",
    ],
)
def test_windows_name_problem_rejects_hostile_names(path):
    assert vfp.windows_name_problem(path) is not None


def test_vanilla_case_collision_is_an_error(tmp_path, monkeypatch):
    validator = _validator(
        tmp_path,
        ["common/dynamic_modifiers/WUW_dynamic_modifiers.txt"],
        ["common/dynamic_modifiers/wuw_dynamic_modifiers.txt"],
        monkeypatch,
    )
    assert validator.errors_found == 1
    assert validator._issues[0].category == "vanilla-path-case"


def test_exact_vanilla_override_is_clean(tmp_path, monkeypatch):
    validator = _validator(
        tmp_path,
        ["common/dynamic_modifiers/wuw_dynamic_modifiers.txt"],
        ["common/dynamic_modifiers/wuw_dynamic_modifiers.txt"],
        monkeypatch,
    )
    assert validator.errors_found == 0
    assert validator.warnings_found == 0


def test_case_collision_in_replaced_dir_is_a_warning(tmp_path, monkeypatch):
    validator = _validator(
        tmp_path,
        ["common/ai_focuses/usa.txt"],
        ["common/ai_focuses/USA.txt"],
        monkeypatch,
    )
    assert validator.errors_found == 0
    assert validator.warnings_found == 1


def test_directory_case_collision_is_an_error(tmp_path, monkeypatch):
    validator = _validator(
        tmp_path,
        ["common/Dynamic_modifiers/99_AFG.txt"],
        ["common/dynamic_modifiers/wuw_dynamic_modifiers.txt"],
        monkeypatch,
    )
    assert validator.errors_found == 1
    assert "directory differs only in case" in validator._issues[0].message


def test_internal_case_collision_is_an_error(tmp_path, monkeypatch):
    validator = _validator(
        tmp_path,
        ["gfx/leaders/GER/Foo.dds", "gfx/leaders/GER/foo.dds"],
        ["common/dynamic_modifiers/wuw_dynamic_modifiers.txt"],
        monkeypatch,
    )
    assert validator.errors_found == 1
    assert validator._issues[0].category == "internal-path-case"


def test_missing_descriptor_fails_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(vfp, "tracked_content_paths", lambda _p: ["common/a.txt"])
    validator = vfp.Validator(mod_path=str(tmp_path), use_colors=False)
    validator.run_validations()
    assert validator.errors_found == 1
    assert validator._issues[0].category == "paths-setup"


def test_missing_vanilla_list_fails_setup(tmp_path, monkeypatch):
    (tmp_path / "descriptor.mod").write_text(_DESCRIPTOR, encoding="utf-8")
    monkeypatch.setattr(vfp, "tracked_content_paths", lambda _p: ["common/a.txt"])
    monkeypatch.setattr(vfp, "find_hoi4_install", lambda: None)
    monkeypatch.setattr(vfp, "load_paths_manifest", set)
    validator = vfp.Validator(mod_path=str(tmp_path), use_colors=False)
    validator.run_validations()
    assert validator.errors_found == 1
    assert validator._issues[0].category == "paths-setup"


def test_shipped_manifest_covers_the_checksummed_roots():
    paths = vfp.load_paths_manifest()
    assert len(paths) > 4000
    assert {p.split("/", 1)[0] for p in paths} == {
        "common",
        "events",
        "history",
        "map",
    }
