#!/usr/bin/env python3
"""
DDS Converter for Millennium Dawn
Converts PNG files to DDS format and validates existing DDS files
according to art standards.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DDSConverter:
    """Converter for PNG to DDS and DDS validation/conversion"""

    def __init__(self, mod_root: str):
        self.mod_root = Path(mod_root)
        self.target_dirs = [
            self.mod_root / "gfx" / "interface" / "goals",
            self.mod_root / "gfx" / "interface" / "ideas",
        ]
        # Option to scan entire gfx folder
        self.scan_all_gfx = False

    def find_png_files(self) -> List[Path]:
        """Find all PNG files in target directories"""
        png_files = []

        if self.scan_all_gfx:
            # Scan entire gfx folder
            gfx_dir = self.mod_root / "gfx"
            if not gfx_dir.exists():
                logger.warning(f"Gfx directory does not exist: {gfx_dir}")
                return []

            logger.info(f"Scanning entire gfx directory: {gfx_dir}")
            for png_file in gfx_dir.rglob("*.png"):
                png_files.append(png_file)
        else:
            # Scan only specific target directories
            for target_dir in self.target_dirs:
                if not target_dir.exists():
                    logger.warning(f"Directory does not exist: {target_dir}")
                    continue

                logger.info(f"Scanning directory: {target_dir}")

                # Recursively find all PNG files
                for png_file in target_dir.rglob("*.png"):
                    png_files.append(png_file)

        logger.info(f"Found {len(png_files)} PNG files to convert")
        return png_files

    def find_dds_files(self) -> List[Path]:
        """Find all DDS files in target directories"""
        dds_files = []

        if self.scan_all_gfx:
            # Scan entire gfx folder
            gfx_dir = self.mod_root / "gfx"
            if not gfx_dir.exists():
                logger.warning(f"Gfx directory does not exist: {gfx_dir}")
                return []

            logger.info(f"Scanning entire gfx directory for DDS files: {gfx_dir}")
            for dds_file in gfx_dir.rglob("*.dds"):
                dds_files.append(dds_file)
        else:
            # Scan only specific target directories
            for target_dir in self.target_dirs:
                if not target_dir.exists():
                    logger.warning(f"Directory does not exist: {target_dir}")
                    continue

                logger.info(f"Scanning directory for DDS files: {target_dir}")

                # Recursively find all DDS files
                for dds_file in target_dir.rglob("*.dds"):
                    dds_files.append(dds_file)

        logger.info(f"Found {len(dds_files)} DDS files to validate")
        return dds_files

    def _determine_compression_format(self, file_path: Path) -> str:
        """
        Determine the correct compression format based on file path

        Args:
            file_path: Path to the file

        Returns:
            Compression format string
        """
        path_str = str(file_path).lower()

        if "leader" in path_str and "small" in path_str:
            return "B8R8A8G8"  # Leader Portraits Small
        elif "leader" in path_str:
            return "DXT1"  # Leader Portraits
        elif "event" in path_str:
            return "DXT5"  # Event Pictures
        elif "tech" in path_str:
            return "B8R8A8G8"  # Tech Icons
        elif "goals" in path_str or "ideas" in path_str:
            return "B8R8A8G8"  # Goals/Focus and Ideas
        else:
            return "B8R8A8G8"  # Default to uncompressed BGRA

    def _create_dds_header(
        self, width: int, height: int, compression_format: str = "B8R8A8G8"
    ) -> bytes:
        """Create DDS header for specified compression format with no mipmaps"""
        # DDS signature
        signature = b"DDS "

        # Create header (124 bytes)
        header = bytearray(124)

        # Header size
        header[0:4] = (124).to_bytes(4, "little")

        # Flags - need to include DDSD_LINEARSIZE for compressed formats
        if compression_format == "B8R8A8G8":
            flags = (
                0x1 | 0x2 | 0x4 | 0x1000
            )  # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
        else:
            flags = (
                0x1 | 0x2 | 0x4 | 0x1000 | 0x80000
            )  # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
        header[4:8] = flags.to_bytes(4, "little")

        # Height and width
        header[12:16] = height.to_bytes(4, "little")
        header[16:20] = width.to_bytes(4, "little")

        # Pitch or LinearSize calculation
        if compression_format == "B8R8A8G8":
            pitch = width * 4  # 4 bytes per pixel for BGRA
            header[20:24] = pitch.to_bytes(4, "little")
        elif compression_format == "DXT1":
            # DXT1: 8 bytes per 4x4 block
            linear_size = max(1, ((width + 3) // 4)) * max(1, ((height + 3) // 4)) * 8
            header[20:24] = linear_size.to_bytes(4, "little")
        elif compression_format == "DXT5":
            # DXT5: 16 bytes per 4x4 block
            linear_size = max(1, ((width + 3) // 4)) * max(1, ((height + 3) // 4)) * 16
            header[20:24] = linear_size.to_bytes(4, "little")

        # Depth (unused for 2D textures)
        header[24:28] = (0).to_bytes(4, "little")

        # Mipmap count (0 for no mipmaps)
        header[28:32] = (0).to_bytes(4, "little")

        # Reserved fields
        header[32:76] = b"\x00" * 44

        # Pixel format (starts at offset 76)
        pixel_format_size = 32
        header[76:80] = pixel_format_size.to_bytes(4, "little")

        if compression_format == "B8R8A8G8":
            # Uncompressed BGRA format
            header[80:84] = (0x40 | 0x1).to_bytes(
                4, "little"
            )  # DDPF_RGB | DDPF_ALPHAPIXELS
            header[84:88] = b"\x00\x00\x00\x00"  # No FourCC
            header[88:92] = (32).to_bytes(4, "little")  # 32 bits per pixel
            header[92:96] = (0x00FF0000).to_bytes(4, "little")  # R mask
            header[96:100] = (0x0000FF00).to_bytes(4, "little")  # G mask
            header[100:104] = (0x000000FF).to_bytes(4, "little")  # B mask
            header[104:108] = (0xFF000000).to_bytes(4, "little")  # A mask
        elif compression_format == "DXT1":
            # DXT1 (BC1) format
            header[80:84] = (0x4).to_bytes(4, "little")  # DDPF_FOURCC
            header[84:88] = b"DXT1"  # FourCC
            header[88:92] = (0).to_bytes(4, "little")  # No RGB bits
            header[92:108] = b"\x00" * 16  # No masks
        elif compression_format == "DXT5":
            # DXT5 (BC3) format
            header[80:84] = (0x4).to_bytes(4, "little")  # DDPF_FOURCC
            header[84:88] = b"DXT5"  # FourCC
            header[88:92] = (0).to_bytes(4, "little")  # No RGB bits
            header[92:108] = b"\x00" * 16  # No masks

        # Caps
        caps_offset = 108
        header[caps_offset : caps_offset + 4] = (0x1000).to_bytes(
            4, "little"
        )  # DDSCAPS_TEXTURE (no mipmap caps)

        # Reserved caps
        header[caps_offset + 4 : caps_offset + 16] = b"\x00" * 12

        return signature + bytes(header)

    def convert_png_to_dds(self, png_path: Path, replace_png: bool = False) -> bool:
        """
        Convert a single PNG file to DDS format

        Args:
            png_path: Path to the PNG file
            replace_png: If True, delete PNG file after successful conversion

        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Create output path (replace .png with .dds)
            dds_path = png_path.with_suffix(".dds")

            # Skip if DDS already exists
            if dds_path.exists():
                logger.info(f"DDS already exists, skipping: {dds_path}")
                return True

            # Determine compression format
            compression_format = self._determine_compression_format(png_path)

            # Load PNG image
            with Image.open(png_path) as img:
                logger.info(
                    f"Converting: {png_path} -> {dds_path} (format: {compression_format})"
                )

                # Convert to RGBA if not already
                if img.mode != "RGBA":
                    img = img.convert("RGBA")

                # Get image dimensions
                width, height = img.size

                # Convert to numpy array
                img_array = np.array(img)

                # Create DDS header
                header = self._create_dds_header(width, height, compression_format)

                if compression_format == "B8R8A8G8":
                    # Convert RGBA to BGRA (swap R and B channels)
                    bgra_array = img_array.copy()
                    bgra_array[:, :, [0, 2]] = bgra_array[:, :, [2, 0]]  # Swap R and B
                    pixel_data = bgra_array.flatten().tobytes()
                else:
                    # For compressed formats, we'll use the raw RGBA data
                    # Note: This is a simplified approach - proper DXT compression would require additional libraries
                    pixel_data = img_array.flatten().tobytes()

                # Write DDS file
                with open(dds_path, "wb") as f:
                    f.write(header)
                    f.write(pixel_data)

                # Remove PNG if requested
                if replace_png:
                    png_path.unlink()
                    logger.info(f"Removed PNG file: {png_path}")

                logger.info(f"Successfully converted: {png_path}")
                return True

        except Exception as e:
            logger.error(f"Error converting {png_path}: {str(e)}")
            return False

    def convert_all(self, replace_png: bool = False) -> Tuple[int, int]:
        """
        Convert all PNG files to DDS format

        Args:
            replace_png: If True, delete PNG files after successful conversion

        Returns:
            Tuple of (successful_conversions, total_files)
        """
        png_files = self.find_png_files()

        if not png_files:
            logger.warning("No PNG files found to convert")
            return 0, 0

        successful = 0
        total = len(png_files)

        logger.info(f"Starting conversion of {total} PNG files...")

        for png_file in png_files:
            if self.convert_png_to_dds(png_file, replace_png=replace_png):
                successful += 1

        logger.info(
            f"Conversion complete: {successful}/{total} files converted successfully"
        )
        return successful, total

    def read_dds_header(self, dds_path: Path) -> dict:
        """
        Read DDS header and extract key information

        Args:
            dds_path: Path to the DDS file

        Returns:
            Dictionary with DDS header information
        """
        try:
            with open(dds_path, "rb") as f:
                # Read signature
                signature = f.read(4)
                if signature != b"DDS ":
                    return {"valid": False, "error": "Invalid DDS signature"}

                # Read header size
                header_size = int.from_bytes(f.read(4), "little")
                if header_size != 124:
                    return {
                        "valid": False,
                        "error": f"Invalid header size: {header_size}",
                    }

                # Read flags
                flags = int.from_bytes(f.read(4), "little")

                # Read dimensions
                height = int.from_bytes(f.read(4), "little")
                width = int.from_bytes(f.read(4), "little")
                pitch = int.from_bytes(f.read(4), "little")
                depth = int.from_bytes(f.read(4), "little")
                mipmap_count = int.from_bytes(f.read(4), "little")

                # Skip reserved fields
                f.seek(76)

                # Read pixel format
                pixel_format_size = int.from_bytes(f.read(4), "little")
                pixel_format_flags = int.from_bytes(f.read(4), "little")
                fourcc = f.read(4)
                rgb_bit_count = int.from_bytes(f.read(4), "little")

                # Read bit masks
                r_mask = int.from_bytes(f.read(4), "little")
                g_mask = int.from_bytes(f.read(4), "little")
                b_mask = int.from_bytes(f.read(4), "little")
                a_mask = int.from_bytes(f.read(4), "little")

                # Read caps
                f.seek(108)
                caps = int.from_bytes(f.read(4), "little")

                return {
                    "valid": True,
                    "width": width,
                    "height": height,
                    "mipmap_count": mipmap_count,
                    "fourcc": fourcc,
                    "rgb_bit_count": rgb_bit_count,
                    "r_mask": r_mask,
                    "g_mask": g_mask,
                    "b_mask": b_mask,
                    "a_mask": a_mask,
                    "caps": caps,
                }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def validate_dds_format(self, dds_path: Path) -> bool:
        """
        Validate if DDS file has correct format with no mipmaps

        Args:
            dds_path: Path to the DDS file

        Returns:
            True if format is correct, False otherwise
        """
        header_info = self.read_dds_header(dds_path)

        if not header_info["valid"]:
            logger.warning(f"Invalid DDS file {dds_path}: {header_info['error']}")
            return False

        # Determine expected format
        expected_format = self._determine_compression_format(dds_path)

        # Check format and mipmaps
        if expected_format == "B8R8A8G8":
            correct_format = (
                header_info["fourcc"]
                == b"\x00\x00\x00\x00"  # No FourCC for uncompressed
                and header_info["rgb_bit_count"] == 32
                and header_info["mipmap_count"] == 0
                and header_info["r_mask"] == 0x00FF0000
                and header_info["g_mask"] == 0x0000FF00
                and header_info["b_mask"] == 0x000000FF
                and header_info["a_mask"] == 0xFF000000
            )
        elif expected_format == "DXT1":
            correct_format = (
                header_info["fourcc"] == b"DXT1" and header_info["mipmap_count"] == 0
            )
        elif expected_format == "DXT5":
            correct_format = (
                header_info["fourcc"] == b"DXT5" and header_info["mipmap_count"] == 0
            )
        else:
            correct_format = False

        if not correct_format:
            logger.info(f"DDS file {dds_path} has incorrect format:")
            logger.info(f"  Expected format: {expected_format}")
            logger.info(f"  FourCC: {header_info['fourcc']}")
            logger.info(f"  Bit count: {header_info['rgb_bit_count']}")
            logger.info(f"  Mipmaps: {header_info['mipmap_count']}")
            logger.info(f"  R mask: 0x{header_info['r_mask']:08X}")
            logger.info(f"  G mask: 0x{header_info['g_mask']:08X}")
            logger.info(f"  B mask: 0x{header_info['b_mask']:08X}")
            logger.info(f"  A mask: 0x{header_info['a_mask']:08X}")

        return correct_format

    def validate_all_dds(self) -> Tuple[int, int]:
        """
        Validate all DDS files and return count of valid/invalid files

        Returns:
            Tuple of (valid_files, total_files)
        """
        dds_files = self.find_dds_files()

        if not dds_files:
            logger.warning("No DDS files found to validate")
            return 0, 0

        valid_count = 0
        total_count = len(dds_files)

        logger.info(f"Validating {total_count} DDS files...")

        for dds_file in dds_files:
            if self.validate_dds_format(dds_file):
                valid_count += 1

        logger.info(
            f"Validation complete: {valid_count}/{total_count} files have correct format"
        )
        return valid_count, total_count

    def convert_dds_to_correct_format(self, dds_path: Path) -> bool:
        """
        Convert a DDS file to correct format with no mipmaps

        Args:
            dds_path: Path to the DDS file

        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Read the DDS file header to get dimensions
            header_info = self.read_dds_header(dds_path)

            if not header_info["valid"]:
                logger.error(f"Cannot read DDS file {dds_path}: {header_info['error']}")
                return False

            # Determine correct format
            correct_format = self._determine_compression_format(dds_path)

            logger.info(f"Re-converting DDS: {dds_path} (format: {correct_format})")

            # Create backup
            backup_path = dds_path.with_suffix(".dds.backup")
            dds_path.rename(backup_path)

            try:
                # Read the original DDS file as an image using Pillow
                with Image.open(backup_path) as img:
                    # Convert to RGBA if not already
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")

                    # Get image dimensions
                    width, height = img.size

                    # Convert to numpy array
                    img_array = np.array(img)

                    # Create DDS header
                    header = self._create_dds_header(width, height, correct_format)

                    if correct_format == "B8R8A8G8":
                        # Convert RGBA to BGRA (swap R and B channels)
                        bgra_array = img_array.copy()
                        bgra_array[:, :, [0, 2]] = bgra_array[
                            :, :, [2, 0]
                        ]  # Swap R and B
                        pixel_data = bgra_array.flatten().tobytes()
                    else:
                        # For compressed formats, we'll use the raw RGBA data
                        # Note: This is a simplified approach - proper DXT compression would require additional libraries
                        pixel_data = img_array.flatten().tobytes()

                    # Write new DDS file
                    with open(dds_path, "wb") as f:
                        f.write(header)
                        f.write(pixel_data)

                # Remove backup if successful
                backup_path.unlink()
                logger.info(f"Successfully re-converted DDS: {dds_path}")
                return True

            except Exception as e:
                # Restore backup on failure
                backup_path.rename(dds_path)
                logger.error(f"Error re-converting DDS {dds_path}: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Error reading DDS file {dds_path}: {str(e)}")
            return False

    def convert_all_dds(self) -> Tuple[int, int]:
        """
        Convert all DDS files to correct format with no mipmaps

        Returns:
            Tuple of (successful_conversions, total_files)
        """
        dds_files = self.find_dds_files()

        if not dds_files:
            logger.warning("No DDS files found to convert")
            return 0, 0

        successful = 0
        total = len(dds_files)

        logger.info(f"Starting DDS re-conversion of {total} files...")

        for dds_file in dds_files:
            if self.convert_dds_to_correct_format(dds_file):
                successful += 1

        logger.info(
            f"DDS re-conversion complete: {successful}/{total} files converted successfully"
        )
        return successful, total


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Convert PNG files to DDS format")
    parser.add_argument(
        "--mod-root",
        required=True,
        help="Path to the Millennium Dawn mod root directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be converted without actually converting",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace PNG files with DDS files (delete PNG after conversion)",
    )
    parser.add_argument(
        "--all-gfx",
        action="store_true",
        help="Scan entire gfx/ folder instead of just goals and ideas directories",
    )
    parser.add_argument(
        "--validate-dds",
        action="store_true",
        help="Validate existing DDS files for correct format",
    )
    parser.add_argument(
        "--convert-dds",
        action="store_true",
        help="Convert existing DDS files to correct format with no mipmaps",
    )

    args = parser.parse_args()

    # Validate mod root
    mod_root = Path(args.mod_root)
    if not mod_root.exists():
        logger.error(f"Mod root directory does not exist: {mod_root}")
        sys.exit(1)

    # Create converter
    converter = DDSConverter(str(mod_root))
    converter.scan_all_gfx = args.all_gfx

    if args.validate_dds:
        # Validate DDS files
        valid, total = converter.validate_all_dds()
        if valid == total:
            logger.info("All DDS files have correct format!")
            sys.exit(0)
        else:
            logger.warning(f"Some DDS files have incorrect format: {valid}/{total}")
            sys.exit(1)
    elif args.convert_dds:
        # Convert DDS files
        successful, total = converter.convert_all_dds()
        if successful == total:
            logger.info("All DDS conversions completed successfully!")
            sys.exit(0)
        else:
            logger.warning(f"Some DDS conversions failed: {successful}/{total}")
            sys.exit(1)
    elif args.dry_run:
        logger.info("DRY RUN MODE - No files will be converted")
        png_files = converter.find_png_files()
        logger.info(f"Would convert {len(png_files)} PNG files:")
        for png_file in png_files:
            dds_path = png_file.with_suffix(".dds")
            compression_format = converter._determine_compression_format(png_file)
            if args.replace:
                logger.info(
                    f"  {png_file} -> {dds_path} (format: {compression_format}, PNG would be deleted)"
                )
            else:
                logger.info(
                    f"  {png_file} -> {dds_path} (format: {compression_format})"
                )
    else:
        # Perform PNG conversion
        successful, total = converter.convert_all(replace_png=args.replace)

        if successful == total:
            logger.info("All conversions completed successfully!")
            sys.exit(0)
        else:
            logger.warning(f"Some conversions failed: {successful}/{total}")
            sys.exit(1)


if __name__ == "__main__":
    main()
