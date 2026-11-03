"""Source contracts for historical AI Pakistan's coalition partner selection."""

import pytest
from shared.paths import REPO_ROOT
from shared_utils import iter_statements, read_script

EFFECTS = read_script(
    str(REPO_ROOT / "common/scripted_effects/00_MD_politicsview_scripted_effects.txt")
)
DECISIONS = read_script(str(REPO_ROOT / "common/decisions/Coalition Decisions.txt"))
ELECTIONS = read_script(str(REPO_ROOT / "events/MD_Elections.txt"))


def _block(script, name):
    blocks = [body for key, _, body in iter_statements(script) if key == name]
    assert len(blocks) == 1 and blocks[0] is not None, name
    return blocks[0]


def _walk(script):
    for key, value, body in iter_statements(script):
        yield key, value, body
        if body is not None:
            yield from _walk(body)


def _matches(script, context):
    def value(token):
        return context.get(token, int(token) if token.isdigit() else token)

    def statement(key, scalar, body):
        if key == "NOT":
            return not _matches(body, context)
        if key == "AND":
            return _matches(body, context)
        if key == "OR":
            return any(statement(*item) for item in iter_statements(body))
        if key == "check_variable":
            [(variable, expected, _)] = list(iter_statements(body))
            return value(variable) == value(expected)
        if key == "original_tag":
            return context["original_tag"] == scalar
        if key == "is_ai":
            return context["is_ai"] == (scalar == "yes")
        if key == "is_historical_focus_on":
            return context["historical"] == (scalar == "yes")
        raise AssertionError(f"Unexpected partner gate: {key}")

    return all(statement(*item) for item in iter_statements(script))


AFFINITY = _block(EFFECTS, "make_affinity_arrays")
PARTNER_LOOP = _block(AFFINITY, "for_loop_effect")
PARTNER_LIMIT = _block(_block(PARTNER_LOOP, "if"), "limit")


@pytest.mark.parametrize(
    ("tag", "ai", "historical", "party", "allowed"),
    [
        ("PAK", True, True, 11, False),
        ("PAK", False, True, 11, True),
        ("PAK", True, False, 11, True),
        ("RAJ", True, True, 11, True),
        ("PAK", True, True, 12, True),
    ],
)
def test_coalition_partner_scope(tag, ai, historical, party, allowed):
    context = {
        "original_tag": tag,
        "is_ai": ai,
        "historical": historical,
        "v": party,
        "max_index_1": 22,
        "max_index_2": 6,
    }
    assert _matches(PARTNER_LIMIT, context) is allowed


def test_both_ai_formation_paths_use_filtered_affinities():
    normal = _block(EFFECTS, "AI_setup_government")
    timeout = _block(_block(DECISIONS, "coalition_decisions"), "coalition_countdown")
    for path in (normal, timeout):
        calls = [(key, value) for key, value, _ in _walk(path)]
        assert calls.count(("make_affinity_arrays", "yes")) == 1
        assert ("reduce_affinity_array_party_1", "yes") in calls
        assert ("reduce_affinity_array_party_2", "yes") in calls
        assert path.index("make_affinity_arrays = yes") < path.index(
            "party_1_affinity_array^i1 > 0"
        )
        assert "party_2_affinity_array^i2 > 0" in path


def test_player_caliphate_invitation_remains_available():
    invite = _block(_block(DECISIONS, "coalition_decisions"), "Caliphate_invite")
    assert ("country_event", "coalition.11", None) in list(_walk(invite))
    assert ("base", "0", None) in list(_walk(_block(invite, "ai_will_do")))
    events = [
        body for key, _, body in iter_statements(ELECTIONS) if key == "country_event"
    ]
    invitation = next(
        body
        for body in events
        if ("id", "coalition.11", None) in list(iter_statements(body))
    )
    assert ("gov_coalition_array", "11", None) in list(_walk(invitation))


def test_re_election_promotes_only_an_existing_coalition_member():
    events = [
        body for key, _, body in iter_statements(ELECTIONS) if key == "country_event"
    ]
    re_election = next(
        body
        for body in events
        if ("id", "MD4_election.2", None) in list(iter_statements(body))
    )
    assert ("update_coalition_leader", "yes", None) in list(_walk(re_election))
    leader = _block(EFFECTS, "update_coalition_leader")
    members = _block(leader, "if")
    additions = [body for key, _, body in _walk(members) if key == "add_to_temp_array"]
    coalition = [list(iter_statements(body)) for body in additions if body]
    assert [
        items[0][1] for items in coalition if items[0][0] == "full_coalition_temp"
    ] == [
        "ruling_party",
        "v",
    ]
    assert ("array", "gov_coalition_array", None) in list(_walk(members))
