#!/user/bin/python
import os
import shutil
from tokenize import Ignore


# Check if a icon is used more than once

with open('../common/national_focus/turkey.txt') as f:
	seen = set()
	for line in f:
		line_lower = line.lower()
		if line_lower in seen:
			if "icon" in line_lower:
				print(line)
		else:
			seen.add(line_lower)