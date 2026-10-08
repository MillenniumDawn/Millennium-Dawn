"""Tests for the category description image padding check (#4315)."""

import validate_decisions as V

_PMC_LOC = (
    "l_english:\n"
    ' pmc_global_management: "Global PMC management"\n'
    ' pmc_global_management_desc: "\\n£CHVK_desctext_pmc\\n\\n\\n\\nManage it."\n'
)


def _sizes(**sprites):
    return V.SpriteSizeIndex({}, sprites)


def test_banner_needs_one_newline_and_tall_picture_six():
    assert V._desc_image_min_newlines(73) == 1
    assert V._desc_image_min_newlines(225) == 6


def test_inline_text_icon_needs_no_newline():
    assert V._desc_image_min_newlines(20) == 0


def test_leading_icon_is_read_with_its_newline_count_and_line():
    assert V._leading_desc_icons(_PMC_LOC) == [
        ("pmc_global_management", 1, "CHVK_desctext_pmc", 3)
    ]


def test_icon_after_prose_is_not_a_leading_icon():
    text = 'l_english:\n cat_desc: "Some prose first.\\n£CHVK_desctext_pmc"\n'

    assert V._leading_desc_icons(text) == []


def test_tall_picture_with_banner_padding_is_reported():
    sprites = _sizes(GFX_CHVK_desctext_pmc=(480, 225))

    msg = V._desc_image_message(
        "pmc_global_management", 1, "CHVK_desctext_pmc", sprites
    )

    assert msg is not None
    assert "480x225" in msg
    assert "6" in msg


def test_tall_picture_with_six_newlines_is_not_reported():
    sprites = _sizes(GFX_CHVK_desctext_pmc=(480, 225))

    assert V._desc_image_message("cat", 6, "CHVK_desctext_pmc", sprites) is None


def test_banner_with_one_newline_is_not_reported():
    sprites = _sizes(GFX_MAIN_desctext_nato=(480, 73))

    assert V._desc_image_message("cat", 1, "MAIN_desctext_nato", sprites) is None


def test_unresolved_icon_is_not_reported():
    assert V._desc_image_message("cat", 0, "nothing", _sizes()) is None


def _validator(tmp_path, write_path, monkeypatch, loc):
    write_path(
        tmp_path,
        "common/decisions/categories/categories.txt",
        "pmc_global_management = {\n\ticon = GFX_decision_category_generic\n}\n",
    )
    write_path(tmp_path, "localisation/english/pmc_l_english.yml", loc)
    monkeypatch.setattr(
        V,
        "build_sprite_size_index",
        lambda *a, **k: _sizes(GFX_CHVK_desctext_pmc=(480, 225)),
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)
    validator.validate_category_desc_images()
    return validator


def test_validator_warns_on_the_category_description(tmp_path, write_path, monkeypatch):
    validator = _validator(tmp_path, write_path, monkeypatch, _PMC_LOC)

    assert [(i.category, i.severity, i.line) for i in validator._issues] == [
        ("category-desc-image-overlap", V.Severity.WARNING, 3)
    ]


def test_validator_ignores_a_description_that_is_not_a_category(
    tmp_path, write_path, monkeypatch
):
    loc = _PMC_LOC.replace("pmc_global_management", "some_focus")

    validator = _validator(tmp_path, write_path, monkeypatch, loc)

    assert validator._issues == []
