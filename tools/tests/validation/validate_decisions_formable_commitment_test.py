"""Tests for the formable commitment ratchet drift check."""

import validate_decisions as V


def _factory(body):
    return V.DecisionFactory(body, source_basename="formable_nation_decisions.txt")


def _gate(fid, size):
    return (
        "\t\tai_will_do = {\n"
        "\t\t\tbase = 10\n"
        "\t\t\tmodifier = {\n"
        "\t\t\t\tfactor = 0\n"
        f"\t\t\t\tNOT = {{ check_variable = {{ formable_committed_id = {fid} }} }}\n"
        "\t\t\t\tcheck_variable = {\n"
        "\t\t\t\t\tvar = formable_committed_size\n"
        f"\t\t\t\t\tvalue = {size}\n"
        "\t\t\t\t\tcompare = greater_than_or_equals\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}\n"
    )


def _commit(fid, size):
    return (
        "\t\t\thidden_effect = {\n"
        f"\t\t\t\tset_variable = {{ formable_committed_id = {fid} }}\n"
        f"\t\t\t\tset_variable = {{ formable_committed_size = {size} }}\n"
        "\t\t\t}\n"
    )


def _start(tag, fid, size):
    return _factory(
        f"\t{tag}_integrate_start = {{\n"
        + _gate(fid, size)
        + "\t\tcomplete_effect = {\n"
        + _commit(fid, size)
        + "\t\t}\n\t}"
    )


def _update_flag(tag, fid, size, state_count):
    entries = "".join(
        f"\t\t\t{100 + n} = {{ is_core_of = ROOT }}\n" for n in range(state_count)
    )
    return _factory(
        f"\t{tag}_update_flag = {{\n"
        + _gate(fid, size)
        + "\t\tavailable = {\n"
        + entries
        + "\t\t}\n"
        + "\t\tcomplete_effect = {\n"
        + _commit(fid, size)
        + "\t\t}\n\t}"
    )


def test_consistent_formable_clean():
    rows = V._find_formable_commitment_rows(
        [_start("AAA", 1, 3), _update_flag("AAA", 1, 3, 3)], {}
    )
    assert rows == []


def test_state_list_drift_flagged():
    # update_flag now lists 4 states but every literal still says 3.
    rows = V._find_formable_commitment_rows(
        [_start("AAA", 1, 3), _update_flag("AAA", 1, 3, 4)], {}
    )
    assert any("size literal 3" in r and "state count 4" in r for r in rows)


def test_missing_gate_flagged():
    ungated = _factory(
        "\tAAA_integrate_BBB = {\n"
        "\t\tai_will_do = { base = 10 }\n"
        "\t\tcomplete_effect = {\n\t\t\tadd_political_power = 1\n\t\t}\n\t}"
    )
    rows = V._find_formable_commitment_rows([_update_flag("AAA", 1, 3, 3), ungated], {})
    assert any(
        "AAA_integrate_BBB" in r and "missing commitment gate" in r for r in rows
    )


def test_id_collision_flagged():
    rows = V._find_formable_commitment_rows(
        [_update_flag("AAA", 1, 3, 3), _update_flag("BBB", 1, 5, 5)], {}
    )
    assert any("commit id 1 collides" in r for r in rows)


def test_gate_id_mismatch_flagged():
    # Gate cites id 2 but the formable's commits establish id 1.
    bad_gate = _factory("\tAAA_integrate_BBB = {\n" + _gate(2, 3) + "\t}")
    rows = V._find_formable_commitment_rows(
        [_update_flag("AAA", 1, 3, 3), bad_gate], {}
    )
    assert any("gate id 2 != AAA commit id 1" in r for r in rows)


def test_cross_reference_unknown_id_flagged():
    # An exemption clause citing an id no formable commits.
    stray = _factory(
        "\tAAA_integrate_BBB = {\n"
        + _gate(1, 3).replace(
            "\t\t\t}\n\t\t}\n",
            "\t\t\t\tNOT = {\n"
            "\t\t\t\t\tAND = {\n"
            "\t\t\t\t\t\tcheck_variable = { formable_committed_id = 99 }\n"
            "\t\t\t\t\t\thas_idea = EU_member\n"
            "\t\t\t\t\t}\n"
            "\t\t\t\t}\n"
            "\t\t\t}\n\t\t}\n",
        )
        + "\t}"
    )
    rows = V._find_formable_commitment_rows([_update_flag("AAA", 1, 3, 3), stray], {})
    assert any("unknown formable id 99" in r for r in rows)


def test_focus_commit_size_mismatch_flagged():
    focus = (
        "focus = {\n"
        "\thidden_effect = {\n"
        "\t\tset_variable = { formable_committed_id = 1 }\n"
        "\t\tset_variable = { formable_committed_size = 7 }\n"
        "\t}\n"
        "}\n"
    )
    rows = V._find_formable_commitment_rows(
        [_update_flag("AAA", 1, 3, 3)], {"05_spain.txt": focus}
    )
    assert any("05_spain.txt: commit size 7" in r for r in rows)


def test_focus_commit_consistent_clean():
    focus = (
        "focus = {\n"
        "\thidden_effect = {\n"
        "\t\tif = {\n"
        "\t\t\tlimit = {\n"
        "\t\t\t\tcheck_variable = {\n"
        "\t\t\t\t\tvar = formable_committed_size\n"
        "\t\t\t\t\tvalue = 3\n"
        "\t\t\t\t\tcompare = less_than\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t\tset_variable = { formable_committed_id = 1 }\n"
        "\t\t\tset_variable = { formable_committed_size = 3 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    rows = V._find_formable_commitment_rows(
        [_start("AAA", 1, 3), _update_flag("AAA", 1, 3, 3)], {"05_spain.txt": focus}
    )
    assert rows == []


# --- special (non-decision) formables: sentinel commit through commit_special_formable ---

_DEF_PATH = "common/scripted_effects/00_formable_effects.txt"


def _special_def(size=1000):
    return (
        "commit_special_formable = {\n"
        "\tif = {\n"
        "\t\tlimit = { has_idea = reshaping_national_identity }\n"
        "\t\tremove_ideas = reshaping_national_identity\n"
        "\t}\n"
        "\thidden_effect = {\n"
        "\t\tset_variable = { formable_committed_id = special_formable_id }\n"
        f"\t\tset_variable = {{ formable_committed_size = {size} }}\n"
        "\t}\n"
        "}\n"
    )


def _special_call(fid):
    return (
        f"\t\t\tset_temp_variable = {{ special_formable_id = {fid} }}\n"
        "\t\t\tcommit_special_formable = yes\n"
    )


def _special_rows(extra_texts, monkeypatch, ids, largest=83):
    monkeypatch.setattr(V, "_SPECIAL_FORMABLE_IDS", ids)
    return V._find_special_formable_rows(extra_texts, largest)


def test_special_commit_clean(monkeypatch):
    texts = {_DEF_PATH: _special_def(), "events/x.txt": _special_call(101)}
    assert _special_rows(texts, monkeypatch, {101: "X"}) == []


def test_special_unknown_id_flagged(monkeypatch):
    texts = {_DEF_PATH: _special_def(), "events/x.txt": _special_call(150)}
    rows = _special_rows(texts, monkeypatch, {101: "X"})
    assert any("unknown special formable id 150" in r for r in rows)


def test_special_orphan_setter_flagged(monkeypatch):
    texts = {
        _DEF_PATH: _special_def(),
        "events/x.txt": _special_call(101)
        + "\t\t\tset_temp_variable = { special_formable_id = 101 }\n"
        "\t\t\tadd_political_power = 1\n",
    }
    rows = _special_rows(texts, monkeypatch, {101: "X"})
    assert any(
        "1 special_formable_id setter(s) not immediately followed" in r for r in rows
    )


def test_special_call_without_setter_flagged(monkeypatch):
    texts = {
        _DEF_PATH: _special_def(),
        "events/x.txt": _special_call(101) + "\t\t\tcommit_special_formable = yes\n",
    }
    rows = _special_rows(texts, monkeypatch, {101: "X"})
    assert any(
        "1 commit_special_formable call(s) without a preceding" in r for r in rows
    )


def test_special_definition_drift_flagged(monkeypatch):
    texts = {_DEF_PATH: _special_def(size=500), "events/x.txt": _special_call(101)}
    rows = _special_rows(texts, monkeypatch, {101: "X"})
    assert any(
        "must set formable_committed_id = special_formable_id" in r for r in rows
    )


def test_special_definition_missing_flagged(monkeypatch):
    rows = _special_rows({"events/x.txt": _special_call(101)}, monkeypatch, {101: "X"})
    assert any(
        "expected exactly one commit_special_formable definition, found 0" in r
        for r in rows
    )


def test_unused_special_id_flagged(monkeypatch):
    texts = {_DEF_PATH: _special_def(), "events/x.txt": _special_call(101)}
    rows = _special_rows(texts, monkeypatch, {101: "X", 102: "Y"})
    assert any("special formable id 102 (Y) has no call site" in r for r in rows)


def test_special_size_must_exceed_largest_formable(monkeypatch):
    texts = {_DEF_PATH: _special_def(), "events/x.txt": _special_call(101)}
    rows = _special_rows(texts, monkeypatch, {101: "X"}, largest=1000)
    assert any(
        "does not exceed the largest formable state count 1000" in r for r in rows
    )


def test_sentinel_literal_outside_effect_flagged(monkeypatch):
    texts = {
        _DEF_PATH: _special_def(),
        "events/x.txt": _special_call(101)
        + "\t\t\tset_variable = { formable_committed_id = 105 }\n"
        "\t\t\tset_variable = { formable_committed_size = 1000 }\n",
    }
    rows = _special_rows(texts, monkeypatch, {101: "X"})
    assert any(
        "sentinel size literal 1000 outside commit_special_formable" in r for r in rows
    )
    assert any("special formable id 105 written inline" in r for r in rows)


def test_effect_tooltip_call_is_not_a_call_site(monkeypatch):
    texts = {
        _DEF_PATH: _special_def(),
        "events/x.txt": "\t\teffect_tooltip = {\n" + _special_call(101) + "\t\t}\n",
    }
    rows = _special_rows(texts, monkeypatch, {101: "X"})
    assert any("special formable id 101 (X) has no call site" in r for r in rows)


def test_special_call_in_formables_file_flagged():
    dec = _factory(
        "\tAAA_integrate_BBB = {\n"
        + _gate(1, 3)
        + "\t\tcomplete_effect = {\n"
        + _special_call(101)
        + "\t\t}\n\t}"
    )
    rows = V._find_formable_commitment_rows([_update_flag("AAA", 1, 3, 3), dec], {})
    assert any(
        "decision formables commit by id/size, not commit_special_formable" in r
        for r in rows
    )


def test_decision_commit_id_in_special_range_flagged():
    rows = V._find_formable_commitment_rows(
        [_start("AAA", 101, 3), _update_flag("AAA", 101, 3, 3)], {}
    )
    assert any("commit id 101 is in the reserved special range" in r for r in rows)


# --- full check on a checkout: skipped only when nothing mentions the ratchet ---


def _sync_issues(tmp_path, write_path, files):
    for relative, content in files.items():
        write_path(tmp_path, relative, content)
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1)
    validator.validate_formable_commitment_sync()
    return [issue.message for issue in validator._issues]


def test_sync_skips_checkout_without_ratchet_sites(tmp_path, write_path):
    files = {"common/decisions/other.txt": "cat = {\n}\n"}
    assert _sync_issues(tmp_path, write_path, files) == []


def test_sync_runs_special_checks_on_any_sentinel_mention(
    tmp_path, write_path, monkeypatch
):
    monkeypatch.setattr(V, "_SPECIAL_FORMABLE_IDS", {101: "X", 102: "Y"})
    files = {"events/x.txt": "x.1 = {\n" + _special_call(101) + "}\n"}
    issues = _sync_issues(tmp_path, write_path, files)
    assert any(
        "expected exactly one commit_special_formable definition, found 0" in m
        for m in issues
    )
    assert any("special formable id 102 (Y) has no call site" in m for m in issues)
