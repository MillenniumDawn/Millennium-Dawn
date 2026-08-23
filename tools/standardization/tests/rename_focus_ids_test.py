from tools.standardization.rename_focus_ids import extract_focus_ids, rename_focus_ids


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
