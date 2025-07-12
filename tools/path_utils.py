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
    if 'common' in filepath:
        return 'common' + filepath.split('common', 1)[1]
    elif 'events' in filepath:
        return 'events' + filepath.split('events', 1)[1]
    elif 'history' in filepath:
        return 'history' + filepath.split('history', 1)[1]
    elif 'interface' in filepath:
        return 'interface' + filepath.split('interface', 1)[1]
    else:
        # If none of the directories are found, return the original filepath
        return filepath