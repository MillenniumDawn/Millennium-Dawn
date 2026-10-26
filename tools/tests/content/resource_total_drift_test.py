"""The money system's resource total must cover every resource the game defines."""

from shared.paths import REPO_ROOT
from shared_utils import iter_statements, read_script


def _block(script, name):
    [body] = [body for key, _, body in iter_statements(script) if key == name]
    assert body is not None, name
    return body


def test_resource_total_sums_the_production_of_every_resource():
    money = read_script(str(REPO_ROOT / "common/scripted_effects/00_money_system.txt"))
    [total] = [
        _block(body, "total_resource_amount")
        for key, _, body in iter_statements(_block(money, "update_state_variables"))
        if key == "set_variable"
        and body is not None
        and any(name == "total_resource_amount" for name, _, _ in iter_statements(body))
    ]
    terms = list(iter_statements(total))
    assert [key for key, _, _ in terms] == ["value"] + ["add"] * (len(terms) - 1)
    resources = read_script(str(REPO_ROOT / "common/resources/00_resources.txt"))
    names = [key for key, _, _ in iter_statements(_block(resources, "resources"))]
    assert sorted(value for _, value, _ in terms) == sorted(
        f"resource_produced@{name}" for name in names
    )
