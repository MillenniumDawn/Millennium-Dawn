#!/usr/bin/env python3

"""Small helpers shared within tools/standardization."""


def format_elapsed(seconds: float) -> str:
    """Render an elapsed duration: `X.XX seconds` under a minute, else `Xm Y.YYs`."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    minutes = int(seconds // 60)
    return f"{minutes}m {seconds % 60:.2f}s"
