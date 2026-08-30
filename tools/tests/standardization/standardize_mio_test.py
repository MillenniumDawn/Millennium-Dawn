"""Tests for the MIO standardizer.

Regression: a trait `parent = { traits = { A B } }` wraps a nested block. The
token-list normalizer used to flatten its inner `=`/`{`/`}` into stray tokens,
which reformatted differently on a second run (non-idempotent). The standardizer
must leave nested blocks intact and produce run2 == run1 exactly.
"""

from standardize_mio import MIOStandardizer

# A realistic organization block with a trait whose `parent` wraps a nested
# `traits = { ... }` block (the non-idempotency trigger).
_MIO = """\
TST_utility_vehicle_manufacturer = {
	allowed = { original_tag = TST }
	name = TST_utility_vehicle_manufacturer
	icon = GFX_idea_generic_manufacturer

	research_categories = {
		armor
	}

	trait = {
		token = TST_ya126_heritage
		name = TST_ya126_heritage
		icon = GFX_generic_mio_trait_icon_reliability

		position = { x = 0 y = 0 }

		equipment_bonus = { reliability = 0.05 }

		on_complete = { expenditure_for_mio_upgrade = yes }

		ai_will_do = { base = 1 }
	}

	trait = {
		token = TST_field_reliability
		name = TST_field_reliability
		icon = GFX_generic_mio_trait_icon_reliability

		parent = { traits = { TST_multifuel_engine TST_hdrive_traction } }
		relative_position_id = TST_ya126_heritage
		position = { x = 0 y = 2 }

		equipment_bonus = { reliability = 0.05 }

		on_complete = { expenditure_for_mio_upgrade = yes }

		ai_will_do = { base = 1 }
	}
}
"""


def _standardize(path):
    std = MIOStandardizer()
    std.standardize_file(str(path), str(path))
    return path.read_text(encoding="utf-8")


def test_nested_parent_block_idempotent(tmp_path):
    src = tmp_path / "mio.txt"
    src.write_text(_MIO, encoding="utf-8")
    run1 = _standardize(src)
    run2 = _standardize(src)
    assert run1 == run2


def test_nested_parent_block_content_preserved(tmp_path):
    src = tmp_path / "mio.txt"
    src.write_text(_MIO, encoding="utf-8")
    out = _standardize(src)
    # The nested block survives intact, not flattened into stray `=`/`{`/`}` tokens.
    assert "parent = { traits = { TST_multifuel_engine TST_hdrive_traction } }" in out
    assert out.count("token = TST_ya126_heritage") == 1
    assert out.count("token = TST_field_reliability") == 1
    # No line degenerates to a lone `=` (the old flattening symptom).
    assert not any(line.strip() == "=" for line in out.splitlines())
