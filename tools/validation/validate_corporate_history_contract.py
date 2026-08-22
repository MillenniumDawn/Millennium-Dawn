#!/usr/bin/env python3
"""Validate the Corporate History framework contract."""

from __future__ import annotations

from corporate_history.model import (
    _NATIVE_ARRAY_BLOCK_EFFECTS,
    _NATIVE_CONTRACT_ROLES,
    _NATIVE_VARIABLE_BLOCK_EFFECTS,
    _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS,
    ChainConfig,
    _collect_native_write_tokens,
    _is_repeatable_decision,
    _removes_active_decision,
)
from corporate_history.validator import Validator
from validator_common import run_validator_main

__all__ = [
    "_NATIVE_ARRAY_BLOCK_EFFECTS",
    "_NATIVE_CONTRACT_ROLES",
    "_NATIVE_VARIABLE_BLOCK_EFFECTS",
    "_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS",
    "ChainConfig",
    "Validator",
    "_collect_native_write_tokens",
    "_is_repeatable_decision",
    "_removes_active_decision",
]


if __name__ == "__main__":
    run_validator_main(Validator, "Validate the corporate-history framework contract")
