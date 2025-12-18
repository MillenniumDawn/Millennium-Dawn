#!/usr/bin/env python3
# Script to fix indentation and spacing issues in MD files
# Fixes:
# - 4-space indentation to tabs
# - Missing spaces around equal signs
# - Double spaces around equal signs
# - Missing spaces around braces { }
# - Double spaces around braces
# Reports (but doesn't fix):
# - Missing quotation marks

import os
import re
import fnmatch

def fix_file_formatting(filepath):
	"""Fix indentation and spacing issues in a single file"""
	try:
		with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
			lines = file.readlines()

		modified = False
		fixed_lines = []
		issues_found = []

		for line_num, line in enumerate(lines, 1):
			original_line = line

			# Skip lines that start with comments
			if line.strip().startswith('#'):
				fixed_lines.append(line)
				continue

			# Fix 4-space indentation to tabs
			# Only replace 4 spaces at the beginning of lines
			if line.startswith('    '):
				# Count how many groups of 4 spaces we have at the start
				indent_count = 0
				temp_line = line
				while temp_line.startswith('    '):
					indent_count += 1
					temp_line = temp_line[4:]

				# Replace with tabs
				line = '\t' * indent_count + temp_line
				if line != original_line:
					modified = True
					issues_found.append(f"Line {line_num}: Fixed 4-space indentation to tabs")

			# Process the line for various fixes, but avoid comments
			comment_pos = line.find('#')
			if comment_pos == -1:
				# No comment, process the whole line
				fixed_line = fix_spacing_issues(line)
			else:
				# Process only the part before the comment
				before_comment = line[:comment_pos]
				after_comment = line[comment_pos:]
				fixed_line = fix_spacing_issues(before_comment) + after_comment

			if fixed_line != line:
				modified = True
				issues_found.append(f"Line {line_num}: Fixed spacing issues")

			fixed_lines.append(fixed_line)

		# Write back the file if it was modified
		if modified:
			with open(filepath, 'w', encoding='utf-8') as file:
				file.writelines(fixed_lines)
			print(f"Fixed: {filepath}")
			for issue in issues_found:
				print(f"  {issue}")
			return True

		return False

	except Exception as e:
		print(f"Error processing {filepath}: {e}")
		return False

def fix_spacing_issues(line):
	"""Fix spacing around equal signs and braces"""
	# Don't process if inside quotes (odd number of quotes means unclosed quote)
	if '"' in line and line.count('"') % 2 == 1:
		return line

	original_line = line

	# Fix spacing around equal signs
	# Remove double spaces around equals
	line = re.sub(r'  =', ' =', line)
	line = re.sub(r'=  ', '= ', line)

	# Add missing spaces around equals
	# Match = that doesn't have spaces on both sides
	line = re.sub(r'([^\s])=([^\s])', r'\1 = \2', line)
	line = re.sub(r'([^\s])=(\s)', r'\1 =\2', line)
	line = re.sub(r'(\s)=([^\s])', r'\1= \2', line)

	# Handle special case for = at end of line
	line = re.sub(r'([^\s])=\n', r'\1 =\n', line)

	# Fix spacing around opening braces {
	# Add space before { if missing
	line = re.sub(r'([^\s]){', r'\1 {', line)
	# Add space after { if missing (but not at end of line)
	line = re.sub(r'{([^\s\n])', r'{ \1', line)
	# Remove double spaces around {
	line = re.sub(r'  {', ' {', line)
	line = re.sub(r'{  ', '{ ', line)

	# Fix spacing around closing braces }
	# Add space before } if missing
	line = re.sub(r'([^\s])}', r'\1 }', line)
	# Add space after } if missing (but not at end of line)
	line = re.sub(r'}([^\s\n])', r'} \1', line)
	# Remove double spaces around }
	line = re.sub(r'  }', ' }', line)
	line = re.sub(r'}  ', '} ', line)

	# Handle special cases for braces at end of line
	line = re.sub(r'([^\s]){\n', r'\1 {\n', line)
	line = re.sub(r'([^\s])}\n', r'\1 }\n', line)

	return line

def check_for_unfixable_issues(filepath):
	"""Check for issues that can't be automatically fixed"""
	issues = []
	try:
		with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
			lines = file.readlines()

		for line_num, line in enumerate(lines, 1):
			# Skip comment lines
			if line.strip().startswith('#'):
				continue

			# Check for odd number of quotes (potential missing quote)
			if '"' in line and line.count('"') % 2 == 1:
				# Make sure it's not in a comment
				comment_pos = line.find('#')
				if comment_pos == -1 or line[:comment_pos].count('"') % 2 == 1:
					issues.append(f"Line {line_num}: Possible missing quotation mark")

	except Exception as e:
		issues.append(f"Error reading file: {e}")

	return issues

def main():
	print("Fixing indentation and spacing issues...")

	# Get script directory and root directory
	script_dir = os.path.dirname(os.path.abspath(__file__))
	root_dir = os.path.dirname(script_dir)

	files_to_process = []
	folders_to_check = ['common', 'events', 'history', 'interface']

	# Collect all .txt files
	for folder in folders_to_check:
		folder_path = os.path.join(root_dir, folder)
		if os.path.exists(folder_path):
			print(f"Scanning {folder}...")
			for root, dirnames, filenames in os.walk(folder_path):
				for filename in fnmatch.filter(filenames, '*.txt'):
					files_to_process.append(os.path.join(root, filename))

	print(f"Processing {len(files_to_process)} files...")

	fixed_count = 0
	unfixable_issues = []

	for filepath in files_to_process:
		if fix_file_formatting(filepath):
			fixed_count += 1

		# Check for issues that can't be automatically fixed
		issues = check_for_unfixable_issues(filepath)
		if issues:
			unfixable_issues.extend([(filepath, issue) for issue in issues])

	print(f"\nFixed {fixed_count} files out of {len(files_to_process)} processed.")

	if unfixable_issues:
		print(f"\nFound {len(unfixable_issues)} issues that need manual attention:")
		for filepath, issue in unfixable_issues:
			print(f"  {filepath}: {issue}")

	print("Done!")

if __name__ == "__main__":
	main()