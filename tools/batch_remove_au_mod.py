import os
import re

base = "/mnt/Linux/github-projects/Millennium-Dawn"
target = "African_Union_Relations"

count = 0
for root, dirs, files in os.walk(os.path.join(base, "history", "countries")):
    for f in sorted(files):
        if not f.endswith(".txt"):
            continue
        path = os.path.join(root, f)
        with open(path, "r") as fh:
            content = fh.read()
        new_content = re.sub(
            r"\tadd_opinion_modifier = \{ target = \w+ modifier = African_Union_Relations \}\n",
            "",
            content,
        )
        if new_content != content:
            with open(path, "w") as fh:
                fh.write(new_content)
            print(f"Updated: {path}")
            count += 1

print(f"\nTotal files updated: {count}")
