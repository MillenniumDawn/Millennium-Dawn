"""Regression for the pre-commit staged-standardizer wrapper.

A standardizer returning False (a non-raising failure such as a write error) must
surface as an error, not get silently counted as "not modified" — otherwise the
hook exits 0 and the commit proceeds with an unstandardized file.
"""

import pytest
import standardize_staged


def test_false_standardizer_return_raises(tmp_path, monkeypatch):
    f = tmp_path / "x.txt"
    f.write_text("idea = { }\n", encoding="utf-8")
    monkeypatch.setattr(
        standardize_staged.IdeaStandardizer,
        "standardize_file",
        lambda self, inp, out: False,
    )
    with pytest.raises(RuntimeError):
        standardize_staged.standardize_file(str(f), "idea")
