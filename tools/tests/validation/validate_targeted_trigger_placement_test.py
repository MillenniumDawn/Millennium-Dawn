"""Tests for the targeted-decision trigger-placement performance checks."""

from shared.suite import decision_factory, decisions_results_for

TARGETS_BLOCK = "\ttargets = {\n\t\tTAG\n\t}\n"
TARGET_ROOT_TRIGGER_BLOCK = "\ttarget_root_trigger = {\n\t\thas_capital = yes\n\t}\n"
ALLOWED_ALWAYS_NO = "\tallowed = {\n\t\talways = no\n\t}\n"
STATE_TARGET_YES = "\tstate_target = yes\n"

VISIBLE_ROOT_ONLY = "\tvisible = {\n\t\thas_capital = yes\n\t}\n"
VISIBLE_WITH_FROM = (
    "\tvisible = {\n\t\tFROM = {\n\t\t\tis_in_faction_with = ROOT\n\t\t}\n\t}\n"
)

TARGET_TRIGGER_NO_FROM = "\ttarget_trigger = {\n\t\thas_capital = yes\n\t}\n"
TARGET_TRIGGER_WITH_FROM = (
    "\ttarget_trigger = {\n\t\tFROM = {\n\t\t\tis_in_faction_with = ROOT\n\t\t}\n\t}\n"
)


def _dec(token, *field_blocks):
    return f"{token} = {{\n" + "".join(field_blocks) + "}"


# --- validate_root_only_visible_on_targeted ---


def test_root_only_check_skips_visible_referencing_from(monkeypatch):
    factory = decision_factory(_dec("dec_c1_clean", TARGETS_BLOCK, VISIBLE_WITH_FROM))
    assert (
        decisions_results_for(
            [factory], monkeypatch, "validate_root_only_visible_on_targeted"
        )
        == []
    )


def test_root_only_visible_flagged(monkeypatch):
    factory = decision_factory(
        _dec("dec_c1_violation", TARGETS_BLOCK, VISIBLE_ROOT_ONLY)
    )
    results = decisions_results_for(
        [factory], monkeypatch, "validate_root_only_visible_on_targeted"
    )
    assert len(results) == 1
    assert "dec_c1_violation" in results[0]
    assert "target_root_trigger" in results[0]


def test_root_only_check_exempts_allowed_always_no(monkeypatch):
    factory = decision_factory(
        _dec("dec_c1_alwaysno", TARGETS_BLOCK, VISIBLE_ROOT_ONLY, ALLOWED_ALWAYS_NO)
    )
    assert (
        decisions_results_for(
            [factory], monkeypatch, "validate_root_only_visible_on_targeted"
        )
        == []
    )


def test_root_only_check_exempts_state_target(monkeypatch):
    factory = decision_factory(
        _dec("dec_c1_statetarget", TARGETS_BLOCK, VISIBLE_ROOT_ONLY, STATE_TARGET_YES)
    )
    assert (
        decisions_results_for(
            [factory], monkeypatch, "validate_root_only_visible_on_targeted"
        )
        == []
    )


def test_root_only_check_ignores_non_targeted_decision(monkeypatch):
    factory = decision_factory(_dec("dec_c1_nontargeted", VISIBLE_ROOT_ONLY))
    assert (
        decisions_results_for(
            [factory], monkeypatch, "validate_root_only_visible_on_targeted"
        )
        == []
    )


def test_root_only_check_skips_when_target_root_trigger_present(monkeypatch):
    factory = decision_factory(
        _dec(
            "dec_c1_hastarget_root",
            TARGETS_BLOCK,
            TARGET_ROOT_TRIGGER_BLOCK,
            VISIBLE_ROOT_ONLY,
        )
    )
    assert (
        decisions_results_for(
            [factory], monkeypatch, "validate_root_only_visible_on_targeted"
        )
        == []
    )


# --- validate_from_checks_in_visible ---


def test_from_in_visible_check_skips_visible_without_from(monkeypatch):
    factory = decision_factory(
        _dec("dec_c2_clean", TARGET_TRIGGER_NO_FROM, VISIBLE_ROOT_ONLY)
    )
    assert (
        decisions_results_for([factory], monkeypatch, "validate_from_checks_in_visible")
        == []
    )


def test_from_in_visible_flagged_with_move_advice(monkeypatch):
    factory = decision_factory(
        _dec("dec_c2_violation", TARGET_TRIGGER_NO_FROM, VISIBLE_WITH_FROM)
    )
    results = decisions_results_for(
        [factory], monkeypatch, "validate_from_checks_in_visible"
    )
    assert len(results) == 1
    assert "dec_c2_violation" in results[0]
    assert "move" in results[0]


def test_from_in_visible_check_exempts_allowed_always_no(monkeypatch):
    factory = decision_factory(
        _dec(
            "dec_c2_alwaysno",
            TARGET_TRIGGER_NO_FROM,
            VISIBLE_WITH_FROM,
            ALLOWED_ALWAYS_NO,
        )
    )
    assert (
        decisions_results_for([factory], monkeypatch, "validate_from_checks_in_visible")
        == []
    )


def test_from_in_visible_check_exempts_state_target(monkeypatch):
    factory = decision_factory(
        _dec(
            "dec_c2_statetarget",
            TARGET_TRIGGER_NO_FROM,
            VISIBLE_WITH_FROM,
            STATE_TARGET_YES,
        )
    )
    assert (
        decisions_results_for([factory], monkeypatch, "validate_from_checks_in_visible")
        == []
    )


def test_from_in_visible_check_ignores_decision_without_target_trigger(monkeypatch):
    factory = decision_factory(_dec("dec_c2_nontargeted", VISIBLE_WITH_FROM))
    assert (
        decisions_results_for([factory], monkeypatch, "validate_from_checks_in_visible")
        == []
    )


def test_from_in_visible_identical_to_target_trigger_gets_deletion_advice(
    monkeypatch,
):
    factory = decision_factory(
        _dec("dec_c2_duplicate", TARGET_TRIGGER_WITH_FROM, VISIBLE_WITH_FROM)
    )
    results = decisions_results_for(
        [factory], monkeypatch, "validate_from_checks_in_visible"
    )
    assert len(results) == 1
    assert "dec_c2_duplicate" in results[0]
    assert "delete" in results[0]
    assert "identical" in results[0]
