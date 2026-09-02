#!/usr/bin/env python3
"""Convert delivered art into the DDS and TGA forms MD ships.

    md_art_convert.py event <src.png>... --out-dir <dir>
    md_art_convert.py portrait <src.png>... --out-dir <dir>
    md_art_convert.py flag <src.png> --name <FLAG_NAME> [--flags-dir gfx/flags]
    md_art_convert.py normalise <dir>... [--check]

event/portrait/flag need ImageMagick on PATH. normalise is pure stdlib and
rewrites nothing but the row order and the origin bit.
"""

import argparse
import shutil
import struct
import subprocess
import sys
from pathlib import Path

COUNTRY_EVENT_SIZE = (217, 163)
NEWS_EVENT_SIZE = (397, 153)
PORTRAIT_SIZE = (156, 210)
FLAG_SIZES = {"": (82, 52), "medium": (41, 26), "small": (10, 7)}

TGA_HEADER = struct.Struct("<BBBHHBHHHHBB")
TGA_TOP_LEFT = 0x20
UNCOMPRESSED_TGA_TYPES = frozenset({1, 2, 3})


def _is_imagemagick(path: str) -> bool:
    """Windows ships its own convert.exe (FAT to NTFS), so ask the binary."""
    try:
        result = subprocess.run(
            [path, "-version"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return "imagemagick" in (result.stdout + result.stderr).lower()


def _which_imagemagick(*names: str) -> str:
    for exe in names:
        found = shutil.which(exe)
        if found and _is_imagemagick(found):
            return found
    sys.exit("ImageMagick not found on PATH (need one of: " + ", ".join(names) + ").")


def imagemagick() -> list[str]:
    return [_which_imagemagick("magick", "convert")]


def image_size(path: Path) -> tuple[int, int]:
    identify = _which_imagemagick("identify", "magick")
    argv = [identify]
    if Path(identify).stem.lower() == "magick":
        argv.append("identify")
    out = subprocess.run(
        argv + ["-format", "%w %h", str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return int(out[0]), int(out[1])


def write_dds(src: Path, dest: Path, size: tuple[int, int], resize: bool) -> None:
    """Uncompressed A8R8G8B8, matching the legacy DDS the game already loads."""
    argv = imagemagick() + [str(src)]
    if resize:
        argv += ["-filter", "Lanczos", "-resize", "%dx%d!" % size]
    # Without -alpha set an alpha-less source writes a 24-bit DDS, which the
    # engine does not read.
    argv += [
        "-alpha",
        "set",
        "-define",
        "dds:compression=none",
        "-define",
        "dds:mipmaps=0",
        str(dest),
    ]
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(argv, check=True)


def write_tga(src: Path, dest: Path, size: tuple[int, int], resize: bool) -> None:
    """Uncompressed TGA with a bottom-left origin, as the rest of gfx/flags uses."""
    argv = imagemagick() + [str(src)]
    if resize:
        argv += ["-filter", "Lanczos", "-resize", "%dx%d!" % size]
    # ImageMagick defaults to a top-left origin descriptor; -flip pairs with
    # -orient so the rows and the header agree.
    argv += ["-flip", "-alpha", "set", "-orient", "bottom-left", "-compress", "None"]
    argv.append(str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(argv, check=True)


def pixels_match(a: Path, b: Path) -> bool:
    argv = imagemagick()
    if Path(argv[0]).stem.lower() == "magick":
        argv.append("compare")
    else:
        argv = [shutil.which("compare") or "compare"]
    result = subprocess.run(
        argv + ["-metric", "AE", str(a), str(b), "null:"],
        capture_output=True,
        text=True,
    )
    return result.stderr.strip().split()[0] in ("0", "0.0")


def tga_normalised(data: bytes) -> bytes | None:
    """Return `data` rewritten bottom-left, or None if it needs no change.

    Row order is reversed and the origin bit cleared; pixel bytes are moved,
    never re-encoded, so the decoded image is identical.
    """
    if len(data) < TGA_HEADER.size:
        return None
    (
        idlength,
        _cmap_type,
        datatype,
        _cmap_origin,
        cmap_length,
        cmap_depth,
        _x,
        _y,
        width,
        height,
        bpp,
        descriptor,
    ) = TGA_HEADER.unpack_from(data, 0)

    if not descriptor & TGA_TOP_LEFT:
        return None
    if datatype not in UNCOMPRESSED_TGA_TYPES:
        return None

    start = TGA_HEADER.size + idlength + cmap_length * (cmap_depth // 8)
    stride = width * (bpp // 8)
    end = start + stride * height
    if stride == 0 or end > len(data):
        return None

    rows = [data[start + i * stride : start + (i + 1) * stride] for i in range(height)]
    header = bytearray(data[:start])
    header[17] = descriptor & ~TGA_TOP_LEFT
    return bytes(header) + b"".join(reversed(rows)) + data[end:]


def normalise_dir(root: Path, check_only: bool) -> tuple[int, int]:
    changed = skipped = 0
    for path in sorted(root.rglob("*.tga")):
        data = path.read_bytes()
        rewritten = tga_normalised(data)
        if rewritten is None:
            if data[17:18] and data[17] & TGA_TOP_LEFT:
                print(f"  SKIP  compressed or malformed, needs a manual pass: {path}")
                skipped += 1
            continue
        print(f"  {'WOULD FIX' if check_only else 'FIX'}  {path}")
        if not check_only:
            path.write_bytes(rewritten)
        changed += 1
    return changed, skipped


def convert_fixed_size(
    sources: list[Path],
    out_dir: Path,
    allowed: list[tuple[int, int]],
    resize: bool,
    verify: bool,
) -> int:
    failures = 0
    for src in sources:
        size = image_size(src)
        if size not in allowed and not resize:
            expected = " or ".join("%dx%d" % s for s in allowed)
            print(f"  SKIP  {src.name} is {size[0]}x{size[1]}, expected {expected}")
            failures += 1
            continue
        target = size if size in allowed else allowed[0]
        dest = out_dir / (src.stem + ".dds")
        write_dds(src, dest, target, resize=size != target)
        if verify and size == target and not pixels_match(src, dest):
            print(f"  FAIL  {dest.name} does not match its source")
            failures += 1
            continue
        print(f"  OK    {dest}  {target[0]}x{target[1]}")
    return failures


def convert_flag(src: Path, name: str, flags_dir: Path, verify: bool) -> int:
    failures = 0
    base = FLAG_SIZES[""]
    size = image_size(src)
    if size != base:
        print(f"  NOTE  {src.name} is {size[0]}x{size[1]}, resizing to 82x52")
    for subdir, target in FLAG_SIZES.items():
        dest = flags_dir / subdir / f"{name}.tga"
        write_tga(src, dest, target, resize=size != target)
        if verify and size == target and not pixels_match(src, dest):
            print(f"  FAIL  {dest} does not match its source")
            failures += 1
            continue
        print(f"  OK    {dest}  {target[0]}x{target[1]}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("event", "convert event pictures to uncompressed DDS"),
        ("portrait", "convert leader portraits to uncompressed DDS"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("sources", nargs="+", type=Path)
        p.add_argument("--out-dir", required=True, type=Path)
        p.add_argument("--resize", action="store_true")
        p.add_argument("--no-verify", action="store_true")

    p = sub.add_parser("flag", help="convert a flag to TGA at all three sizes")
    p.add_argument("source", type=Path)
    p.add_argument("--name", required=True)
    p.add_argument("--flags-dir", type=Path, default=Path("gfx/flags"))
    p.add_argument("--no-verify", action="store_true")

    p = sub.add_parser("normalise", help="rewrite top-left-origin TGAs in place")
    p.add_argument("roots", nargs="+", type=Path)
    p.add_argument("--check", action="store_true")

    args = parser.parse_args()

    if args.command == "normalise":
        total_changed = total_skipped = 0
        for root in args.roots:
            changed, skipped = normalise_dir(root, args.check)
            total_changed += changed
            total_skipped += skipped
        verb = "would fix" if args.check else "fixed"
        print(f"\n{verb}: {total_changed}  needing a manual pass: {total_skipped}")
        return 1 if args.check and total_changed else 0

    if args.command == "flag":
        failures = convert_flag(
            args.source, args.name, args.flags_dir, not args.no_verify
        )
    else:
        allowed = (
            [COUNTRY_EVENT_SIZE, NEWS_EVENT_SIZE]
            if args.command == "event"
            else [PORTRAIT_SIZE]
        )
        failures = convert_fixed_size(
            args.sources, args.out_dir, allowed, args.resize, not args.no_verify
        )

    if failures:
        print(f"\n{failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
