"""Tests for validate_ai_weight_order (issue #5738).

AI weight modifiers run in order on a running total, so a positive `add` after
a `factor = 0` modifier brings the zeroed weight back.
"""

import pytest
import validate_ai_weight_order as V
from shared.suite import issue_rows, run_validator

ZERO = "\tmodifier = { factor = 0 has_war = yes }\n"
ADD = "\tmodifier = { add = 5 has_stability > 0.5 }\n"
NESTED_ADD = "\tmodifier = {\n\t\tfactor = 2\n\t\tsome_math = { add = 5 }\n\t}\n"


def _block(*modifiers, name="ai_chance"):
    return name + " = {\n\tbase = 10\n" + "".join(modifiers) + "}\n"


def _modifier(weight):
    return "\tmodifier = { " + weight + " has_war = yes }\n"


# name: (script, [(line of the first add after a zero, block name)])
_CASES = {
    "add after zero": (_block(ZERO, ADD), [(4, "ai_chance")]),
    "ai_will_do": (_block(ZERO, ADD, name="ai_will_do"), [(4, "ai_will_do")]),
    "decimal zero": (_block(_modifier("factor = 0.0"), ADD), [(4, "ai_chance")]),
    "once per block": (
        _block(ZERO, ADD, ADD) + _block(ADD, ZERO) + _block(ZERO, ADD),
        [(4, "ai_chance"), (15, "ai_chance")],
    ),
    "zero last": (_block(ADD, ZERO), []),
    "negative add": (_block(ZERO, _modifier("add = -5")), []),
    "zero add": (_block(ZERO, _modifier("add = 0")), []),
    "variable add": (_block(ZERO, _modifier("add = bonus_weight")), []),
    "factor after zero": (_block(ZERO, _modifier("factor = 2")), []),
    "factor 0.5": (_block(_modifier("factor = 0.5"), ADD), []),
    "factor 0.05": (_block(_modifier("factor = 0.05"), ADD), []),
    "factor 10": (_block(_modifier("factor = 10"), ADD), []),
    "root-level factor": ("ai_will_do = {\n\tfactor = 0\n" + ADD + "}\n", []),
    "add in a nested block": (_block(ZERO, NESTED_ADD), []),
    "zero outside a modifier": (_block("\tsome_block = { factor = 0 }\n", ADD), []),
    "zero and add together": (_block("\tmodifier = { factor = 0 add = 5 }\n"), []),
    "commented-out add": (_block(ZERO, "\t# modifier = { add = 5 }\n"), []),
    "unclosed block": ("ai_chance = {\n\tbase = 10\n" + ZERO + ADD, []),
}


@pytest.mark.parametrize(("script", "expected"), _CASES.values(), ids=_CASES)
def test_scan_text_reports_the_first_add_after_a_zero(script, expected):
    found = [(line, message.split()[0]) for line, message in V.scan_text(script)]
    assert found == expected


def test_validator_reports_the_same_cold_warm_and_uncached(
    tmp_path, write_path, issues_by_line, monkeypatch
):
    option = "\t\t".join(("", "ai_chance = {\n", "\tbase = 10\n", ZERO, ADD, "}\n"))
    write_path(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n\tid = foo.1\n\toption = {\n\t\tname = foo.1.a\n"
        + option
        + "\t}\n}\n",
    )
    write_path(tmp_path, "common/decisions/Clean.txt", _block(ADD, ZERO))
    scans = []
    scan_text = V.scan_text

    def counted(raw):
        scans.append(raw)
        return scan_text(raw)

    monkeypatch.setattr(V, "scan_text", counted)
    monkeypatch.delenv("MD_NO_CACHE", raising=False)

    cold = issue_rows(issues_by_line(V.Validator, tmp_path)[1])
    warm = issue_rows(issues_by_line(V.Validator, tmp_path)[1])
    assert len(scans) == 2
    uncached = run_validator(V.Validator, tmp_path)
    assert len(scans) == 4

    assert cold == warm == issue_rows(uncached)
    assert [(category, path, line) for category, _, path, line in cold] == [
        ("ai-weight-zero-then-add", "events/Ev.txt", 8)
    ]
    assert (uncached.warnings_found, uncached.errors_found) == (1, 0)
