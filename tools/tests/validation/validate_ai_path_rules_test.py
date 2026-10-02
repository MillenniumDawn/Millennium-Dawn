"""Tests for `validate_ai_path_rules.py` (every playable country tree has an AI path rule)."""

import validate_ai_path_rules as V

TREE = "focus_tree = {{\n\tid = {tag}_focus\n\tcountry = {{\n\t\tfactor = 0\n\t\tmodifier = {{\n\t\t\tadd = 10\n\t\t\ttag = {tag}\n\t\t}}\n\t}}\n}}\n"
SHARED_TREE = "focus_tree = {\n\tid = shared\n\tcountry = {\n\t\tmodifier = { tag = AAA }\n\t\tmodifier = { tag = BBB }\n\t}\n}\n"
STATE = "state = {{\n\tid = 1\n\thistory = {{\n\t\towner = {tag}\n\t}}\n}}\n"
OPTION = '\toption = {{\n\t\tname = {name}\n\t\ttext = "X"\n\t\tdesc = "X"\n\t}}\n'
RULE = (
    '{tag}_ai_behavior = {{\n\tname = "{tag}_AI_BEHAVIOR"\n\tgroup = "RULE_GROUP_AI_BEHAVIOR"\n'
    "{options}"
    '\tdefault = {{\n\t\tname = NO_PATH\n\t\ttext = "X"\n\t\tdesc = "X"\n\t}}\n}}\n'
)
FULL_RULE = RULE.format(
    tag="AAA",
    options=OPTION.format(name="HISTORICAL") + OPTION.format(name="RANDOM_PATH"),
)
NO_HISTORICAL_RULE = RULE.format(tag="AAA", options=OPTION.format(name="RANDOM_PATH"))
NO_DEFAULT_RULE = (
    'AAA_ai_behavior = {\n\tname = "AAA_AI_BEHAVIOR"\n\tgroup = "RULE_GROUP_AI_BEHAVIOR"\n'
    + OPTION.format(name="HISTORICAL")
    + "}\n"
)


def _write(tmp_path, write_path, tree=None, states=None, rules=""):
    write_path(
        tmp_path,
        "common/national_focus/05_aaa.txt",
        TREE.format(tag="AAA") if tree is None else tree,
    )
    write_path(
        tmp_path,
        "history/states/1-A.txt",
        STATE.format(tag="AAA") if states is None else states,
    )
    write_path(tmp_path, "common/game_rules/00_game_rules.txt", rules)


def _run(tmp_path, staged_only=False):
    v = V.Validator(str(tmp_path), staged_only=staged_only)
    v.run_validations()
    return v._issues


def test_reports_tree_without_rule(tmp_path, write_path):
    _write(tmp_path, write_path)

    issues = _run(tmp_path)

    assert len(issues) == 1
    issue = issues[0]
    assert issue.category == "ai-path-rule-missing"
    assert issue.file == "common/national_focus/05_aaa.txt"
    assert issue.line == 3
    assert "'AAA'" in issue.message


def test_full_rule_is_clean(tmp_path, write_path):
    _write(tmp_path, write_path, rules=FULL_RULE)

    assert _run(tmp_path) == []


def test_rule_without_historical_is_incomplete(tmp_path, write_path):
    _write(tmp_path, write_path, rules=NO_HISTORICAL_RULE)

    issues = _run(tmp_path)

    assert [i.category for i in issues] == ["ai-path-rule-incomplete"]
    assert issues[0].file == "common/game_rules/00_game_rules.txt"
    assert issues[0].line == 1
    assert "HISTORICAL" in issues[0].message


def test_rule_without_default_is_incomplete(tmp_path, write_path):
    _write(tmp_path, write_path, rules=NO_DEFAULT_RULE)

    issues = _run(tmp_path)

    assert [i.category for i in issues] == ["ai-path-rule-incomplete"]
    assert "default" in issues[0].message


def test_shared_tree_is_skipped(tmp_path, write_path):
    _write(tmp_path, write_path, tree=SHARED_TREE)

    assert _run(tmp_path) == []


def test_tag_without_start_states_is_skipped(tmp_path, write_path):
    _write(tmp_path, write_path, states=STATE.format(tag="BBB"))

    assert _run(tmp_path) == []


def test_commented_owner_is_ignored(tmp_path, write_path):
    _write(tmp_path, write_path, states="#owner = AAA\n" + STATE.format(tag="BBB"))

    assert _run(tmp_path) == []


def test_empty_tree_is_clean(tmp_path):
    assert _run(tmp_path) == []


def test_staged_mode_skips_when_scope_untouched(tmp_path, write_path, monkeypatch):
    _write(tmp_path, write_path)
    write_path(tmp_path, "common/technologies/x.txt", "")
    monkeypatch.setenv("MD_STAGED_FILES", "common/technologies/x.txt")

    assert _run(tmp_path, staged_only=True) == []


def test_staged_mode_runs_when_game_rules_staged(tmp_path, write_path, monkeypatch):
    _write(tmp_path, write_path)
    monkeypatch.setenv("MD_STAGED_FILES", "common/game_rules/00_game_rules.txt")

    assert len(_run(tmp_path, staged_only=True)) == 1


def test_rules_parser():
    parsed = V._rules(FULL_RULE + "\n" + NO_DEFAULT_RULE.replace("AAA", "BBB"))

    assert parsed["AAA"] == (1, ["HISTORICAL", "RANDOM_PATH"], True)
    assert parsed["BBB"] == (21, ["HISTORICAL"], False)
