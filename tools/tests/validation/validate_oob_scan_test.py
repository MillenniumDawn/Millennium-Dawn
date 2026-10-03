"""Exact-position tests for the scans behind validate_oob_units.py.

The block tree, effect closure, template index, delete and load_oob gates each
skip or batch work. These pin their output on the shapes that break a scanner:
a brace or `#` inside a quoted string, a comment naming the token, the first
and last line, no trailing newline and CRLF. The validator-level cases check a
pooled run and a warm disk cache against the plain in-process run.
"""

import validate_oob_units as oob
from shared.suite import write_under
from validate_oob_units import (
    Validator,
    _build_block_nodes,
    _check_created_units,
    _deleted_template_names,
    _effect_template_closure,
    division_template_entries,
    find_load_oob_references,
)

_BS = chr(92)
_FOREIGN = "CREATE UNIT: foreign-only static template definition"


def _division(template):
    quoted = [_BS + '"' + value + _BS + '"' for value in ("1st Guard", template)]
    return (
        f"name = {quoted[0]} division_template = {quoted[1]}"
        " start_equipment_factor = 1.0"
    )


def _shape(text):
    return [(n["label"], n["line"], n["parent"]) for n in _build_block_nodes(text)]


# --- block tree ---------------------------------------------------------------


def test_block_lines_run_from_the_first_line_to_an_unterminated_last_line():
    text = "a = {\n\tb = { }\n}\nc = { d = { } }"
    assert _shape(text) == [("a", 1, -1), ("b", 2, 0), ("c", 4, -1), ("d", 4, 2)]


def test_quoted_braces_and_escaped_quotes_open_no_block():
    text = 'a = {\n\tlog = "x { ' + _BS + '" } #"\n\tb = { }\n}\n'
    assert _shape(text) == [("a", 1, -1), ("b", 3, 0)]


def test_an_unclosed_quote_ends_at_the_line_break():
    text = 'a = {\n\tname = "open\n\tb = { }\n}\n'
    assert _shape(text) == [("a", 1, -1), ("b", 3, 0)]


def test_crlf_text_keeps_labels_and_lines():
    text = "a =\n{\n\tb = { }\n}\nc = { }"
    assert _shape(text.replace("\n", "\r\n")) == _shape(text)
    assert _shape(text) == [("a", 2, -1), ("b", 3, 0), ("c", 5, -1)]


# --- create_unit blocks in one file -------------------------------------------


def _event_with_create_units():
    return (
        "# create_unit = { owner = ROOT }\n"
        "country_event = {\n"
        "\toption = {\n"
        "\t\tcapital_scope =\n"
        "\t\t{\n"
        '\t\t\tlog = "} #"\n'
        "\t\t\tcreate_unit = {\n"
        f'\t\t\t\tdivision = "{_division("Militia")}"\n'
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
        "create_unit = { owner = ROOT }"
    )


def _create_unit_issues(tmp_path, content):
    path = write_under(tmp_path, "events/TST.txt", content)
    issues = _check_created_units(
        (str(path), "events/TST.txt", str(tmp_path), frozenset(), {}, {}, frozenset())
    )
    return [(i.file, i.line, i.message) for i in issues]


_CREATE_UNIT_ISSUES = [
    ("events/TST.txt", 7, "7: create_unit missing `owner`"),
    (
        "events/TST.txt",
        13,
        "13: create_unit outside a state scope (effect does nothing at country scope)",
    ),
    ("events/TST.txt", 13, "13: create_unit missing `division` string"),
]


def test_create_unit_lines_skip_comments_and_quoted_braces(tmp_path):
    assert (
        _create_unit_issues(tmp_path, _event_with_create_units()) == _CREATE_UNIT_ISSUES
    )


def test_create_unit_lines_are_the_same_with_crlf(tmp_path):
    crlf = _event_with_create_units().replace("\n", "\r\n")
    assert _create_unit_issues(tmp_path, crlf) == _CREATE_UNIT_ISSUES


# --- whole-mod indexes --------------------------------------------------------


def test_effect_closure_keys_only_top_level_effects(tmp_path):
    path = write_under(
        tmp_path,
        "common/scripted_effects/tst.txt",
        "# commented_effect = { }\n"
        '{ stray = { has_template = "Stray" } }\n'
        "ensure_guard = {\n"
        "\tinner_effect = {\n"
        '\t\tdivision_template = { name = "Guard" }\n'
        "\t}\n"
        "\tcall_other = yes\n"
        "}\n"
        'call_other = {\n\tif = { limit = { has_template = "Other" } }\n}',
    )
    assert _effect_template_closure(str(tmp_path), [str(path)]) == {
        "ensure_guard": frozenset({"Guard", "Other"}),
        "call_other": frozenset({"Other"}),
    }


_TEMPLATE_SOURCE = (
    '# division_template = { name = "Commented" }\n'
    "OPR = {\n"
    '\tdivision_template = {\n\t\tname = "Guard"\n\t\tregiments = { }\n\t}\n'
    "}\n"
    'division_template = { name = "[ROOT.GetAdjective] Guard" }\n'
    'event_target:ally = { division_template = { name = "Ally" } }'
)


def test_template_entries_resolve_owners_per_file():
    assert division_template_entries(
        "common/scripted_effects/tst.txt", _TEMPLATE_SOURCE
    ) == [("Guard", "OPR"), ("Ally", None)]
    assert division_template_entries("history/units/TST.txt", _TEMPLATE_SOURCE) == [
        ("Guard", None),
        ("Ally", None),
    ]


def test_deleted_names_ignore_a_commented_delete(tmp_path):
    commented = write_under(
        tmp_path,
        "events/A.txt",
        '# delete_unit_template_and_units = { division_template = "Ghost" }\n',
    )
    real = write_under(
        tmp_path,
        "events/B.txt",
        'x = { delete_unit_template_and_units = { division_template = "Real" } }',
    )
    names = _deleted_template_names(str(tmp_path), [str(commented), str(real)])
    assert names == frozenset({"Real"})


def test_load_oob_refs_on_the_first_and_last_lines():
    content = 'load_oob = "TST_2000"\n# load_oob = GHOST\nx = { load_oob="TST_late" }'
    expected = [("TST_2000", 1), ("TST_late", 3)]
    assert find_load_oob_references(content) == expected
    assert find_load_oob_references(content.replace("\n", "\r\n")) == expected
    assert find_load_oob_references('x = { load_oob="TST_1" }') == [("TST_1", 1)]
    assert find_load_oob_references("# load_oob = GHOST") == []


# --- validator runs -----------------------------------------------------------


def _event(filler):
    return "# filler\n" * filler + (
        "country_event = {\n"
        "\toption = {\n"
        "\t\tcapital_scope = {\n"
        "\t\t\tcreate_unit = {\n"
        f'\t\t\t\tdivision = "{_division("Guard")}"\n'
        "\t\t\t\towner = TST\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}"
    )


def _write_mod(tmp_path, events):
    write_under(
        tmp_path,
        "common/scripted_effects/tst_templates.txt",
        'OPR = {\n\tdivision_template = {\n\t\tname = "Guard"\n\t}\n}\n',
    )
    for index in range(events):
        write_under(tmp_path, f"events/TST_{index:02}.txt", _event(index))


def _foreign(index, filler):
    line = filler + 4
    return (
        f"events/TST_{index:02}.txt",
        line,
        f"{line}: create_unit uses division_template 'Guard', but only static "
        "definitions found for OPR; none found for TST",
    )


def _findings(tmp_path, workers=1):
    validator = Validator(str(tmp_path), use_colors=False, workers=workers)
    assert validator.workers == workers
    validator.run_all_validations()
    assert {issue.category for issue in validator._issues} <= {_FOREIGN}
    return [(i.file, i.line, i.message) for i in validator._issues]


def test_pooled_run_matches_the_in_process_run(tmp_path, monkeypatch):
    # Eleven event files plus the template file clear the pool threshold for
    # both the template index and the create_unit pass.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    _write_mod(tmp_path, 11)

    pooled = _findings(tmp_path, workers=2)
    assert pooled == _findings(tmp_path)
    assert sorted(pooled) == [_foreign(index, index) for index in range(11)]


def test_warm_cache_reuses_the_cold_scan_until_a_file_changes(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write_mod(tmp_path, 2)
    cold = _findings(tmp_path)
    assert sorted(cold) == [_foreign(0, 0), _foreign(1, 1)]

    build_nodes = oob._build_block_nodes
    template_entries = oob.division_template_entries

    def must_not_run(*_args):
        raise AssertionError("a warm run must reuse the cached scan")

    monkeypatch.setattr(oob, "_build_block_nodes", must_not_run)
    monkeypatch.setattr(oob, "division_template_entries", must_not_run)
    assert _findings(tmp_path) == cold

    parsed_line_counts = []

    def record(text):
        parsed_line_counts.append(text.count("\n"))
        return build_nodes(text)

    monkeypatch.setattr(oob, "_build_block_nodes", record)
    monkeypatch.setattr(oob, "division_template_entries", template_entries)
    write_under(tmp_path, "events/TST_00.txt", _event(3))
    assert sorted(_findings(tmp_path)) == [_foreign(0, 3), _foreign(1, 1)]
    # The edit rebuilds the stat-keyed template index (templates file and both
    # events) but re-parses only the edited event for its create_unit checks.
    assert sorted(parsed_line_counts) == [5, 10, 12, 12]
