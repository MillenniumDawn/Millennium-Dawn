"""Tests for the unannounced decision-unlock check.

A decision effect that sets a flag another decision waits on has unlocked that
decision. Only the inconsistent case is reported: a block that already announces
at least one unlock and misses a sibling gated on the flag it just set.
"""

import validate_decisions as V
from shared.suite import decision_factory, fake_decisions_validator


def _results_for(sources, monkeypatch, ai_only_by_category=()):
    factories = [decision_factory(src) for src in sources]
    validator = fake_decisions_validator("/tmp")
    monkeypatch.setattr(
        V, "parse_all_decision_factories", lambda mod_path, lowercase=False: factories
    )
    monkeypatch.setattr(
        validator,
        "_get_ai_only_by_category",
        lambda: set(ai_only_by_category),
        raising=False,
    )
    return validator._unannounced_decision_unlocks()


def _setter(*unlocks, flag="md_gate_flag"):
    lines = "".join(f"\t\tunlock_decision_tooltip = {u}\n" for u in unlocks)
    return (
        "md_setter = {\n"
        "\tcomplete_effect = {\n"
        f"\t\tset_country_flag = {flag}\n"
        f"{lines}"
        "\t}\n"
        "}"
    )


def _gated(token, block="visible", flag="md_gate_flag", negate=False):
    check = f"has_country_flag = {flag}"
    if negate:
        check = f"NOT = {{ {check} }}"
    return f"{token} = {{\n\t{block} = {{\n\t\t{check}\n\t}}\n}}"


def test_missed_sibling_is_flagged(monkeypatch):
    out = _results_for(
        [_setter("md_announced"), _gated("md_announced"), _gated("md_missed")],
        monkeypatch,
    )
    assert len(out) == 1
    assert "md_missed" in out[0]
    assert "md_announced" not in out[0].split("but not")[1]


def test_all_unlocks_announced_is_clean(monkeypatch):
    out = _results_for(
        [
            _setter("md_one", "md_two"),
            _gated("md_one"),
            _gated("md_two"),
        ],
        monkeypatch,
    )
    assert out == []


def test_block_announcing_nothing_is_not_flagged(monkeypatch):
    # MD does not announce every unlock; only inconsistency is a defect.
    out = _results_for([_setter(), _gated("md_missed")], monkeypatch)
    assert out == []


def test_negated_flag_gate_is_not_an_unlock(monkeypatch):
    # `NOT = { has_country_flag = X }` is satisfied until X is set, so setting
    # the flag hides that decision rather than unlocking it.
    out = _results_for(
        [
            _setter("md_announced"),
            _gated("md_announced"),
            _gated("md_hidden", negate=True),
        ],
        monkeypatch,
    )
    assert out == []


def test_available_gate_counts_as_an_unlock(monkeypatch):
    out = _results_for(
        [
            _setter("md_announced"),
            _gated("md_announced"),
            _gated("md_missed", block="available"),
        ],
        monkeypatch,
    )
    assert len(out) == 1
    assert "md_missed" in out[0]


def test_timed_set_flag_block_form_is_read(monkeypatch):
    setter = (
        "md_setter = {\n"
        "\tcomplete_effect = {\n"
        "\t\tset_country_flag = { flag = md_gate_flag days = 30 }\n"
        "\t\tunlock_decision_tooltip = md_announced\n"
        "\t}\n"
        "}"
    )
    out = _results_for(
        [setter, _gated("md_announced"), _gated("md_missed")], monkeypatch
    )
    assert len(out) == 1
    assert "md_missed" in out[0]


def test_ai_only_target_is_not_flagged(monkeypatch):
    out = _results_for(
        [_setter("md_announced"), _gated("md_announced"), _gated("md_ai")],
        monkeypatch,
        ai_only_by_category={"md_ai"},
    )
    assert out == []


def test_setter_gating_itself_is_not_flagged(monkeypatch):
    source = (
        "md_setter = {\n"
        "\tvisible = {\n\t\thas_country_flag = md_gate_flag\n\t}\n"
        "\tcomplete_effect = {\n"
        "\t\tset_country_flag = md_gate_flag\n"
        "\t\tunlock_decision_tooltip = md_announced\n"
        "\t}\n"
        "}"
    )
    out = _results_for([source, _gated("md_announced")], monkeypatch)
    assert out == []
