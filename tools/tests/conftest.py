"""Suite-wide fixtures for every test under tools/tests."""

import multiprocessing
import os

import pytest


def pytest_configure():
    # An xdist worker is multi-threaded, and a child forked from one can deadlock.
    multiprocessing.set_start_method("spawn", force=True)


@pytest.fixture(autouse=True)
def restore_md_no_cache():
    """Undo production writes to MD_NO_CACHE so later tests keep their cache."""
    prior = os.environ.get("MD_NO_CACHE")
    yield
    if prior is None:
        os.environ.pop("MD_NO_CACHE", None)
    else:
        os.environ["MD_NO_CACHE"] = prior
