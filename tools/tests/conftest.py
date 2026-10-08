"""Suite-wide fixtures for every test under tools/tests."""

import os

import pytest


@pytest.fixture(autouse=True)
def restore_md_no_cache():
    """Undo production writes to MD_NO_CACHE so later tests keep their cache."""
    prior = os.environ.get("MD_NO_CACHE")
    yield
    if prior is None:
        os.environ.pop("MD_NO_CACHE", None)
    else:
        os.environ["MD_NO_CACHE"] = prior
