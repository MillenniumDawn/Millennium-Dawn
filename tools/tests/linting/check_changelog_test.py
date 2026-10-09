import check_changelog
from check_changelog import check_lines, order_lines


def _lines(text):
    return text.strip("\n").splitlines()


def test_ordered_block_passes():
    lines = _lines("""
v2.0.1

Content:
 - Added a global feature
 - [CHI] Added a Chinese focus
 - [CHI/ISR] Fixed shared sprites
 - [ENG] Added a British event
 - [ENG] Added another British event

Bugfix:
 - Fixed a global bug
 - [ALG] Fixed an Algerian tooltip
""")
    assert check_lines(lines) == []


def test_untagged_after_tagged_fails():
    lines = _lines("""
v2.0.1

Content:
 - [CHI] Added a Chinese focus
 - Added a global feature
""")
    assert check_lines(lines) == [
        "line 5: untagged entry must come before [CHI] (line 4)"
    ]


def test_out_of_order_tags_fail():
    lines = _lines("""
v2.0.1

Content:
 - [FRA] Added a French focus
 - [ENG] Added a British event
""")
    assert check_lines(lines) == ["line 5: [ENG] must come before [FRA] (line 4)"]


def test_compound_tags_sort_by_first_tag():
    lines = _lines("""
v2.0.1

Bugfix:
 - [CHI] Fixed a Chinese focus
 - [CHI/NKO] Fixed a joint focus
 - [PER][BRA] Guarded divisions
 - [PER] Fixed a Persian event
 - [RAJ/PAK/CHI] Fixed border decisions
""")
    assert check_lines(lines) == []


def test_multi_tag_entry_sorts_with_its_first_tag():
    lines = _lines("""
v2.0.1

Bugfix:
 - [CHI/NKO] Fixed a joint focus
 - [CHI] Fixed a Chinese focus
""")
    assert check_lines(lines) == []


def test_indented_category_header_starts_new_order():
    lines = _lines("""
v2.0.1

Content:
 - [USA] Added an American event

  Bugfix:
 - [ALG] Fixed an Algerian tooltip
""")
    assert check_lines(lines) == []


def test_each_category_is_checked_separately():
    lines = _lines("""
v2.0.1

Content:
 - [USA] Added an American event

Bugfix:
 - Fixed a global bug
 - [ALG] Fixed an Algerian tooltip
""")
    assert check_lines(lines) == []


def test_older_versions_are_ignored():
    lines = _lines("""
v2.0.1

Content:
 - [ALG] Added an Algerian event

v2.0.1

Content:
 - [USA] Added an American event
 - Added a global feature
 - [ALG] Added an Algerian event
""")
    assert check_lines(lines) == []


def test_blank_line_between_entries_fails():
    lines = _lines("""
v2.0.1

Content:
 - Added a global feature

 - [CHI] Added a Chinese focus
""")
    assert check_lines(lines) == ["line 5: remove the blank line between entries"]


def test_repeated_blank_line_fails():
    lines = _lines("""
v2.0.1

Content:
 - Added a global feature


Bugfix:
 - Fixed a global bug
""")
    assert check_lines(lines) == ["line 6: remove the repeated blank line"]


def test_blank_lines_in_older_versions_are_ignored():
    lines = _lines("""
v2.0.1

Content:
 - Added a global feature

v2.0.1

Content:
 - Added a global feature


 - [CHI] Added a Chinese focus
""")
    assert check_lines(lines) == []


def test_main_reports_errors(tmp_path, monkeypatch, capsys):
    path = tmp_path / "Changelog.txt"
    path.write_text("v2.0.1\n\nContent:\n - [FRA] A\n - [ENG] B\n", encoding="utf-8")
    monkeypatch.setattr(check_changelog.sys, "argv", ["check_changelog", str(path)])
    assert check_changelog.main() == 1
    assert "[ENG] must come before [FRA]" in capsys.readouterr().err


def test_main_ignores_older_versions_with_bom(tmp_path, monkeypatch):
    path = tmp_path / "Changelog.txt"
    path.write_text(
        "v2.0.1\n\nContent:\n - [ENG] B\n\nv2.0.1\n\nContent:\n - [FRA] A\n - [ENG] B\n",
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(check_changelog.sys, "argv", ["check_changelog", str(path)])
    assert check_changelog.main() == 0


def test_sort_preserves_entries_line_endings_and_older_versions():
    older = "v2.0.1\r\nContent:\r\n - [USA] Old\r\n\r\n\r\n - Global old\r\n"
    original = (
        "\ufeffv2.0.1\r\n\r\nContent:\r\n"
        " - [USA] U\r\n\r\n - Global\r\n"
        " - [chi/NKO] C1\r\n - [CHI] C2\r\n"
        "Bugfix:\r\n - [FRA] F\r\n - [ENG] E\r\n" + older
    )
    expected = (
        "\ufeffv2.0.1\r\n\r\nContent:\r\n"
        " - Global\r\n - [chi/NKO] C1\r\n"
        " - [CHI] C2\r\n - [USA] U\r\n"
        "Bugfix:\r\n - [ENG] E\r\n - [FRA] F\r\n" + older
    )
    ordered = order_lines(original.splitlines(keepends=True))
    assert "".join(ordered) == expected
    assert check_lines(ordered) == []
    assert order_lines(ordered) == ordered
    assert order_lines([]) == []


def test_sort_tidies_blank_lines_and_keeps_category_spacing():
    original = (
        "v2.0.1\n\nContent:\n - [USA] U\n\n\n - Global\n\n\n"
        "Bugfix:\n - B\n\nFooter text\n\n\nMore text\n"
    )
    ordered = order_lines(original.splitlines(keepends=True))
    assert "".join(ordered) == (
        "v2.0.1\n\nContent:\n - Global\n - [USA] U\n\n"
        "Bugfix:\n - B\n\nFooter text\n\nMore text\n"
    )
    assert check_lines(ordered) == []


def test_sort_preserves_an_absent_final_newline():
    original = "v2.0.1\nContent:\n - [USA] U\n - Global"
    assert "".join(order_lines(original.splitlines(keepends=True))) == (
        "v2.0.1\nContent:\n - Global\n - [USA] U"
    )


def test_main_passes_clean_file(tmp_path, monkeypatch):
    path = tmp_path / "Changelog.txt"
    path.write_text("v2.0.1\n\nContent:\n - A\n - [ENG] B\n", encoding="utf-8")
    monkeypatch.setattr(check_changelog.sys, "argv", ["check_changelog", str(path)])
    assert check_changelog.main() == 0
