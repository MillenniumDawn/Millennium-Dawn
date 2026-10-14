"""Country pages must point at flag images that exist."""

import check_flag_images as flags
import pytest
from shared.suite import write_tree


@pytest.mark.parametrize(
    ("images", "report"),
    [
        pytest.param(
            ["one.png", "two.png"], (True, "Flag image references OK."), id="present"
        ),
        pytest.param(
            ["one.png"],
            (
                False,
                "Flag image validation failed:\n"
                "two.mdx: flag_image /assets/images/two.png missing at "
                "src/assets/images/two.png",
            ),
            id="missing",
        ),
    ],
)
def test_run(tmp_path, monkeypatch, images, report):
    monkeypatch.setattr(flags, "COUNTRIES_DIR", tmp_path / "countries")
    monkeypatch.setattr(flags, "ASSETS_ROOT", tmp_path / "assets")
    write_tree(
        tmp_path,
        {
            "countries/one.md": "flag_image: /assets/images/one.png\nother: x",
            "countries/two.mdx": "flag_image: '/assets/images/two.png'",
            **{f"assets/{image}": "" for image in images},
        },
    )

    assert flags.run() == report
