"""Live event content that must pass the corruption PP-cost guard check."""

import validate_events as V
from shared.paths import REPO_ROOT
from shared.suite import build_validator, read_text


def test_libya_event_exclusion_is_recognized_in_the_live_tree():
    assert "LibyaRandomEvents.16.c" in read_text(REPO_ROOT / "events/Libya.txt")
    validator = build_validator(V.Validator, REPO_ROOT, check_corruption_pp_costs=True)

    validator.validate_corruption_pp_cost()

    assert not [
        issue
        for issue in validator._issues
        if issue.file == "events/Libya.txt"
        and "LibyaRandomEvents.16.c" in issue.message
    ]
