#!/usr/bin/env python3
"""
Script to find double-defined textures in .gfx files.
Searches for duplicate texturefile definitions across all .gfx files in the Millennium Dawn mod.
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

def find_gfx_files(root_dir):
    """Find all .gfx files in the directory tree."""
    gfx_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.gfx'):
                gfx_files.append(os.path.join(root, file))
    return gfx_files

def extract_texture_definitions(file_path):
    """Extract texturefile definitions from a .gfx file."""
    texture_definitions = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Pattern to match texturefile = "path/to/file.dds"
        pattern = r'texturefile\s*=\s*"([^"]+)"'
        matches = re.finditer(pattern, content, re.IGNORECASE)

        for match in matches:
            texture_path = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            texture_definitions.append({
                'file': file_path,
                'texture_path': texture_path,
                'line_number': line_number,
                'full_match': match.group(0)
            })

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return texture_definitions

def find_duplicate_textures(root_dir):
    """Find all duplicate texture definitions across .gfx files."""
    print(f"Searching for .gfx files in: {root_dir}")

    # Find all .gfx files
    gfx_files = find_gfx_files(root_dir)
    print(f"Found {len(gfx_files)} .gfx files")

    # Dictionary to store texture paths and their definitions
    texture_registry = defaultdict(list)

    # Process each .gfx file
    for gfx_file in gfx_files:
        # Skip goals_shine.gfx entirely as it contains intentional duplicates
        if 'goals_shine.gfx' in gfx_file:
            print(f"Skipping: {os.path.relpath(gfx_file, root_dir)} (intentional duplicates)")
            continue

        # Skip files under Modding resources directory (development/testing files)
        if 'Modding resources' in gfx_file:
            print(f"Skipping: {os.path.relpath(gfx_file, root_dir)} (modding resources)")
            continue

        print(f"Processing: {os.path.relpath(gfx_file, root_dir)}")
        definitions = extract_texture_definitions(gfx_file)

        for definition in definitions:
            texture_registry[definition['texture_path']].append(definition)

    # Find duplicates
    duplicates = {}
    for texture_path, definitions in texture_registry.items():
        if len(definitions) > 1:
            duplicates[texture_path] = definitions

    return duplicates

def print_results(duplicates, output_file=None):
    """Print the results of duplicate texture search."""
    if not duplicates:
        message = "\nNo duplicate texture definitions found!"
        print(message)
        if output_file:
            output_file.write(message + "\n")
        return

    header = f"\nFound {len(duplicates)} textures with duplicate definitions:"
    separator = "=" * 80

    print(header)
    print(separator)

    if output_file:
        output_file.write(header + "\n")
        output_file.write(separator + "\n")

    for texture_path, definitions in duplicates.items():
        texture_info = f"\nTexture: {texture_path}"
        count_info = f"   Found {len(definitions)} definitions:"

        print(texture_info)
        print(count_info)

        if output_file:
            output_file.write(texture_info + "\n")
            output_file.write(count_info + "\n")

        for i, definition in enumerate(definitions, 1):
            rel_file = os.path.relpath(definition['file'])
            file_info = f"   {i}. File: {rel_file}"
            line_info = f"      Line: {definition['line_number']}"
            def_info = f"      Definition: {definition['full_match']}"

            print(file_info)
            print(line_info)
            print(def_info)

            if output_file:
                output_file.write(file_info + "\n")
                output_file.write(line_info + "\n")
                output_file.write(def_info + "\n")

        separator_line = "-" * 40
        print(separator_line)
        if output_file:
            output_file.write(separator_line + "\n")

def main():
    """Main function."""
    # Get the root directory (current directory by default)
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()

    if not os.path.exists(root_dir):
        print(f"Error: Directory '{root_dir}' does not exist!")
        sys.exit(1)

    print("Millennium Dawn - Duplicate Texture Finder")
    print("=" * 50)

    # Find duplicates
    duplicates = find_duplicate_textures(root_dir)

    # Create output filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"duplicate_textures_report_{timestamp}.txt"

    # Print results to console and file
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        # Write header to file
        output_file.write("Millennium Dawn - Duplicate Texture Finder\n")
        output_file.write("=" * 50 + "\n")
        output_file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_file.write(f"Search directory: {root_dir}\n\n")

        # Print results
        print_results(duplicates, output_file)

        # Summary
        total_duplicates = sum(len(definitions) for definitions in duplicates.values())
        if duplicates:
            summary_lines = [
                f"\nSummary:",
                f"   - {len(duplicates)} unique textures have duplicates",
                f"   - {total_duplicates} total texture definitions",
                f"   - {total_duplicates - len(duplicates)} duplicate definitions found",
                f"   - Note: goals_shine.gfx and Modding resources are excluded (intentional duplicates)"
            ]

            for line in summary_lines:
                print(line)
                output_file.write(line + "\n")

        completion_msg = "\nSearch completed!"
        print(completion_msg)
        output_file.write(completion_msg + "\n")

    print(f"\nResults saved to: {output_filename}")

if __name__ == "__main__":
    main()
