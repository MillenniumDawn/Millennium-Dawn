"""Tests for the focus title/description color-palette check in
validate_focus_tree (validate_focus_loc_colors / _load_focus_loc_values).
"""

import validate_focus_tree as V
from shared.suite import write_under_str as _write


def _focus_file(tmp_path, body, name="test.txt"):
    return _write(tmp_path, f"common/national_focus/{name}", body)


def _loc_file(tmp_path, body, name="md_l_english.yml"):
    return _write(tmp_path, f"localisation/english/{name}", body)


def _validator(tmp_path, **kwargs):
    return V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)


def _messages(validator, category):
    return [i.message for i in validator._issues if i.category == category]


TREE = """focus_tree = {
\tid = tree_a
\tfocus = { id = TAG_focus_a x = 0 y = 0 cost = 1 }
\tfocus = { id = TAG_focus_b x = 2 y = 0 cost = 1 }
\tfocus = { id = TAG_focus_c x = 4 y = 0 cost = 1 }
}
"""

LOC = (
    "l_english:\n"
    ' TAG_focus_a:0 "§Ycolored§! title"\n'
    ' TAG_focus_a_desc:0 "Use §Ythis§! or §Gthat§! or §Rcost§!"\n'
    ' TAG_focus_b:0 "Clean title"\n'
    ' TAG_focus_b_desc:0 "Off palette §Lbad§! code"\n'
    ' TAG_focus_c:0 "Clean title c"\n'
    ' TAG_focus_c_desc:0 "See 15 U.S.C. § 1 for details"\n'
)


def _run(tmp_path):
    _focus_file(tmp_path, TREE)
    _loc_file(tmp_path, LOC)
    v = _validator(tmp_path)
    v.validate_focus_loc_colors()
    return v


def test_colored_focus_title_is_flagged(tmp_path):
    v = _run(tmp_path)

    messages = _messages(v, "focus-title-color-code")
    assert messages == [
        "Focus title 'TAG_focus_a' uses color code §Y — titles carry no color"
    ]


def test_clean_focus_title_is_not_flagged(tmp_path):
    v = _run(tmp_path)

    titled = [
        i
        for i in v._issues
        if i.category == "focus-title-color-code" and "TAG_focus_b" in i.message
    ]
    assert titled == []


def test_desc_using_only_palette_colors_is_not_flagged(tmp_path):
    v = _run(tmp_path)

    desc = [
        i
        for i in v._issues
        if i.category == "focus-desc-color-palette" and "TAG_focus_a" in i.message
    ]
    assert desc == []


def test_desc_using_off_palette_color_is_flagged(tmp_path):
    v = _run(tmp_path)

    messages = _messages(v, "focus-desc-color-palette")
    assert messages == [
        "Focus description 'TAG_focus_b_desc' uses color code §L — use" " §Y, §G or §R"
    ]


def test_prose_section_sign_is_not_treated_as_a_color_code(tmp_path):
    v = _run(tmp_path)

    flagged = [i for i in v._issues if "TAG_focus_c" in i.message]
    assert flagged == []


def test_finding_is_reported_against_the_yml_file_and_line(tmp_path):
    v = _run(tmp_path)

    title_issues = [i for i in v._issues if i.category == "focus-title-color-code"]
    assert len(title_issues) == 1
    issue = title_issues[0]
    assert issue.file == "localisation/english/md_l_english.yml"
    assert issue.line == 2

    desc_issues = [i for i in v._issues if i.category == "focus-desc-color-palette"]
    assert len(desc_issues) == 1
    assert desc_issues[0].file == "localisation/english/md_l_english.yml"
    assert desc_issues[0].line == 5
