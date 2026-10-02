#!/usr/bin/env python3
"""Extract a .docx dev diary into ordered text blocks + images.

Dependency-free (stdlib only). A .docx is a zip:
  word/document.xml          body, paragraph styles, inline image refs
  word/_rels/document.xml.rels   rId -> media path
  word/media/*               the image bytes

Walks <w:body> in document order and prints a JSON document to stdout:
  {
    "title":  <docx core title | first heading text | null>,
    "blocks": [ {type:"heading", level:2|3, text}, {type:"para", text},
                {type:"image", index:N}, ... ],
    "images": ["picture-1.png", "picture-2.png", ...]
  }

Referenced media are copied, in first-appearance order, to
  <image-dir>/<prefix>-<N>.<ext>   (extension preserved; nothing is converted)

Text is emitted VERBATIM. No whitespace, quote, ellipsis, or dash normalization
happens here -- that is the model's job per the skill's voice rules.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CP = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
DC = "{http://purl.org/dc/elements/1.1/}"

HEADING_RE = re.compile(r"heading\s*([1-9])", re.IGNORECASE)


def warn(msg):
    print(f"extract_docx: {msg}", file=sys.stderr)


def load_rels(zf):
    """rId -> media zip path (e.g. 'word/media/image1.png')."""
    rels = {}
    try:
        root = ET.fromstring(zf.read("word/_rels/document.xml.rels"))
    except KeyError:
        return rels
    for rel in root.findall(f"{PKG_REL}Relationship"):
        rid = rel.get("Id")
        target = rel.get("Target", "")
        if "media/" in target:
            # Targets are relative to word/ ; normalize ../ and leading slashes.
            norm = target.lstrip("/")
            if norm.startswith("word/"):
                rels[rid] = norm
            else:
                rels[rid] = "word/" + norm.replace("../", "")
    return rels


def doc_title(zf):
    try:
        root = ET.fromstring(zf.read("docProps/core.xml"))
    except (KeyError, ET.ParseError):
        return None
    node = root.find(f"{DC}title")
    if node is not None and node.text and node.text.strip():
        return node.text.strip()
    return None


def run_text(run):
    """Concatenate <w:t> (and tab/break) for one run, verbatim."""
    parts = []
    for child in run.iter():
        tag = child.tag
        if tag == f"{W}t":
            parts.append(child.text or "")
        elif tag == f"{W}tab":
            parts.append("\t")
        elif tag in (f"{W}br", f"{W}cr"):
            parts.append("\n")
    return "".join(parts)


def run_is_bold(run):
    rpr = run.find(f"{W}rPr")
    if rpr is None:
        return False
    b = rpr.find(f"{W}b")
    return b is not None and b.get(f"{W}val", "true") not in ("false", "0")


def run_is_italic(run):
    rpr = run.find(f"{W}rPr")
    if rpr is None:
        return False
    i = rpr.find(f"{W}i")
    return i is not None and i.get(f"{W}val", "true") not in ("false", "0")


def run_image_rids(run):
    """rIds of images embedded in this run, in order."""
    rids = []
    for blip in run.iter(f"{A}blip"):
        rid = blip.get(f"{R}embed") or blip.get(f"{R}link")
        if rid:
            rids.append(rid)
    return rids


def paragraph_style_level(para):
    ppr = para.find(f"{W}pPr")
    if ppr is None:
        return None
    pstyle = ppr.find(f"{W}pStyle")
    if pstyle is None:
        return None
    val = pstyle.get(f"{W}val", "")
    m = HEADING_RE.search(val)
    if not m:
        return None
    n = int(m.group(1))
    # Heading1 -> ## (level 2); Heading2/3+ -> ### (level 3). Diaries use ## / ###.
    return 2 if n == 1 else 3


def emit_run_text(run):
    text = run_text(run)
    if not text:
        return ""
    # Apply emphasis only when it wraps real (non-space) content.
    stripped = text.strip()
    if not stripped:
        return text
    lead = text[: len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    if run_is_bold(run):
        stripped = f"**{stripped}**"
    elif run_is_italic(run):
        stripped = f"_{stripped}_"
    return f"{lead}{stripped}{trail}"


def main():
    ap = argparse.ArgumentParser(description="Extract a .docx dev diary.")
    ap.add_argument("--docx", required=True, help="Path to the .docx file")
    ap.add_argument("--image-dir", required=True, help="Destination folder for images")
    ap.add_argument("--image-prefix", default="picture", help="Image filename prefix")
    args = ap.parse_args()

    if not os.path.isfile(args.docx):
        warn(f"file not found: {args.docx}")
        return 2
    if not zipfile.is_zipfile(args.docx):
        warn(f"not a valid .docx (not a zip): {args.docx}")
        return 2

    with zipfile.ZipFile(args.docx) as zf:
        names = set(zf.namelist())
        if "word/document.xml" not in names:
            warn("missing word/document.xml -- not a Word .docx")
            return 2
        rels = load_rels(zf)
        title = doc_title(zf)
        try:
            body = ET.fromstring(zf.read("word/document.xml")).find(f"{W}body")
        except ET.ParseError as exc:
            warn(f"could not parse document.xml: {exc}")
            return 2
        if body is None:
            warn("no <w:body> found")
            return 2

        blocks = []
        # rId -> sequential image number (1-based, first-appearance order)
        rid_to_index = {}
        # sequential number -> media zip path
        index_to_media = {}

        def register_image(rid):
            if rid in rid_to_index:
                return rid_to_index[rid]
            media = rels.get(rid)
            if not media or media not in names:
                warn(f"image rId {rid} has no media file; skipped")
                return None
            idx = len(rid_to_index) + 1
            rid_to_index[rid] = idx
            index_to_media[idx] = media
            return idx

        for para in body.findall(f"{W}p"):
            level = paragraph_style_level(para)
            text_parts = []
            para_images = []
            for run in para.findall(f"{W}r"):
                for rid in run_image_rids(run):
                    idx = register_image(rid)
                    if idx is not None:
                        para_images.append(idx)
                text_parts.append(emit_run_text(run))
            text = "".join(text_parts).strip()

            if text:
                if level:
                    blocks.append({"type": "heading", "level": level, "text": text})
                else:
                    blocks.append({"type": "para", "text": text})
            for idx in para_images:
                blocks.append({"type": "image", "index": idx})

        if title is None:
            for b in blocks:
                if b["type"] == "heading":
                    title = b["text"]
                    break

        # Copy media in first-appearance order to <image-dir>/<prefix>-<N>.<ext>.
        os.makedirs(args.image_dir, exist_ok=True)
        image_names = []
        with tempfile.TemporaryDirectory() as tmp:
            for idx in sorted(index_to_media):
                media = index_to_media[idx]
                ext = os.path.splitext(media)[1].lower() or ".png"
                if ext in (".emf", ".wmf"):
                    warn(f"image {idx} is {ext} (vector); copied but may not render")
                out_name = f"{args.image_prefix}-{idx}{ext}"
                extracted = zf.extract(media, tmp)
                shutil.copyfile(extracted, os.path.join(args.image_dir, out_name))
                image_names.append(out_name)

    print(json.dumps({"title": title, "blocks": blocks, "images": image_names}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
