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
    rows = V._find_formable_commitment_rows(
        [_update_flag("AAA", 1, 3, 3), ungated], {}
    )
    assert any("AAA_integrate_BBB" in r and "missing commitment gate" in r for r in rows)


def test_id_collision_flagged():
    rows = V._find_formable_commitment_rows(
        [_update_flag("AAA", 1, 3, 3), _update_flag("BBB", 1, 5, 5)], {}
    )
    assert any("commit id 1 collides" in r for r in rows)


def test_gate_id_mismatch_flagged():
    # Gate cites id 2 but the formable's commits establish id 1.
    bad_gate = _factory(
        "\tAAA_integrate_BBB = {\n" + _gate(2, 3) + "\t}"
    )
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
    assert any("05_spain.txt: focus commit size 7" in r for r in rows)


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
