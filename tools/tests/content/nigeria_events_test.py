"""Source contracts for Nigerian investigation rewards and Ambazonia responses."""

import pytest
from shared.paths import REPO_ROOT
from shared_utils import iter_statements, read_script

SCRIPT = read_script(str(REPO_ROOT / "events/Nigeria.txt"))


def _option(event_id, option_id):
    [event] = [
        body
        for key, _, body in iter_statements(SCRIPT)
        if key == "country_event"
        and body
        and ("id", event_id, None) in list(iter_statements(body))
    ]
    [option] = [
        body
        for key, _, body in iter_statements(event)
        if key == "option"
        and body
        and ("name", option_id, None) in list(iter_statements(body))
    ]
    return option


@pytest.mark.parametrize(
    "variable", ["party_popularity_increase", "temp_outlook_increase"]
)
def test_explosion_investigation_rewards_support(variable):
    option = _option("nigeria_md.106", "nigeria_md.106.a")
    values = [
        value
        for key, _, body in iter_statements(option)
        if key == "set_temp_variable" and body
        for name, value, _ in iter_statements(body)
        if name == variable
    ]
    assert values == ["0.02"]
    assert ("change_relative_party_popularity", "yes", None) in list(
        iter_statements(option)
    )


@pytest.mark.parametrize(
    ("option_id", "followup"),
    [
        ("nigeria_ambazonia.4.a", "nigeria_ambazonia.5"),
        ("nigeria_ambazonia.4.b", "nigeria_ambazonia.6"),
    ],
    ids=["fight", "concede"],
)
def test_ambazonia_responses_notify_cameroon(option_id, followup):
    option = _option("nigeria_ambazonia.4", option_id)
    [receiver] = [
        body for key, _, body in iter_statements(option) if key == "CAM" and body
    ]
    [dispatch] = [
        body
        for key, _, body in iter_statements(receiver)
        if key == "country_event" and body
    ]
    assert list(iter_statements(dispatch)) == [
        ("id", followup, None),
        ("days", "5", None),
    ]
