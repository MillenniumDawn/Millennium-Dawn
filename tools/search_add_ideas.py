#!/usr/bin/env python3
"""
Script to search for 'add_ideas = <tag>' and 'add_timed_idea = { idea = <tag> }' patterns in files.
Supports searching single files, multiple files, or entire directories recursively.
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Set


def find_idea_patterns(content: str, filename: str = "") -> List[Tuple[str, int, str, str]]:
    results = []
    lines = content.split('\n')

    simple_pattern = r'^\s*add_ideas\s*=\s*(?:{?\s*)?([A-Za-z0-9_]+)(?:\s*}?)?\s*$'
    timed_pattern = r'^\s*add_timed_idea\s*=\s*{'
    idea_in_timed_pattern = r'^\s*idea\s*=\s*([A-Za-z0-9_]+)\s*$'

    in_timed_block = False
    timed_block_start_line = 0

    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()

        simple_match = re.match(simple_pattern, line)
        if simple_match:
            idea_tag = simple_match.group(1)
            results.append((idea_tag, line_num, line_stripped, "add_ideas"))
            continue

        timed_start_match = re.match(timed_pattern, line)
        if timed_start_match:
            in_timed_block = True
            timed_block_start_line = line_num
            continue

        if in_timed_block:
            idea_match = re.match(idea_in_timed_pattern, line)
            if idea_match:
                idea_tag = idea_match.group(1)
                results.append((idea_tag, line_num, line_stripped, "add_timed_idea"))

            if line_stripped == "}" or line_stripped.endswith("}"):
                in_timed_block = False

    return results


def search_file(filepath: str) -> List[Tuple[str, int, str, str]]:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return find_idea_patterns(content, os.path.basename(filepath))
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return []


def search_directory(directory: str, file_extensions: List[str] = None) -> dict:
    results = {}

    if file_extensions is None:
        file_extensions = ['.txt', '.yml', '.yaml']

    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                filepath = os.path.join(root, file)
                file_results = search_file(filepath)
                if file_results:
                    results[filepath] = file_results

    return results


def filter_excluded_tags(matches: List[Tuple[str, int, str, str]], exclude_prefixes: List[str]) -> List[Tuple[str, int, str, str]]:
    if not exclude_prefixes:
        return matches

    filtered_matches = []
    for idea_tag, line_num, full_line, pattern_type in matches:
        should_exclude = False
        for prefix in exclude_prefixes:
            if idea_tag.startswith(prefix):
                should_exclude = True
                break

        if not should_exclude:
            filtered_matches.append((idea_tag, line_num, full_line, pattern_type))

    return filtered_matches


def print_results(results: dict, show_line_numbers: bool = True, show_full_line: bool = True):
    if not results:
        print("No idea patterns found.")
        return

    total_matches = sum(len(matches) for matches in results.values())
    print(f"Found {total_matches} idea patterns in {len(results)} files:\n")

    for filepath, matches in results.items():
        print(f"File: {filepath}")
        print("-" * (len(filepath) + 6))

        for idea_tag, line_num, full_line, pattern_type in matches:
            output = f"  {idea_tag} ({pattern_type})"
            if show_line_numbers:
                output += f" (line {line_num})"
            if show_full_line:
                output += f": {full_line}"
            print(output)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Search for 'add_ideas = <tag>' and 'add_timed_idea = { idea = <tag> }' patterns in files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search_add_ideas.py file.txt
  python search_add_ideas.py -d common/
  python search_add_ideas.py -d common/ -e .txt .yml
  python search_add_ideas.py file1.txt file2.txt
  python search_add_ideas.py -d common/ --exclude COM IND
  python search_add_ideas.py file.txt --exclude BRA USA
        """
    )

    parser.add_argument('paths', nargs='+', help='Files or directories to search')
    parser.add_argument('-d', '--directory', action='store_true',
                       help='Treat paths as directories to search recursively')
    parser.add_argument('-e', '--extensions', nargs='+', default=['.txt', '.yml', '.yaml'],
                       help='File extensions to include when searching directories')
    parser.add_argument('--no-line-numbers', action='store_true',
                       help='Hide line numbers in output')
    parser.add_argument('--no-full-line', action='store_true',
                       help='Hide full line content in output')
    parser.add_argument('--unique-tags', action='store_true',
                       help='Show only unique idea tags found')
    parser.add_argument('--exclude', nargs='+', default=[],
                       help='Exclude idea tags that start with these prefixes (e.g., COM IND)')
    parser.add_argument('--pattern-type', choices=['all', 'add_ideas', 'add_timed_idea'],
                       default='all', help='Filter by pattern type')

    args = parser.parse_args()

    all_results = {}

    if args.directory:
        for path in args.paths:
            if os.path.isdir(path):
                dir_results = search_directory(path, args.extensions)
                all_results.update(dir_results)
            else:
                print(f"Warning: {path} is not a directory, skipping...")
    else:
        for path in args.paths:
            if os.path.isfile(path):
                file_results = search_file(path)
                if file_results:
                    all_results[path] = file_results
            else:
                print(f"Warning: {path} is not a file, skipping...")

    if args.pattern_type != 'all':
        filtered_results = {}
        for filepath, matches in all_results.items():
            filtered_matches = [match for match in matches if match[3] == args.pattern_type]
            if filtered_matches:
                filtered_results[filepath] = filtered_matches
        all_results = filtered_results

    if args.exclude:
        filtered_results = {}
        for filepath, matches in all_results.items():
            filtered_matches = filter_excluded_tags(matches, args.exclude)
            if filtered_matches:
                filtered_results[filepath] = filtered_matches
        all_results = filtered_results

    if args.unique_tags:
        unique_tags = set()
        for matches in all_results.values():
            for idea_tag, _, _, _ in matches:
                unique_tags.add(idea_tag)

        print(f"Found {len(unique_tags)} unique idea tags:")
        for tag in sorted(unique_tags):
            print(f"  {tag}")
    else:
        print_results(all_results,
                     show_line_numbers=not args.no_line_numbers,
                     show_full_line=not args.no_full_line)


if __name__ == "__main__":
    main()