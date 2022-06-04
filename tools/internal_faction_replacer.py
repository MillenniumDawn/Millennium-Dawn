# Written by Birdy
# Usage: python internal_faction_line_replacer.py "PATH_TO_HISTORY/COUNTRIES"

from pathlib import Path
import re
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("path", type=Path)
args = parser.parse_args()

pathlist = args.path.glob("*.txt")

for path in pathlist:
	with open(path, "r", encoding='utf_8_sig') as f:
		data = f.read()
	with open(path, "w", encoding='utf_8_sig') as f:
		f.write(
			re.sub(
				"decrease_saudi_royal_family_opinion = yes",
				"set_temp_variable = { temp_opinion = -5 }\n\t\t\tchange_saudi_royal_family_opinion = yes",
				data
			)
		)