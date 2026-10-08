"""Shared fixtures for validator unit tests."""

import pytest


@pytest.fixture
def no_vanilla_gfx(monkeypatch):
    import validate_gfx_references as vg

    monkeypatch.setattr(vg, "_vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(vg, "_load_vanilla_sprite_manifest", lambda: frozenset())
    monkeypatch.setattr(vg, "_vanilla_gui_ref_index", lambda: {})


@pytest.fixture
def pool_sizes(monkeypatch):
    """Record the size of every worker pool validator_common starts."""
    import validator_common

    real_pool = validator_common.Pool
    sizes = []

    def counting_pool(*args, **kwargs):
        sizes.append(kwargs.get("processes"))
        return real_pool(*args, **kwargs)

    monkeypatch.setattr(validator_common, "Pool", counting_pool)
    return sizes


@pytest.fixture
def write_path():
    from shared.suite import write_text

    def write(root, relative_path, content=""):
        return write_text(root / relative_path, content)

    return write


@pytest.fixture
def country_file(tmp_path):
    def write(body, name="ARA - Arabistan.txt"):
        d = tmp_path / "history" / "countries"
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        p.write_text(body, encoding="utf-8")
        return str(p)

    return write


@pytest.fixture
def issues_by_line():
    def run(validator_cls, root):
        validator = validator_cls(str(root), use_colors=False, workers=1)
        validator.run_validations()
        return {
            (issue.category, issue.line): issue for issue in validator._issues
        }, validator

    return run


@pytest.fixture
def gfx_notices(monkeypatch):
    from validate_gfx_references import Validator

    def collect(tmp_path, check):
        logged = []
        validator = Validator(str(tmp_path), use_colors=False)
        monkeypatch.setattr(validator, "log", lambda msg, *a, **k: logged.append(msg))
        check(validator)
        return logged

    return collect
