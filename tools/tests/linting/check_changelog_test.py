import check_changelog
from check_changelog import check_lines


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

v2.0.0

Content:
 - [USA] Added an American event
 - Added a global feature
 - [ALG] Added an Algerian event
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
        "v2.0.1\n\nContent:\n - [ENG] B\n\nv2.0.0\n\nContent:\n - [FRA] A\n - [ENG] B\n",
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(check_changelog.sys, "argv", ["check_changelog", str(path)])
    assert check_changelog.main() == 0


def test_main_passes_clean_file(tmp_path, monkeypatch):
    path = tmp_path / "Changelog.txt"
    path.write_text("v2.0.1\n\nContent:\n - A\n - [ENG] B\n", encoding="utf-8")
    monkeypatch.setattr(check_changelog.sys, "argv", ["check_changelog", str(path)])
    assert check_changelog.main() == 0
