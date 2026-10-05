"""Selection tests for validator_batches (CI batch list + PR impact scan)."""

import pytest
import run_validator_batch as rvb
import validator_batches as vb
from shared.paths import VALIDATION_DIR


@pytest.fixture(scope="module")
def repository_import_graph():
    return vb._build_import_graph()


@pytest.fixture
def reuse_repository_import_graph(monkeypatch, repository_import_graph):
    # Each selection gets its own mutable graph without reparsing unchanged sources.
    monkeypatch.setattr(
        vb,
        "_build_import_graph",
        lambda nodes: {
            node: edges.copy() for node, edges in repository_import_graph.items()
        },
    )


def test_every_batch_spec_script_exists():
    assert len(vb.ALL_SPECS) == 43
    assert not {spec.name for spec in vb.ALL_SPECS} & {
        spec.name for spec in vb.IMPACT_ONLY_SPECS
    }
    missing = [
        spec.script
        for spec in vb.ALL_SPECS
        if not (VALIDATION_DIR / spec.script).is_file()
    ]
    assert not missing, f"batch specs name scripts that do not exist: {missing}"


def test_batches_cover_every_ci_validator_exactly_once():
    scripts = [spec.script for spec in vb.ALL_SPECS]
    assert len(scripts) == len(set(scripts)), "a validator appears in two batches"
    for spec in vb.ALL_SPECS:
        assert spec.groups, f"{spec.script} would never be selected (no groups)"


def test_core_batch_selects_from_the_core_groups():
    for spec in vb.BATCHES["core"]:
        # Only common-mistakes also scans the music tree.
        extra = {"music"} if spec.name == "common-mistakes" else set()
        assert set(spec.groups) == set(vb._CORE_GROUPS) | extra


def test_variables_spec_carries_the_redundant_focus_flag_scan():
    spec = next(spec for spec in vb.ALL_SPECS if spec.name == "variables")
    assert spec.args == ("--redundant-focus-flags",)
    assert spec.strict is True


def test_decisions_spec_carries_the_unannounced_category_scan():
    spec = next(spec for spec in vb.ALL_SPECS if spec.name == "decisions")
    assert spec.args == ("--unannounced-categories",)
    assert spec.strict is True


def test_selected_specs_filters_by_changed_groups():
    selected = {
        spec.name
        for spec in vb.BATCHES["targeted-a"]
        if spec.name
        in {s.name for s in rvb.selected_specs("targeted-a", {"localisation"})}
    }
    assert selected == {"decisions", "mios"}
    # An unknown or empty group list selects the whole batch (dispatch flow).
    assert len(rvb.selected_specs("targeted-a", None)) == len(vb.BATCHES["targeted-a"])


def test_graphic_db_group_selects_gfx_references():
    selected = {spec.name for spec in rvb.selected_specs("targeted-b", {"graphic-db"})}
    assert selected == {"gfx-references"}


def test_music_group_selects_only_common_mistakes():
    selected = {spec.name for spec in rvb.selected_specs("core", {"music"})}
    assert selected == {"common-mistakes"}


def test_selected_specs_rejects_unknown_batch():
    with pytest.raises(SystemExit, match="Unknown batch"):
        rvb.selected_specs("nope", None)


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_direct_validator_change_selects_transitive_importers():
    # validate_bonus_names imports from validate_tech_categories, so a change
    # to tech-categories must re-run its consumer too.
    batch, adhoc = vb.select_for_changed_files(
        ["tools/validation/validate_tech_categories.py"]
    )
    assert {spec.name for spec in batch} == {"tech-categories", "bonus-names"}
    assert adhoc == []


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_shared_module_change_selects_its_transitive_consumers():
    batch, adhoc = vb.select_for_changed_files(["tools/validation/sprite_index.py"])
    assert {"events", "focus-tree", "scientist-traits", "decisions"} <= {
        spec.name for spec in batch
    }
    assert adhoc == []


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_linting_wrapper_change_selects_the_validator_it_wraps():
    # Both validate_common_mistakes and validate_decisions import this scanner.
    batch, adhoc = vb.select_for_changed_files(
        ["tools/linting/check_common_mistakes.py"]
    )
    assert {spec.name for spec in batch} == {
        "common-mistakes",
        "decisions",
        "equipment-variants",
    }
    assert adhoc == []


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_shared_infrastructure_selects_every_validator():
    # shared_utils is imported (transitively through validator_common) by all
    # validators, so the conservative selection is the whole CI set.
    batch, adhoc = vb.select_for_changed_files(["tools/shared_utils.py"])
    assert {spec.name for spec in batch} >= {spec.name for spec in vb.ALL_SPECS}
    assert {
        "file-paths",
        "style",
        "mod-descriptors",
        "localization-encoding",
    } <= {spec.name for spec in batch}
    assert adhoc == []


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_validator_common_change_selects_the_impact_checks_it_feeds():
    batch, adhoc = vb.select_for_changed_files(["tools/validation/validator_common.py"])
    impact = {spec.name for spec in vb.IMPACT_ONLY_SPECS}
    assert {spec.name for spec in batch} & impact == {
        "file-paths",
        "style",
        "mod-descriptors",
    }
    assert adhoc == []


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_leaf_validation_tooling_selects_every_check(repository_import_graph):
    # Nothing imports the batch runner, so no importer bounds what it can break.
    assert not vb._transitive_importers(
        repository_import_graph, "validation/run_validator_batch"
    )
    batch, adhoc = vb.select_for_changed_files(
        ["tools/validation/run_validator_batch.py"]
    )
    assert {spec.name for spec in batch} == {
        spec.name for spec in vb.ALL_SPECS + vb.IMPACT_ONLY_SPECS
    }
    assert adhoc == []


def test_report_library_change_selects_every_batch_validator():
    batch, adhoc = vb.select_for_changed_files(["tools/report_lib/loader.py"])
    assert [spec.name for spec in batch] == [spec.name for spec in vb.ALL_SPECS]
    assert adhoc == []


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_leaf_shared_module_selects_only_its_importers():
    batch, _ = vb.select_for_changed_files(["tools/validation/equipment_stats.py"])
    assert {spec.name for spec in batch} == {"ideas", "mios"}


def test_new_validator_gets_an_adhoc_full_scan(tmp_path, monkeypatch):
    (tmp_path / "validate_brand_new_thing.py").write_text(
        "from shared_utils import run_validator_main\nrun_validator_main(Validator)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(vb, "VALIDATION_DIR", str(tmp_path))

    batch, adhoc = vb.select_for_changed_files(
        ["tools/validation/validate_brand_new_thing.py"]
    )
    assert batch == []
    assert [spec.name for spec in adhoc] == ["brand-new-thing"]


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_deleted_validator_is_dropped(tmp_path, monkeypatch):
    # The changed path still names the validator, but the file is gone: there
    # is nothing left to run, and the scan must not fail on it.
    monkeypatch.setattr(vb, "VALIDATION_DIR", str(tmp_path))
    batch, adhoc = vb.select_for_changed_files(["tools/validation/validate_events.py"])
    assert batch == []
    assert adhoc == []


@pytest.mark.usefixtures("reuse_repository_import_graph")
def test_renamed_validator_runs_only_under_its_new_name(tmp_path, monkeypatch):
    # A rename surfaces as delete + add: the old path is dropped, the new
    # path runs (as ad-hoc while unwired).
    (tmp_path / "validate_renamed_thing.py").write_text(
        "from shared_utils import run_validator_main\nrun_validator_main(Validator)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(vb, "VALIDATION_DIR", str(tmp_path))

    batch, adhoc = vb.select_for_changed_files(
        [
            "tools/validation/validate_events.py",
            "tools/validation/validate_renamed_thing.py",
        ]
    )
    assert batch == []
    assert [spec.name for spec in adhoc] == ["renamed-thing"]


def test_standalone_ci_tools_select_only_their_impact_specs():
    for path, name in (
        ("tools/linting/validate_localization_encoding.py", "localization-encoding"),
        ("tools/linting/validate_mod_encoding.py", "mod-encoding"),
        ("tools/linting/validate_txt_encoding.py", "txt-encoding"),
        ("tools/validation/validate_style.py", "style"),
        ("tools/validation/validate_mod_descriptors.py", "mod-descriptors"),
        ("tools/validation/validate_file_paths.py", "file-paths"),
    ):
        batch, adhoc = vb.select_for_changed_files([path])
        assert [spec.name for spec in batch] == [name]
        assert adhoc == []


def test_manual_texture_audit_stays_excluded_from_impact():
    batch, adhoc = vb.select_for_changed_files(
        ["tools/validation/validate_unused_textures.py"]
    )
    assert batch == []
    assert adhoc == []


def test_manual_standardization_check_stays_excluded_from_impact():
    # Manual-only: the standardization report is deliberately unwired from
    # pre-commit and CI, so editing the script must not re-select it.
    batch, adhoc = vb.select_for_changed_files(
        ["tools/validation/validate_standardization.py"]
    )
    assert batch == []
    assert adhoc == []


def test_unsupported_new_validator_is_not_run_with_standard_flags(
    tmp_path, monkeypatch
):
    (tmp_path / "validate_custom.py").write_text(
        "import argparse\nargparse.ArgumentParser().parse_args()\n", encoding="utf-8"
    )
    monkeypatch.setattr(vb, "VALIDATION_DIR", str(tmp_path))
    batch, adhoc = vb.select_for_changed_files(["tools/validation/validate_custom.py"])
    assert batch == []
    assert adhoc == []


def test_unknown_validation_tooling_selects_conservatively():
    batch, adhoc = vb.select_for_changed_files(
        ["tools/validation/brand_new_shared_helper.py"]
    )
    assert {spec.name for spec in batch} >= {spec.name for spec in vb.ALL_SPECS}
    assert {spec.name for spec in batch} >= {spec.name for spec in vb.IMPACT_ONLY_SPECS}
    assert adhoc == []


def test_reference_file_selects_its_validator():
    batch, adhoc = vb.select_for_changed_files([".claude/docs/typo-watchlist.md"])
    assert [spec.name for spec in batch] == ["localisation"]
    assert adhoc == []

    batch, _ = vb.select_for_changed_files(
        ["resources/documentation/modifiers_documentation.md"]
    )
    assert [spec.name for spec in batch] == ["modifiers"]


def test_unrelated_changes_select_nothing():
    for path in (
        "tools/tests/validation/config_drift_test.py",
        ".github/workflows/test-suite.yml",
        "common/decisions/whatever.txt",
    ):
        batch, adhoc = vb.select_for_changed_files([path])
        assert batch == [], path
        assert adhoc == [], path


def test_import_graph_parses_comma_and_relative_imports(tmp_path):
    # Regex import scanning missed `import a, b` and relative imports; the
    # AST graph must catch both, or validators silently drop off selection.
    (tmp_path / "validation").mkdir()
    (tmp_path / "shared_utils.py").write_text("", encoding="utf-8")
    # The known module comes second so a first-alias-only reading misses it.
    (tmp_path / "validation/validate_comma.py").write_text(
        "import other_module, shared_utils\n", encoding="utf-8"
    )
    (tmp_path / "validation/validate_relative.py").write_text(
        "from . import other_module, validate_comma\nfrom .shared_utils import thing\n",
        encoding="utf-8",
    )
    nodes = {
        "shared_utils": str(tmp_path / "shared_utils.py"),
        "validation/validate_comma": str(tmp_path / "validation/validate_comma.py"),
        "validation/validate_relative": str(
            tmp_path / "validation/validate_relative.py"
        ),
    }

    graph = vb._build_import_graph(nodes)

    assert graph["validation/validate_comma"] == {"shared_utils"}
    assert graph["validation/validate_relative"] == {
        "validation/validate_comma",
        "shared_utils",
    }


def test_module_importers_follow_the_transitive_chain(repository_import_graph):
    graph = {node: edges.copy() for node, edges in repository_import_graph.items()}
    importers = vb._transitive_importers(graph, "validation/equipment_stats")
    assert {"validation/validate_ideas", "validation/validate_mios"} <= importers
    chain = {"leaf": set(), "middle": {"leaf"}, "top": {"middle"}, "other": set()}
    assert vb._transitive_importers(chain, "leaf") == {"middle", "top"}


def test_unparsable_module_stays_conservative(tmp_path):
    # A file that cannot be parsed imports nothing by our reading; it must
    # not look isolated and drop validators from selection.
    (tmp_path / "validation").mkdir()
    (tmp_path / "validation/validate_broken.py").write_text(
        "def broken(:\n", encoding="utf-8"
    )
    nodes = {
        "validation/validate_broken": str(tmp_path / "validation/validate_broken.py")
    }

    graph = vb._build_import_graph(nodes)

    assert graph["validation/validate_broken"] == set()


def test_import_graph_is_not_built_for_non_import_selections(monkeypatch):
    def unexpected_graph(*args):
        pytest.fail("selection does not need an import graph")

    monkeypatch.setattr(vb, "_build_import_graph", unexpected_graph)
    batch, adhoc = vb.select_for_changed_files(
        [
            "common/decisions/whatever.txt",
            ".claude/docs/typo-watchlist.md",
            "tools/validation/validate_style.py",
            "tools/validation/validate_unused_textures.py",
        ]
    )
    assert [spec.name for spec in batch] == ["localisation", "style"]
    assert adhoc == []


def test_import_graph_is_built_once_per_selection_not_cached_across_calls(
    tmp_path, monkeypatch, write_path
):
    validation_dir = tmp_path / "validation"
    for name in ("validate_tech_categories", "validate_bonus_names", "equipment_stats"):
        write_path(validation_dir, f"{name}.py")
    write_path(validation_dir, "validate_ideas.py", "import equipment_stats\n")
    monkeypatch.setattr(vb, "TOOLS_DIR", str(tmp_path))
    monkeypatch.setattr(vb, "VALIDATION_DIR", str(validation_dir))
    original = vb._build_import_graph
    calls = []

    def build(nodes):
        calls.append(nodes)
        return original(nodes)

    monkeypatch.setattr(vb, "_build_import_graph", build)
    changed = [
        "tools/validation/validate_tech_categories.py",
        "tools/validation/equipment_stats.py",
    ]
    first = vb.select_for_changed_files(changed)
    assert len(calls) == 1
    assert vb.select_for_changed_files(changed) == first
    assert len(calls) == 2
    assert {spec.name for spec in first[0]} == {"tech-categories", "ideas"}
    assert first[1] == []

    write_path(
        validation_dir,
        "validate_bonus_names.py",
        "import validate_tech_categories\n",
    )
    batch, adhoc = vb.select_for_changed_files(changed)
    assert {spec.name for spec in batch} == {"tech-categories", "bonus-names", "ideas"}
    assert adhoc == []
    assert len(calls) == 3
