"""Regressions for the shared meta_effect/meta_trigger name scanner.

Guards the quoted-template coverage folded into validator_common after the
unused-scripted validator's local copy was removed, so both consumers (unused
scripted, scripted localisation) see quoted references like
`"[?token]_unlock_btn_enabled"`.
"""

import validator_common as VC


def _write(tmp_path, body):
    path = tmp_path / "meta.txt"
    path.write_text(body)
    return str(path)


def test_bare_template_reference(tmp_path):
    path = _write(
        tmp_path,
        "meta_effect = { text = { set_leader_[IDEOLOGY] = yes } }\n",
    )
    assert VC.scan_meta_constructed_names(
        [path], {"set_leader_communism", "unrelated_effect"}
    ) == {"set_leader_communism"}


def test_quoted_leading_placeholder_reference(tmp_path):
    # The bare `[TRIG] = yes` alone anchors nothing; the constant suffix lives
    # only inside the quoted assignment. This is the case the local copy caught
    # and the shared helper previously missed.
    path = _write(
        tmp_path,
        "meta_trigger = {\n"
        "\ttext = { [TRIG] = yes }\n"
        '\tTRIG = "[?global.tokens^v.GetTokenKey]_unlock_btn_enabled"\n'
        "}\n",
    )
    assert VC.scan_meta_constructed_names(
        [path], {"mio_x_unlock_btn_enabled", "other_trigger"}
    ) == {"mio_x_unlock_btn_enabled"}


def test_no_meta_keyword_scans_nothing(tmp_path):
    path = _write(tmp_path, 'foo = "[?bar]_unlock_btn_enabled"\n')
    assert VC.scan_meta_constructed_names([path], {"x_unlock_btn_enabled"}) == set()
