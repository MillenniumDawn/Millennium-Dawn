import sys

import pytest

import tools.standardization.rename_focus_ids as rename_focus_ids_module
from tools.standardization.rename_focus_ids import (
    extract_focus_ids,
    main,
    rename_focus_ids,
)


def _write(path, text):
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def test_extracts_focus_ids_without_tree_or_nested_ids():
    text = """focus_tree = {
\tid = australia_focus
\tfocus = {
\t\tid = ast_first
\t\tcompletion_reward = { id = nested_id }
\t}
}
shared_focus = {
\tid = second_focus
}
"""

    assert extract_focus_ids(text, "AST") == {
        "ast_first": "AST_first",
        "second_focus": "AST_second_focus",
    }


def test_renames_focus_references_and_preserves_unrelated_tokens(tmp_path):
    focus_dir = tmp_path / "common" / "national_focus"
    event_dir = tmp_path / "events"
    loc_dir = tmp_path / "localisation" / "english"
    focus_dir.mkdir(parents=True)
    event_dir.mkdir(parents=True)
    loc_dir.mkdir(parents=True)

    focus_file = focus_dir / "05_Australia.txt"
    _write(
        focus_file,
        """shared_focus = {
\tid = ast_first
\tlog = \"Focus ast_first\"
\trelative_position_id = ast_first
\tmodifier = ast_first
}
""",
    )
    event_file = event_dir / "australia.txt"
    _write(event_file, "\tfocus = ast_first\n")
    localisation_file = loc_dir / "MD_focus_AST_l_english.yml"
    _write(
        localisation_file,
        'l_english:\n AST_ast_first: "old"\n ast_first: "new"\n ast_first_desc: "desc"\n',
    )

    mapping, changed = rename_focus_ids(tmp_path, focus_file, localisation_file, "AST")

    assert mapping == {"ast_first": "AST_first"}
    assert focus_file in changed
    output = focus_file.read_text(encoding="utf-8")
    assert "id = AST_first" in output
    assert "Focus AST_first" in output
    assert "relative_position_id = AST_first" in output
    assert "modifier = ast_first" in output
    assert event_file.read_text(encoding="utf-8") == "\tfocus = AST_first\n"
    assert 'AST_first: "new"' in localisation_file.read_text(encoding="utf-8")
    assert 'AST_first_desc: "desc"' in localisation_file.read_text(encoding="utf-8")


def test_cli_defaults_to_repo_root_from_standardization_directory(
    tmp_path, monkeypatch
):
    root = tmp_path / "repo"
    standardization_dir = root / "tools" / "standardization"
    focus_file = root / "common" / "national_focus" / "05_Australia.txt"
    event_file = root / "events" / "australia.txt"
    localisation_file = root / "localisation" / "english" / "MD_focus_AST_l_english.yml"
    standardization_dir.mkdir(parents=True)
    focus_file.parent.mkdir(parents=True)
    event_file.parent.mkdir(parents=True)
    localisation_file.parent.mkdir(parents=True)
    _write(focus_file, "focus = {\n\tid = ast_first\n}\n")
    _write(event_file, "focus = ast_first\n")
    _write(localisation_file, 'l_english:\n ast_first: "Focus"\n')

    monkeypatch.setattr(
        rename_focus_ids_module,
        "__file__",
        str(standardization_dir / "rename_focus_ids.py"),
    )
    monkeypatch.chdir(standardization_dir)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rename_focus_ids.py",
            "--focus-file",
            "../../common/national_focus/05_Australia.txt",
            "--localisation-file",
            "../../localisation/english/MD_focus_AST_l_english.yml",
            "--tag",
            "AST",
        ],
    )

    assert main() == 0
    assert event_file.read_text(encoding="utf-8") == "focus = AST_first\n"


def test_tag_prefixed_ast_ids_map_from_both_spellings():
    text = "focus = {\n\tid = AST_ast_first\n}\nfocus = {\n\tid = AST_second\n}\n"
    assert extract_focus_ids(text, "AST") == {
        "AST_ast_first": "AST_first",
        "ast_first": "AST_first",
        "AST_second": "AST_second",
    }


def test_duplicate_normalised_ids_are_rejected():
    text = "focus = {\n\tid = ast_first\n}\nfocus = {\n\tid = AST_first\n}\n"
    with pytest.raises(ValueError, match="Duplicate normalized focus ID: AST_first"):
        extract_focus_ids(text, "AST")


def _tree(tmp_path, focus_text, event_text, localisation_text):
    focus_dir = tmp_path / "common" / "national_focus"
    event_dir = tmp_path / "events"
    loc_dir = tmp_path / "localisation" / "english"
    focus_dir.mkdir(parents=True)
    event_dir.mkdir(parents=True)
    loc_dir.mkdir(parents=True)
    focus_file = focus_dir / "05_Australia.txt"
    event_file = event_dir / "australia.txt"
    localisation_file = loc_dir / "MD_focus_AST_l_english.yml"
    _write(focus_file, focus_text)
    _write(event_file, event_text)
    _write(localisation_file, localisation_text)
    return focus_file, event_file, localisation_file


def test_focus_file_without_ids_is_rejected(tmp_path):
    focus_file, _event_file, localisation_file = _tree(
        tmp_path,
        "focus_tree = {\n\tid = australia_focus\n}\n",
        "focus = something_else\n",
        'l_english:\n other_key: "x"\n',
    )
    with pytest.raises(ValueError, match="No focus IDs found"):
        rename_focus_ids(tmp_path, focus_file, localisation_file, "AST")


def test_already_canonical_tree_rewrites_nothing(tmp_path):
    focus_file, event_file, localisation_file = _tree(
        tmp_path,
        "shared_focus = {\n\tid = AST_first\n}\n",
        "focus = something_else\n",
        'l_english:\n other_key: "x"\n',
    )

    mapping, changed = rename_focus_ids(tmp_path, focus_file, localisation_file, "AST")

    assert mapping == {"AST_first": "AST_first"}
    assert changed == []
    assert event_file.read_text(encoding="utf-8") == "focus = something_else\n"
