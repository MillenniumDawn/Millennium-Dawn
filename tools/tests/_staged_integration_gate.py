"""Shared skip-gate for the opt-in staged-validator integration tests."""

import os
import shutil
from unittest import SkipTest


def require_staged_integration_enabled() -> None:
    """Skip the caller unless opted into staged-validator integration runs.

    Shared by staged_validators_test.py and staged_validators_real_test.py,
    which both gate their real git-staging integration test the same way.
    """
    if not os.environ.get("MD_RUN_STAGED_INTEGRATION"):
        raise SkipTest(
            "set MD_RUN_STAGED_INTEGRATION=1 to run staged-validator integration"
        )
    if shutil.which("git") is None:
        raise SkipTest("git not available")
