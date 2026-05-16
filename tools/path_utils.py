#!/usr/bin/env python3
"""
Path utility functions for coding standards scripts.
"""


def clean_filepath(filepath):
    """
    Clean up the filepath to show only from relevant directory onwards.

    Args:
        filepath (str): The full filepath to clean

    Returns:
        str: The cleaned filepath showing only from the relevant directory
    """
    for prefix in ("common", "events", "history", "interface"):
        if prefix in filepath:
            return prefix + filepath.split(prefix, 1)[1]
    return filepath
