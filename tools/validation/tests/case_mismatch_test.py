"""Unit tests for casefold_index and case_mismatch in validator_common."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from validator_common import case_mismatch, casefold_index


def test_casefold_index_maps_lower_to_canonical():
    idx = casefold_index(["FOO_Bar", "baz_QUX"])
    assert idx["foo_bar"] == "FOO_Bar"
    assert idx["baz_qux"] == "baz_QUX"


def test_case_mismatch_exact_returns_none():
    idx = casefold_index(["FOO_Bar"])
    assert case_mismatch("FOO_Bar", idx) is None


def test_case_mismatch_case_only_returns_canonical():
    idx = casefold_index(["FOO_Bar"])
    assert case_mismatch("foo_bar", idx) == "FOO_Bar"
    assert case_mismatch("FOO_BAR", idx) == "FOO_Bar"


def test_case_mismatch_absent_returns_none():
    idx = casefold_index(["FOO_Bar"])
    assert case_mismatch("totally_missing", idx) is None


def test_case_mismatch_empty_index():
    assert case_mismatch("anything", {}) is None
