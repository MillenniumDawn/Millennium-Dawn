#!/usr/bin/env python3
import re
from pathlib import Path

dirpath = Path("docs/national-content")
for path in sorted(dirpath.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n.*?\n---\s*\n)", text, re.S)
    front = m.group(1) if m else ""
    body = text[m.end() :] if m else text
    # determine country name from frontmatter title
    country = path.stem.replace("-", " ")
    if front:
        tmatch = re.search(r'title:\s*"([^"]+)"', front)
        if tmatch:
            tval = tmatch.group(1)
            if tval.startswith("National Content - "):
                country = tval.split("National Content - ", 1)[1]
    # build standardized header
    flag_name = country.lower().replace(" ", "_")
    header_lines = []
    header_lines.append(f"## {country} WIP")
    header_lines.append("")
    header_lines.append(
        f"![Flag_of_{country.replace(' ', '_')}]({{ '/uploads/flags/{flag_name}.png' | relative_url }}){{: .country-flag}}"
    )
    header_lines.append("")
    header = "\n".join(header_lines)
    # strip existing intro: drop initial heading and image
    lines = body.splitlines()
    i = 0
    # skip leading blanks
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    # skip existing ## ... WIP heading if present
    if i < len(lines) and re.match(r"##\s+", lines[i]):
        i += 1
        # skip a blank after
        if i < len(lines) and lines[i].strip() == "":
            i += 1
    # skip image line
    if (
        i < len(lines)
        and lines[i].strip().startswith("![")
        and ".country-flag" in lines[i]
    ):
        i += 1
        if i < len(lines) and lines[i].strip() == "":
            i += 1
    newbody = header + "\n".join(lines[i:]).lstrip("\n")
    newtext = front + newbody
    if newtext != text:
        path.write_text(newtext, encoding="utf-8")
        print("normalized", path.name)
print("normalization complete")
