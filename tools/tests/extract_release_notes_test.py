import extract_release_notes


def test_extracts_exact_tag_section():
    changelog = "v2.0.0\n\nContent:\n - Previous release\n"
    assert extract_release_notes.extract_section(changelog, "v2.0.0") == (
        "v2.0.0\n\nContent:\n - Previous release"
    )


def test_letter_suffix_matches_its_own_header():
    changelog = "v1.12.3\nBase notes\nv1.12.3b\nHotfix notes\nv1.12.4\nLater notes"
    assert extract_release_notes.extract_section(changelog, "v1.12.3b") == (
        "v1.12.3b\nHotfix notes"
    )


def test_stops_at_next_version_header():
    changelog = "v2.0.0\nFirst notes\nv2.0.1\nSecond notes"
    assert extract_release_notes.extract_section(changelog, "v2.0.0") == (
        "v2.0.0\nFirst notes"
    )


def test_missing_tag_returns_none():
    assert extract_release_notes.extract_section("v2.0.0\nNotes", "v2.0.1") is None


def test_empty_section_returns_none():
    changelog = "v2.0.0\n\n  \nv2.0.1\nNotes"
    assert extract_release_notes.extract_section(changelog, "v2.0.0") is None


def test_cli_writes_section_and_returns_one_for_missing_section(tmp_path, monkeypatch):
    changelog = tmp_path / "Changelog.txt"
    output = tmp_path / "release-notes.md"
    changelog.write_text("v2.0.0\nNotes\n", encoding="utf-8")
    monkeypatch.setattr(
        extract_release_notes.sys,
        "argv",
        [
            "extract_release_notes",
            "v2.0.0",
            "--changelog",
            str(changelog),
            "--output",
            str(output),
        ],
    )

    assert extract_release_notes.main() == 0
    assert output.read_text(encoding="utf-8") == "v2.0.0\nNotes\n"

    monkeypatch.setattr(
        extract_release_notes.sys,
        "argv",
        [
            "extract_release_notes",
            "v2.0.1",
            "--changelog",
            str(changelog),
            "--output",
            str(output),
        ],
    )
    assert extract_release_notes.main() == 1
