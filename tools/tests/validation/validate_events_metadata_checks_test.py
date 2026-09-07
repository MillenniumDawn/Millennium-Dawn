"""Event checks that walk metadata instead of a second body-list parse."""

from shared.suite import write_under_str as _write
from validate_events import Validator


def _validator(tmp_path):
    return Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def test_missing_triggered_only_uses_metadata_flags(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = foo.1\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = foo.2\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.2.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = foo.3\n"
        "\t#is_triggered_only = yes\n"
        "\toption = { name = foo.3.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_missing_triggered_only()
    joined = " ".join(i.message for i in v._issues)
    assert "foo.1" in joined
    assert "foo.3" in joined
    assert "foo.2" not in joined


def test_identical_event_bodies_are_not_collapsed(tmp_path):
    body = "country_event = {\n\toption = { name = dup.a }\n}\n"
    _write(tmp_path, "events/A.txt", body)
    _write(tmp_path, "events/B.txt", body)
    v = _validator(tmp_path)
    v.validate_missing_triggered_only()
    joined = " ".join(i.message for i in v._issues)
    assert "A.txt" in joined
    assert "B.txt" in joined


def test_missing_loc_skips_hidden_and_flags_option_names(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = vis.1\n"
        "\tis_triggered_only = yes\n"
        "\ttitle = vis.1.t\n"
        "\toption = { name = vis.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = hid.1\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\ttitle = hid.1.t\n"
        "\toption = { name = hid.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_missing_localisation()
    joined = " ".join(i.message for i in v._issues)
    assert "vis.1.t" in joined
    assert "vis.1.a" in joined
    assert "hid.1" not in joined


def test_unsupported_title_block_and_inline(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\ttitle = foo.1.t\n"
        "\ttitle = {\n"
        "\t\ttext = foo.1.t\n"
        "\t}\n"
        "\toption = { name = foo.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_unsupported_title_desc()
    assert [i.category for i in v._issues] == ["invalid-title-desc"]
    assert "foo.1" in v._issues[0].message


def test_loc_check_ignores_defined_and_dotless_references(tmp_path):
    """`title = FOO_TITLE` carries no namespace dot, so it is not an event key."""
    _write(
        tmp_path,
        "localisation/english/md_l_english.yml",
        'l_english:\n vis.1.d:0 "Body"\n',
    )
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = vis.1\n"
        "\tis_triggered_only = yes\n"
        "\ttitle = FOO_TITLE\n"
        "\tdesc = vis.1.d\n"
        "\toption = { name = vis.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_missing_localisation()
    assert [i.message for i in v._issues] == [
        "vis.1 - Ev.txt: missing loc key 'vis.1.a'"
    ]


def test_mtth_on_triggered_only_flagged_unless_in_a_random_events_pool(tmp_path):
    _write(
        tmp_path,
        "common/on_actions/00_on_actions.txt",
        "on_actions = {\n"
        "\ton_startup = {\n"
        "\t\trandom_events = {\n"
        "\t\t\t100 = pool.1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\tmean_time_to_happen = { days = 30 }\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = pool.1\n"
        "\tis_triggered_only = yes\n"
        "\tmean_time_to_happen = { days = 30 }\n"
        "\toption = { name = pool.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = auto.1\n"
        "\tmean_time_to_happen = { days = 30 }\n"
        "\toption = { name = auto.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_mtth_triggered_only()
    assert [i.message for i in v._issues] == ["foo.1 - Ev.txt"]
    assert v._issues[0].category == "mtth-triggered-only"


def test_hidden_events_with_options_flagged_and_counted(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = hid.1\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = hid.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = hid.2\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = hid.2.a }\n"
        "\toption = { name = hid.2.b }\n"
        "}\n"
        "country_event = {\n"
        "\tid = hid.3\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\timmediate = { add_political_power = 5 }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_hidden_event_options()
    assert [i.message for i in v._issues] == [
        "hid.1 - Ev.txt: 1 option block",
        "hid.2 - Ev.txt: 2 option blocks"
        " (only the first auto-fires — the rest are dead code)",
    ]


def test_hidden_event_loc_flagged_only_when_the_key_resolves(tmp_path):
    _write(
        tmp_path,
        "localisation/english/md_l_english.yml",
        'l_english:\n hid.1.t:0 "Title"\n',
    )
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = hid.1\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\ttitle = hid.1.t\n"
        "}\n"
        "country_event = {\n"
        "\tid = hid.2\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\ttitle = hid.2.t\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_hidden_event_localisation()
    assert [i.message for i in v._issues] == ["hid.1 - Ev.txt: hid.1.t"]
    assert v._issues[0].category == "hidden-event-localisation"


def test_duplicate_event_id_reports_the_overwriting_definition(tmp_path):
    body = (
        "country_event = {{\n"
        "\tid = {eid}\n"
        "\tis_triggered_only = yes\n"
        "\toption = {{ name = {eid}.a }}\n"
        "}}\n"
    )
    _write(
        tmp_path,
        "events/Ev.txt",
        body.format(eid="dup.1") + body.format(eid="uniq.1") + body.format(eid="dup.1"),
    )
    v = _validator(tmp_path)
    v.validate_duplicate_event_ids()
    assert [i.message for i in v._issues] == ["dup.1 - defined in Ev.txt and Ev.txt"]
    assert v._issues[0].category == "duplicate-event-id"


def test_undeclared_namespace_flagged(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "add_namespace = foo\n"
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = bar.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = bar.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = nodot\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = nodot.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_namespace_mismatch()
    assert [i.message for i in v._issues] == [
        "bar.1 - Ev.txt (namespace 'bar' not declared)"
    ]


def test_unreferenced_triggered_only_flagged_unless_namespace_is_dynamic(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "add_namespace = foo\n"
        "add_namespace = dyn\n"
        "country_event = {\n"
        "\tid = foo.9\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.9.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = dyn.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = dyn.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = foo.8\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.8.a }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/scripted_effects/00_fx.txt",
        "dispatch_effect = {\n"
        "\tcountry_event = dyn.[EVENT_ID]\n"
        "\tcountry_event = foo.8\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_triggered_only_unreferenced()
    assert [i.message for i in v._issues] == ["foo.9 - Ev.txt"]
    assert v._issues[0].category == "unreferenced-triggered-only"


def test_id_based_checks_skip_a_block_with_no_id(tmp_path):
    """A malformed block has no ID to report against; only the checks that can
    name it "unknown" may report on it."""
    _write(
        tmp_path,
        "events/Ev.txt",
        "add_namespace = foo\n"
        "country_event = {\n"
        "\tis_triggered_only = yes\n"
        "\thidden = yes\n"
        "\tmean_time_to_happen = { days = 30 }\n"
        "\ttitle = foo.1.t\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    v.validate_mtth_triggered_only()
    v.validate_duplicate_event_ids()
    v.validate_namespace_mismatch()
    v.validate_hidden_event_localisation()
    assert v._issues == []

    v.validate_hidden_event_options()
    assert [i.message for i in v._issues] == ["unknown - Ev.txt: 1 option block"]


def test_event_metadata_is_parsed_once_per_run(tmp_path):
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    assert v._get_event_metadata() is v._get_event_metadata()


def test_empty_event_file_is_skipped(tmp_path):
    _write(tmp_path, "events/Empty.txt", "")
    _write(
        tmp_path,
        "events/Ev.txt",
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\tfire_only_once = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    meta, _ = v._get_event_metadata()
    assert [ev["id"] for ev in meta] == ["foo.1"]
    assert v._get_fire_only_once_ids() == {"foo.1"}
    assert v._get_fire_only_once_ids() is v._fire_only_once_ids_cache


def test_indented_definitions_reach_the_metadata_checks(tmp_path):
    """Definitions are found by brace matching, not by column.

    64 event definitions in the mod are indented, and a column-anchored scan
    dropped every one of them from the duplicate-id and namespace checks.
    """
    _write(
        tmp_path,
        "events/Ev.txt",
        "add_namespace = foo\n"
        "\tcountry_event = {\n"
        "\t\tid = foo.1\n"
        "\t\tis_triggered_only = yes\n"
        "\t\toption = { name = foo.1.a }\n"
        "\t}\n"
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n"
        "\tcountry_event = {\n"
        "\t\tid = undeclared.1\n"
        "\t\tis_triggered_only = yes\n"
        "\t\toption = { name = undeclared.1.a }\n"
        "\t}\n",
    )
    v = _validator(tmp_path)
    meta, namespaces = v._get_event_metadata()

    assert namespaces == {"foo"}
    assert [m["id"] for m in meta] == ["foo.1", "foo.1", "undeclared.1"]

    v.validate_duplicate_event_ids()
    v.validate_namespace_mismatch()
    reported = " ".join(str(i) for i in v._issues)
    assert "foo.1" in reported, "the indented duplicate was not reported"
    assert (
        "undeclared.1" in reported
    ), "the indented namespace mismatch was not reported"


def test_nested_fire_id_is_not_adopted_by_a_malformed_parent(tmp_path):
    """An id belonging to a block fire is not the definition's own id.

    The malformed block has no id of its own but fires foo.1 from an option.
    Taking that id would invent a duplicate of the real foo.1 and label the
    malformed block with someone else's name instead of leaving it unknown.
    """
    _write(
        tmp_path,
        "events/Ev.txt",
        "add_namespace = foo\n"
        "country_event = {\n"
        "\tis_triggered_only = yes\n"
        "\toption = {\n"
        "\t\tname = broken.a\n"
        "\t\tcountry_event = { id = foo.1 days = 1 }\n"
        "\t}\n"
        "}\n"
        "country_event = {\n"
        "\tid = foo.1\n"
        "\tis_triggered_only = yes\n"
        "\toption = { name = foo.1.a }\n"
        "}\n",
    )
    v = _validator(tmp_path)
    meta, _ = v._get_event_metadata()

    assert [m["id"] for m in meta] == [None, "foo.1"]

    v.validate_duplicate_event_ids()
    assert not any(
        "foo.1" in str(issue) for issue in v._issues
    ), "the nested fire was counted as a second definition of foo.1"
