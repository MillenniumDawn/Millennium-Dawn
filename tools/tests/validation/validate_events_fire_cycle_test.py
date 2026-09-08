"""Tests for validate_events.py: self-referencing events and event fire cycles.

Issue #3332. An event that fires itself parks a re-arming entry in the engine
event queue; self-reference is the length-1 case of a cycle in the event fire
graph, so one graph pass finds both. `scan_event_fire_edges` builds the graph
with call-site lines, `_iter_fire_cycles` enumerates the cycles through
`graphlib`, and `scan_event_fire_graph` keeps its old self-edge-free shape for
the date-gated scheduling check that consumes it.
"""

from validate_events import (
    _iter_fire_cycles,
    scan_event_fire_edges,
    scan_event_fire_graph,
)


def _event(eid, body):
    return f"country_event = {{\n\tid = {eid}\n\tis_triggered_only = yes\n{body}}}\n"


def _write(tmp_path, text, name="Ev.txt"):
    d = tmp_path / "events"
    d.mkdir(parents=True, exist_ok=True)
    path = d / name
    path.write_text(text, encoding="utf-8")
    return str(path)


# --- scan_event_fire_edges -------------------------------------------------


def test_block_form_self_fire_reports_call_site_line(tmp_path):
    # The `country_event = {` line is the call site, not the `id =` line under it.
    path = _write(
        tmp_path,
        _event(
            "foo.1",
            "\toption = {\n"
            "\t\tname = foo.1.a\n"
            "\t\thidden_effect = {\n"
            "\t\t\tcountry_event = {\n"
            "\t\t\t\tid = foo.1\n"
            "\t\t\t\tdays = 100\n"
            "\t\t\t}\n"
            "\t\t}\n"
            "\t}\n",
        ),
    )
    edges = scan_event_fire_edges((path, frozenset()))
    assert edges == [("foo.1", "foo.1", path, 7)]


def test_short_form_self_fire_reports_call_site_line(tmp_path):
    path = _write(
        tmp_path,
        _event(
            "foo.1",
            "\toption = {\n\t\tname = foo.1.a\n\t\tcountry_event = foo.1\n\t}\n",
        ),
    )
    edges = scan_event_fire_edges((path, frozenset()))
    assert edges == [("foo.1", "foo.1", path, 6)]


def test_self_fire_line_is_correct_for_a_later_definition(tmp_path):
    # Regression: the offset is measured from the definition's own line, so a
    # definition further down the file must not shift its call-site lines.
    text = _event("foo.1", "\toption = { name = foo.1.a }\n") + _event(
        "foo.2", "\toption = {\n\t\tname = foo.2.a\n\t\tcountry_event = foo.2\n\t}\n"
    )
    path = _write(tmp_path, text)
    edges = scan_event_fire_edges((path, frozenset()))
    assert edges == [("foo.2", "foo.2", path, 11)]


def test_fire_of_another_event_is_not_a_self_edge(tmp_path):
    path = _write(
        tmp_path,
        _event(
            "foo.1",
            "\toption = {\n\t\tname = foo.1.a\n\t\tcountry_event = foo.2\n\t}\n",
        ),
    )
    assert scan_event_fire_edges((path, frozenset())) == [("foo.1", "foo.2", path, 6)]


def test_interpolated_id_is_not_an_edge(tmp_path):
    # `country_event = UN.[ID]` has no literal target to resolve.
    path = _write(
        tmp_path,
        _event(
            "UN.1",
            "\toption = {\n\t\tname = UN.1.a\n\t\tcountry_event = UN.[ID]\n\t}\n",
        ),
    )
    assert scan_event_fire_edges((path, frozenset())) == []


def test_commented_out_self_fire_is_ignored(tmp_path):
    path = _write(
        tmp_path,
        _event(
            "foo.1",
            "\toption = {\n\t\tname = foo.1.a\n\t\t#country_event = foo.1\n\t}\n",
        ),
    )
    assert scan_event_fire_edges((path, frozenset())) == []


def test_fire_graph_drops_self_edges_but_keeps_the_rest(tmp_path):
    # scan_event_fire_graph feeds validate_date_gated_scheduling, which treats
    # an edge as "a parent schedules this child"; a self-fire schedules nothing.
    text = _event(
        "foo.1",
        "\toption = {\n"
        "\t\tname = foo.1.a\n"
        "\t\tcountry_event = foo.1\n"
        "\t\tcountry_event = foo.2\n"
        "\t}\n",
    )
    path = _write(tmp_path, text)
    assert scan_event_fire_graph((path, frozenset())) == [("foo.1", "foo.2")]
    assert [(p, c) for p, c, _f, _l in scan_event_fire_edges((path, frozenset()))] == [
        ("foo.1", "foo.1"),
        ("foo.1", "foo.2"),
    ]


def test_unreadable_file_yields_no_edges(tmp_path):
    assert scan_event_fire_edges((str(tmp_path / "missing.txt"), frozenset())) == []


# --- _iter_fire_cycles -----------------------------------------------------


def test_acyclic_graph_has_no_cycles():
    assert _iter_fire_cycles({"a": {"b"}, "b": {"c"}, "c": set()}) == []


def test_self_loop_is_a_length_one_cycle():
    assert _iter_fire_cycles({"a": {"a"}}) == [["a", "a"]]


def test_two_event_cycle_is_reported_in_fire_order():
    # The path reads as "a fires b fires a", not as a dependency chain.
    assert _iter_fire_cycles({"a": {"b"}, "b": {"a"}}) == [["a", "b", "a"]]


def test_longer_cycle_is_reported_whole():
    assert _iter_fire_cycles({"a": {"b"}, "b": {"c"}, "c": {"a"}}) == [
        ["a", "b", "c", "a"]
    ]


def test_every_cycle_in_one_component_is_reported():
    # Two distinct cycles share the node `a`; peeling one edge must not hide
    # the other.
    cycles = _iter_fire_cycles({"a": {"b", "c"}, "b": {"a"}, "c": {"a"}})
    assert sorted(cycles) == [["a", "b", "a"], ["a", "c", "a"]]


def test_self_loop_and_multi_cycle_are_both_reported():
    cycles = _iter_fire_cycles({"a": {"b"}, "b": {"a"}, "x": {"x"}})
    assert sorted(cycles) == [["a", "b", "a"], ["x", "x"]]


def test_a_node_outside_the_cycle_is_not_reported():
    cycles = _iter_fire_cycles({"a": {"b"}, "b": {"a"}, "d": {"a"}})
    assert cycles == [["a", "b", "a"]]
    assert all("d" not in c for c in cycles)


def test_child_with_no_outgoing_edges_terminates():
    # A child that never appears as a key must still be registered as a node.
    assert _iter_fire_cycles({"a": {"b"}}) == []


def test_dense_graph_terminates():
    # Every node fires every node, self-fires included: the walk must drain
    # rather than spin, so it is bounded by the edge count.
    nodes = [str(i) for i in range(6)]
    graph = {n: set(nodes) for n in nodes}
    cycles = _iter_fire_cycles(graph)
    assert cycles
    assert len(cycles) <= len(nodes) * len(nodes)
    assert _iter_fire_cycles({n: set(nodes) for n in nodes}) == cycles


def test_cycle_rotation_is_canonical_and_stable():
    # graphlib reports whichever rotation its walk entered; the finding's
    # anchor and message must not move between runs.
    assert _iter_fire_cycles({"b": {"c"}, "c": {"a"}, "a": {"b"}}) == [
        ["a", "b", "c", "a"]
    ]
    assert _iter_fire_cycles({"c": {"a"}, "a": {"b"}, "b": {"c"}}) == [
        ["a", "b", "c", "a"]
    ]


def test_self_fire_inside_a_quoted_string_is_not_an_edge(tmp_path):
    # The self-fire check is an ERROR; a log string mentioning the keyword
    # must not block a commit.
    path = _write(
        tmp_path,
        _event(
            "q.1",
            "\toption = {\n"
            "\t\tname = q.1.a\n"
            '\t\tlog = "hi country_event = q.1 bye"\n'
            "\t}\n",
        ),
    )
    assert scan_event_fire_edges((path, frozenset())) == []


def test_line_is_right_when_the_opening_brace_is_on_its_own_line(tmp_path):
    # `<kw> = \n {` is legal: the block pattern's `\s*` spans the newline, so
    # offsets must be measured from the brace, not from the keyword.
    text = (
        "country_event =\n"
        "{\n"
        "\tid = z.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n"
        "\t\tname = z.1.a\n"
        "\t\tcountry_event = z.1\n"
        "\t}\n"
        "}\n"
    )
    path = _write(tmp_path, text)
    assert scan_event_fire_edges((path, frozenset())) == [("z.1", "z.1", path, 7)]


# --- validator wiring ------------------------------------------------------


def _run(tmp_path, write_path, monkeypatch, script, **kwargs):
    import validate_events as V
    import validator_common

    monkeypatch.setattr(validator_common, "_LOG_LEVEL", "INFO")
    write_path(tmp_path, "events/test_events.txt", script)
    validator = V.Validator(
        str(tmp_path), use_colors=False, workers=1, no_cache=True, **kwargs
    )
    return validator


def test_validator_reports_a_self_fire_as_an_error(tmp_path, write_path, monkeypatch):
    validator = _run(
        tmp_path,
        write_path,
        monkeypatch,
        _event(
            "foo.1",
            "\toption = {\n\t\tname = foo.1.a\n\t\tcountry_event = foo.1\n\t}\n",
        ),
    )
    validator.validate_self_referencing_events()

    assert [(i.severity, i.category) for i in validator._issues] == [
        ("error", "self-referencing-event")
    ]
    assert validator._issues[0].file == "events/test_events.txt"
    assert validator._issues[0].line == 6
    assert "fires itself" in validator._issues[0].message


def test_validator_stays_quiet_when_no_event_fires_itself(
    tmp_path, write_path, monkeypatch
):
    validator = _run(
        tmp_path,
        write_path,
        monkeypatch,
        _event(
            "foo.1",
            "\toption = {\n\t\tname = foo.1.a\n\t\tcountry_event = foo.2\n\t}\n",
        ),
    )
    validator.validate_self_referencing_events()

    assert validator._issues == []


def test_fire_cycle_check_is_opt_in(tmp_path, write_path, monkeypatch):
    script = _event(
        "foo.1", "\toption = {\n\t\tname = foo.1.a\n\t\tcountry_event = foo.2\n\t}\n"
    ) + _event(
        "foo.2", "\toption = {\n\t\tname = foo.2.a\n\t\tcountry_event = foo.1\n\t}\n"
    )

    off = _run(tmp_path, write_path, monkeypatch, script)
    off.run_validations()
    assert not [i for i in off._issues if i.category == "event-fire-cycle"]

    on = _run(tmp_path, write_path, monkeypatch, script, fire_cycles=True)
    on.validate_event_fire_cycles()
    cycles = [i for i in on._issues if i.category == "event-fire-cycle"]
    assert len(cycles) == 1
    assert cycles[0].severity == "warning"
    assert "foo.1 -> foo.2 -> foo.1" in cycles[0].message
