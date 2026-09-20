"""Tests for the achievement possible/happened original_tag redundancy check.

_MD_achievements.txt's `possible` block is evaluated once on game start and
stored in the save, so it gates which country may earn the achievement. A
country's `original_tag` never changes mid-game, so re-checking the same tag in
`happened` is redundant. `_scan_file` flags exactly those duplicate tags and
only them.
"""

from validate_achievements import _scan_file


def _achievement(name, possible, happened):
    return (
        f"{name} = {{\n"
        f"\tpossible = {{\n{possible}\t}}\n"
        f"\thappened = {{\n{happened}\t}}\n"
        f"}}\n"
    )


def _build(blocks):
    return "unique_id = MD_custom_achievements_1\n\n" + "\n".join(blocks)


def _scan(content, tmp_path):
    f = tmp_path / "achievements" / "MD_achievements.txt"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")
    return _scan_file((str(f), str(tmp_path)))


def test_flags_happened_redundant_tag(tmp_path):
    txt = _build(
        [
            _achievement(
                "rise_of_the_maltesers",
                "\t\toriginal_tag = MLT\n",
                "\t\thas_country_flag = USoE\n",
            ),
            _achievement(
                "make_america_great",
                "\t\toriginal_tag = USA\n",
                "\t\toriginal_tag = USA\n" "\t\tnum_of_nukes > 99\n",
            ),
        ]
    )
    findings = _scan(txt, tmp_path)
    # Only the redundant `original_tag = USA` in happened is flagged; neither
    # the MLT happened (no tag) nor the possible gates are.
    assert len(findings) == 1
    rel, line, tag = findings[0]
    assert rel == "achievements/MD_achievements.txt"
    assert tag == "USA"
    # The flagged line is the happened occurrence (2nd USA), not the possible one.
    assert txt.split("\n")[line - 1].strip() == "original_tag = USA"


def test_possible_or_gate_not_flagged_in_clean_happened(tmp_path):
    # OR-gated formable: happened states only the earned condition, no tag.
    txt = _build(
        [
            _achievement(
                "unite_yugoslavia",
                "\t\tOR = {\n"
                "\t\t\toriginal_tag = SER\n"
                "\t\t\toriginal_tag = CRO\n"
                "\t\t}\n",
                "\t\tis_yugoslavia_state_owned = yes\n",
            )
        ]
    )
    assert _scan(txt, tmp_path) == []


def test_happened_negation_outside_gate_not_flagged(tmp_path):
    # A `NOT = { original_tag = X }` that is not in the possible gate is a real
    # restriction (e.g. "form Europe without USA"), not a redundant re-check.
    txt = _build(
        [
            _achievement(
                "europe_but_no_usa",
                "\t\tOR = {\n"
                "\t\t\toriginal_tag = GER\n"
                "\t\t\toriginal_tag = FRA\n"
                "\t\t}\n",
                "\t\tNOT = { original_tag = USA }\n" "\t\thas_idea = super_power\n",
            )
        ]
    )
    assert _scan(txt, tmp_path) == []


def test_happened_tag_for_different_country_not_flagged(tmp_path):
    # happened gates a *different* tag than possible (a subject check), so the
    # possible tag admission is not duplicated; only a same-tag overlap flags.
    txt = _build(
        [
            _achievement(
                "puppeteer",
                "\t\toriginal_tag = GER\n",
                "\t\tSOV = { is_subject_of = GER }\n",
            )
        ]
    )
    assert _scan(txt, tmp_path) == []
