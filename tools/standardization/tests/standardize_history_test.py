"""Tests for the history standardizer.

The transform is documented as lossless: repeated statements (two add_equipment,
two set_country_flag) are semantically meaningful in HOI4 history files and must
all survive. It is also idempotent, and must preserve quoted strings and
comments verbatim.
"""

from standardize_history import HistoryStandardizer

# Modeled on real history/countries structure: a dated block with duplicate
# flags, duplicate special projects, a quoted string, and comments.
_HISTORY = """\
capital = 652

2000.1.1 = {
	set_country_flag = TST_alpha
	set_country_flag = TST_alpha
	set_country_flag = TST_beta

	complete_special_project = sp:sp_space_program
	complete_special_project = sp:sp_space_program

	# keep this standalone comment
	create_country_leader = {
		name = "Mark Rutte"
		picture = "gfx_leader_HOL"
	}

	add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 100 } # inline note
	add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 100 }
}
"""


def _standardize(path):
    std = HistoryStandardizer(idea_law=set(), idea_faction=set(), modifier_vars={})
    std.standardize_file(str(path), str(path))
    return path.read_text(encoding="utf-8")


def test_repeated_statements_all_retained(tmp_path):
    src = tmp_path / "hist.txt"
    src.write_text(_HISTORY, encoding="utf-8")
    out = _standardize(src)
    assert out.count("set_country_flag = TST_alpha") == 2
    assert out.count("complete_special_project = sp:sp_space_program") == 2
    assert out.count("add_equipment_to_stockpile") == 2


def test_idempotent(tmp_path):
    src = tmp_path / "hist.txt"
    src.write_text(_HISTORY, encoding="utf-8")
    run1 = _standardize(src)
    run2 = _standardize(src)
    assert run1 == run2


def test_quoted_string_and_comments_preserved(tmp_path):
    src = tmp_path / "hist.txt"
    src.write_text(_HISTORY, encoding="utf-8")
    out = _standardize(src)
    assert 'name = "Mark Rutte"' in out
    assert "# keep this standalone comment" in out
    assert "# inline note" in out
