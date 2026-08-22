import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISR_EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "ISR_oem_effects.txt"
ON_ACTIONS_DIR = ROOT / "common" / "on_actions"
ISR_ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "99_ISR_on_actions.txt"
ISR_EVENTS_PATH = ROOT / "events" / "ISR_oem_events.txt"
USA_DECISIONS_PATH = (
    ROOT / "common" / "decisions" / "USA_corporate_systems_dashboard.txt"
)
LINUX_PARTICIPANT_TAGS = (
    "BRA",
    "CHI",
    "ENG",
    "FRA",
    "GER",
    "POL",
    "RAJ",
    "SOV",
    "USA",
    "VEN",
)


def _blocks(text: str, name: str) -> list[str]:
    pattern = re.compile(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{")
    blocks = []
    for match in pattern.finditer(text):
        depth = 0
        for index in range(text.index("{", match.start()), len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[match.start() : index + 1])
                    break
    return blocks


def _named_block(text: str, name: str) -> str:
    blocks = _blocks(text, name)
    assert blocks, f"missing block {name}"
    return blocks[0]


def test_isr_dispatch_respects_corporate_history_modes():
    effects = ISR_EFFECTS_PATH.read_text(encoding="utf-8")
    isr_on_actions = ISR_ON_ACTIONS_PATH.read_text(encoding="utf-8")
    events = ISR_EVENTS_PATH.read_text(encoding="utf-8")

    monthly_driver = _named_block(effects, "ISR_oem_monthly_driver")
    assert "corporate_history_enabled = yes" in monthly_driver
    assert "original_tag = ISR" in monthly_driver
    assert "NOT = { has_country_flag = collapsed_nation }" in monthly_driver
    assert "country_event = ISR_oem_events.90" not in monthly_driver
    assert "corporate_history_outcomes_only_enabled = yes" in monthly_driver
    assert monthly_driver.count("ISR_oem_reconstruct_history = yes") == 2
    assert "corporate_history_full_enabled = yes" in monthly_driver
    assert "ISR_oem_schedule_current_year_events = yes" in monthly_driver
    assert "ISR_oem_schedule_due_events = yes" in monthly_driver
    assert "id = ISR_oem_events.90" not in events

    monthly = _named_block(isr_on_actions, "on_monthly_ISR")
    assert monthly.count("ISR_oem_monthly_driver = yes") == 1


def test_country_local_hooks_replace_abk_singleton_dispatchers():
    isr = ISR_ON_ACTIONS_PATH.read_text(encoding="utf-8")
    linux_blocks = []
    for path in sorted(ON_ACTIONS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        for host in re.findall(r"(?m)^\s*(on_[A-Za-z0-9_]+)\s*=\s*\{", text):
            if host == "on_actions":
                continue
            linux_blocks.extend(
                block
                for block in _blocks(text, host)
                if "linux_system_monthly_driver = yes" in block
            )
    linux = "\n".join(linux_blocks)

    assert len(_blocks(isr, "on_monthly_ISR")) == 1
    assert not _blocks(linux, "on_monthly")
    assert {
        tag
        for tag in LINUX_PARTICIPANT_TAGS
        if len(_blocks(linux, f"on_monthly_{tag}")) == 1
    } == set(LINUX_PARTICIPANT_TAGS)
    assert "ISR_oem_monthly_driver = yes" in isr
    assert linux.count("linux_system_monthly_driver = yes") == len(
        LINUX_PARTICIPANT_TAGS
    )
    assert "ABK" not in isr
    assert "ABK" not in linux


def test_usa_policy_visibility_keeps_ibm_outside_recipient_or():
    decisions = USA_DECISIONS_PATH.read_text(encoding="utf-8")
    recipients = {
        "USA_corporate_policy_open_systems_procurement": {
            "USA_apple_state_initialized",
            "USA_nvidia_state_initialized",
        },
        "USA_corporate_policy_domestic_capacity_grants": {
            "USA_apple_state_initialized",
            "USA_nvidia_state_initialized",
            "USA_ti_state_initialized",
            "USA_micron_state_initialized",
            "USA_motorola_state_initialized",
        },
        "USA_corporate_policy_secure_federal_systems": {
            "USA_dell_state_initialized",
            "USA_motorola_state_initialized",
            "USA_google_state_initialized",
        },
        "USA_corporate_policy_advanced_computing_consortium": {
            "USA_nvidia_state_initialized",
            "USA_google_state_initialized",
            "USA_apple_state_initialized",
            "USA_ti_state_initialized",
            "USA_micron_state_initialized",
            "USA_motorola_state_initialized",
        },
    }

    for decision_id, expected_recipients in recipients.items():
        decision = _named_block(decisions, decision_id)
        visible = _named_block(decision, "visible")
        recipient_or = _named_block(visible, "OR")
        flags = set(re.findall(r"has_country_flag = ([A-Za-z0-9_]+)", recipient_or))

        assert visible.count("has_country_flag = USA_ibm_state_initialized") == 1
        assert "USA_ibm_state_initialized" not in flags
        assert flags == expected_recipients
