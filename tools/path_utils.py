#!/usr/bin/env python3
"""
Path utility functions for coding standards scripts.
"""


def clean_filepath(filepath):
    """Trim a filepath to start from the first known mod directory.

    Args:
        filepath (str): The full filepath to clean.

    Returns:
        str: The trimmed path, or the original if no known prefix is present.
    """
    for prefix in ("common", "events", "history", "interface"):
        if prefix in filepath:
            return prefix + filepath.split(prefix, 1)[1]
    return filepath
