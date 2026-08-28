"""Tests for the shared CPU budget that keeps tooling off the whole machine.

A full suite run fans out over every validator and each keeps its own worker
pool, so concurrency has to come out of one ceiling rather than each caller
sizing itself against the raw core count.
"""

import shared_utils as U


def _cores(monkeypatch, count):
    monkeypatch.setattr(U.os, "cpu_count", lambda: count)
    monkeypatch.delenv("MD_MAX_WORKERS", raising=False)
    monkeypatch.delenv("CI", raising=False)


def test_budget_leaves_a_quarter_of_the_cores_free(monkeypatch):
    _cores(monkeypatch, 24)
    assert U.cpu_budget() == 18
    _cores(monkeypatch, 8)
    assert U.cpu_budget() == 6


def test_budget_never_drops_below_one_core(monkeypatch):
    _cores(monkeypatch, 1)
    assert U.cpu_budget() == 1
    monkeypatch.setattr(U.os, "cpu_count", lambda: None)
    assert U.cpu_budget() == 1


def test_ci_runners_get_every_core(monkeypatch):
    _cores(monkeypatch, 4)
    monkeypatch.setenv("CI", "true")
    assert U.cpu_budget() == 4


def test_explicit_override_wins_over_the_share(monkeypatch):
    _cores(monkeypatch, 24)
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    assert U.cpu_budget() == 2
    monkeypatch.setenv("CI", "true")
    assert U.cpu_budget() == 2


def test_junk_override_falls_back_to_the_share(monkeypatch):
    _cores(monkeypatch, 24)
    for value in ("", "  ", "0", "-4", "half"):
        monkeypatch.setenv("MD_MAX_WORKERS", value)
        assert U.cpu_budget() == 18


def test_split_keeps_concurrency_times_workers_inside_the_budget(monkeypatch):
    _cores(monkeypatch, 24)
    for tasks in (1, 2, 5, 18, 35, 200):
        parallel, workers = U.split_cpu_budget(tasks)
        assert parallel >= 1 and workers >= 1
        assert parallel <= tasks
        assert parallel * workers <= U.cpu_budget()


def test_split_gives_a_single_task_the_whole_budget(monkeypatch):
    _cores(monkeypatch, 24)
    assert U.split_cpu_budget(1) == (1, 18)


def test_split_survives_a_one_core_budget(monkeypatch):
    _cores(monkeypatch, 1)
    assert U.split_cpu_budget(35) == (1, 1)
