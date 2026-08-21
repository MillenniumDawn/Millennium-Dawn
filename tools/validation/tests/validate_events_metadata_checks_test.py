"""Event checks that walk metadata instead of a second body-list parse."""

from shared_utils import write_text_under
from validate_events import Validator


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    write_text_under(str(p), str(tmp_path), body)
    return str(p)


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
