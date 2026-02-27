#!/usr/bin/env python3
"""
Convert DDS files from DX10/sRGB format to legacy ARGB8888 format.

Converts: B8G8R8A8_UNORM_SRGB (DX10 header, DXGI format 91)
      To: ARGB8888 legacy DDS (no DX10 header, raw 32-bit ARGB)

Usage:
    python convert_dds_to_legacy.py <input.dds> [output.dds]
    python convert_dds_to_legacy.py <directory>        # converts all .dds in-place
    python convert_dds_to_legacy.py <directory> <out>  # converts to separate output dir
"""

import os
import struct
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DDS_MAGIC = 0x20534444  # "DDS "
DX10_FOURCC = 0x30315844  # "DX10"

DXGI_B8G8R8A8_SRGB = 91  # B8G8R8A8_UNORM_SRGB
DXGI_B8G8R8A8_UNORM = 87  # B8G8R8A8_UNORM  (also convertible)

# Legacy pixel-format block that matches AS1.dds exactly
#   PF Flags : 0x41  (DDPF_ALPHAPIXELS | DDPF_RGB)
#   FourCC   : 0x00000000
#   BitCount : 32
#   R mask   : 0x00FF0000
#   G mask   : 0x0000FF00
#   B mask   : 0x000000FF
#   A mask   : 0xFF000000
LEGACY_PIXELFORMAT = struct.pack(
    "<8I",
    32,  # dwSize
    0x41,  # dwFlags  (DDPF_ALPHAPIXELS | DDPF_RGB)
    0x00000000,  # dwFourCC (none)
    32,  # dwRGBBitCount
    0x00FF0000,  # dwRBitMask
    0x0000FF00,  # dwGBitMask
    0x000000FF,  # dwBBitMask
    0xFF000000,  # dwABitMask
)


# --------------------------------------------------------------------------- #
# sRGB → linear lookup table (applied to R, G, B; alpha is left unchanged)
# --------------------------------------------------------------------------- #
def _srgb_to_linear(v: int) -> int:
    n = v / 255.0
    linear = n / 12.92 if n <= 0.04045 else ((n + 0.055) / 1.055) ** 2.4
    return int(linear * 255.0 + 0.5)


SRGB_TO_LINEAR = bytes(_srgb_to_linear(i) for i in range(256))


# --------------------------------------------------------------------------- #
# Core conversion
# --------------------------------------------------------------------------- #
def convert_dds_to_legacy(input_path: str, output_path: str | None = None) -> bool:
    """
    Convert a single DDS file from DX10/sRGB to legacy ARGB8888.

    Returns True on success, False if the file was skipped or failed.
    """
    if output_path is None:
        output_path = input_path

    with open(input_path, "rb") as f:
        raw = bytearray(f.read())

    # ---- validate magic --------------------------------------------------- #
    if struct.unpack_from("<I", raw, 0)[0] != DDS_MAGIC:
        print(f"  SKIP  Not a DDS file: {input_path}")
        return False

    if struct.unpack_from("<I", raw, 4)[0] != 124:
        print(f"  SKIP  Unexpected header size in: {input_path}")
        return False

    # ---- check pixel-format block ----------------------------------------- #
    pf_flags = struct.unpack_from("<I", raw, 80)[0]
    pf_fourcc = struct.unpack_from("<I", raw, 84)[0]

    # --- already legacy? --------------------------------------------------- #
    if pf_fourcc != DX10_FOURCC:
        print(f"  SKIP  Already legacy (no DX10 header): {input_path}")
        return False

    # ---- read DX10 extension (starts at byte 128) ------------------------- #
    dxgi_format = struct.unpack_from("<I", raw, 128)[0]

    if dxgi_format not in (DXGI_B8G8R8A8_SRGB, DXGI_B8G8R8A8_UNORM):
        print(f"  SKIP  Unsupported DXGI format {dxgi_format}: {input_path}")
        return False

    apply_srgb_conversion = dxgi_format == DXGI_B8G8R8A8_SRGB

    width = struct.unpack_from("<I", raw, 16)[0]
    height = struct.unpack_from("<I", raw, 12)[0]
    label = "B8G8R8A8_UNORM_SRGB" if apply_srgb_conversion else "B8G8R8A8_UNORM"
    print(
        f"  CONVERT  {os.path.basename(input_path)}  [{label} → ARGB8888 legacy]  {width}×{height}"
    )

    # ================================================================== #
    # Build the new file
    #
    # Old layout:  [magic 4] [header 124] [DX10-ext 20] [pixels ...]
    # New layout:  [magic 4] [header 124]               [pixels ...]
    #
    # The DX10 extension (20 bytes) is removed, and the pixel-format
    # block inside the 124-byte header is replaced with the legacy block.
    # ================================================================== #
    pixel_data = raw[148:]  # everything after the 20-byte DX10 extension

    # Optionally linearise pixels (BGRA order, alpha unchanged)
    if apply_srgb_conversion:
        pixel_data = bytearray(pixel_data)
        for i in range(0, width * height * 4, 4):
            pixel_data[i] = SRGB_TO_LINEAR[pixel_data[i]]  # B
            pixel_data[i + 1] = SRGB_TO_LINEAR[pixel_data[i + 1]]  # G
            pixel_data[i + 2] = SRGB_TO_LINEAR[pixel_data[i + 2]]  # R
            # pixel_data[i+3] unchanged                         # A

    # Copy the original 128-byte block (magic + header) and patch it
    new_header = bytearray(raw[:128])

    # Replace pixel-format block (bytes 76–107 inside the file, i.e. 76–107)
    new_header[76:108] = LEGACY_PIXELFORMAT

    # Clear the DX10 FourCC that we just overwrote (sanity — already done above)
    # Caps / reserved bytes stay the same

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(new_header)
        f.write(pixel_data)

    print(f"  ✓  Saved: {output_path}")
    return True


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = sys.argv[1]

    if os.path.isdir(src):
        out_dir = sys.argv[2] if len(sys.argv) > 2 else None
        files = sorted(Path(src).rglob("*.dds"))
        if not files:
            print(f"No .dds files found in {src}")
            sys.exit(0)

        print(f"Processing {len(files)} file(s) in: {src}\n")
        converted = skipped = 0
        for f in files:
            dest = str(Path(out_dir) / f.relative_to(src)) if out_dir else str(f)
            if convert_dds_to_legacy(str(f), dest):
                converted += 1
            else:
                skipped += 1
        print(f"\nDone — converted: {converted}  skipped: {skipped}")

    else:
        dest = sys.argv[2] if len(sys.argv) > 2 else None
        ok = convert_dds_to_legacy(src, dest)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
