import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ON_ACTIONS_ROOT = ROOT / "common" / "on_actions"
GPU_DRIVER_CALL = "gpu_development_monthly_driver = yes"
GPU_HOSTS = {
    "USA": "99_USA_on_actions.txt",
    "CAN": "MD_event_on_actions.txt",
    "KOR": "MD_event_on_actions.txt",
    "CHI": "99_CHI_on_actions.txt",
    "JAP": "99_JAP_on_actions.txt",
    "TAI": "02_oem_corporate_history_monthly_on_actions.txt",
}
CORPORATE_HOSTS = {
    "CAN": ("MD_event_on_actions.txt", "CAN_corporate_history_monthly_outcomes = yes"),
    "ENG": ("99_ENG_on_actions.txt", "ENG_corporate_history_monthly_outcomes = yes"),
    "JAP": ("99_JAP_on_actions.txt", "JAP_corporate_history_monthly_outcomes = yes"),
    "UKR": ("99_UKR_on_actions.txt", "UKR_corporate_history_monthly_outcomes = yes"),
}


def _extract_block(text: str, start: int) -> str:
    depth = 0
    opened = False
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
            opened = True
        elif text[index] == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start : index + 1]
    raise AssertionError("unterminated on-action block")


def _named_blocks(text: str, name: str) -> list[str]:
    pattern = re.compile(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{")
    return [_extract_block(text, match.start()) for match in pattern.finditer(text)]


def test_gpu_driver_uses_each_authoritative_monthly_host_once():
    assert not (ON_ACTIONS_ROOT / "02_gpu_development_on_actions.txt").exists()

    for tag, expected_filename in GPU_HOSTS.items():
        callers = []
        for path in sorted(ON_ACTIONS_ROOT.glob("*.txt")):
            blocks = _named_blocks(
                path.read_text(encoding="utf-8"), f"on_monthly_{tag}"
            )
            for block in blocks:
                if GPU_DRIVER_CALL in block:
                    assert block.count("\n\t\teffect = {") == 1
                    callers.append((path.name, block.count(GPU_DRIVER_CALL)))

        assert callers == [(expected_filename, 1)]


def test_corporate_drivers_reuse_existing_authoritative_monthly_hosts():
    dedicated_text = (
        ON_ACTIONS_ROOT / "02_oem_corporate_history_monthly_on_actions.txt"
    ).read_text(encoding="utf-8")
    for tag, (expected_filename, driver_call) in CORPORATE_HOSTS.items():
        assert _named_blocks(dedicated_text, f"on_monthly_{tag}") == []
        callers = []
        for path in sorted(ON_ACTIONS_ROOT.glob("*.txt")):
            blocks = _named_blocks(
                path.read_text(encoding="utf-8"), f"on_monthly_{tag}"
            )
            for block in blocks:
                if driver_call in block:
                    callers.append((path.name, block.count(driver_call)))

        assert callers == [(expected_filename, 1)]
