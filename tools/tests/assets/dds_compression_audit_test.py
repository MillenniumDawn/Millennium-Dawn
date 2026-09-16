"""Deterministic tests for tools/assets/dds_compression_audit.py.

Builds synthetic DDS files rather than shipping binary fixtures: legacy
uncompressed and FourCC headers, DX10 containers holding both block compressed
and uncompressed payloads, opaque and translucent alpha across mip levels,
truncated and malformed input, and the three output modes.
"""

import json
import struct

from shared.suite import dds_header, load_tool_module

audit = load_tool_module("assets/dds_compression_audit.py")

DDS_MAGIC = 0x20534444
DDSD_CAPS = 0x1
DDSCAPS_TEXTURE = 0x1000


def _pixelformat(flags, fourcc=0, bit_count=0, masks=(0, 0, 0, 0)):
    return struct.pack("<8I", 32, flags, fourcc, bit_count, *masks)


def _uncompressed(width, height, *, alpha_rows=None, mip_count=1, declared_mips=None):
    """A 32bpp BGRA DDS. alpha_rows maps mip index -> alpha byte for that level."""
    pf = _pixelformat(audit.DDPF_ALPHAPIXELS, bit_count=32, masks=(0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000))
    head = dds_header(
        DDS_MAGIC,
        DDSD_CAPS,
        height,
        width,
        width * height * 4,
        pf,
        DDSCAPS_TEXTURE,
        declared_mips if declared_mips is not None else mip_count,
    )
    body = b""
    w, h = width, height
    for level in range(mip_count):
        alpha = (alpha_rows or {}).get(level, 0xFF)
        body += struct.pack("<I", (alpha << 24) | 0x00112233) * (w * h)
        w, h = max(1, w // 2), max(1, h // 2)
    return head + body


def _fourcc(width, height, tag=b"DXT1"):
    pf = _pixelformat(audit.DDPF_FOURCC, fourcc=struct.unpack("<I", tag)[0])
    return dds_header(DDS_MAGIC, DDSD_CAPS, height, width, 0, pf, DDSCAPS_TEXTURE, 1) + b"\x00" * 64


def _dx10(width, height, dxgi):
    pf = _pixelformat(audit.DDPF_FOURCC, fourcc=struct.unpack("<I", b"DX10")[0])
    head = dds_header(DDS_MAGIC, DDSD_CAPS, height, width, 0, pf, DDSCAPS_TEXTURE, 1)
    ext = struct.pack("<5I", dxgi, 3, 0, 1, 0)
    return head + ext + struct.pack("<I", 0xFF112233) * (width * height)


def _write(tmp_path, name, blob):
    path = tmp_path / name
    path.write_bytes(blob)
    return path


# --- header parsing --------------------------------------------------------


def test_opaque_texture_is_offered_as_dxt1(tmp_path):
    path = _write(tmp_path, "opaque.dds", _uncompressed(8, 8))
    texture = audit.parse(path)
    assert texture.compressed is False
    assert texture.alpha_used is False
    assert texture.target == "DXT1"


def test_translucent_texture_is_offered_as_dxt5(tmp_path):
    path = _write(tmp_path, "glass.dds", _uncompressed(8, 8, alpha_rows={0: 0x40}))
    assert audit.parse(path).target == "DXT5"


def test_alpha_in_a_lower_mip_still_forces_dxt5(tmp_path):
    """The top level is opaque; only the second level is translucent."""
    blob = _uncompressed(8, 8, alpha_rows={1: 0x10}, mip_count=4)
    texture = audit.parse(_write(tmp_path, "deep.dds", blob))
    assert texture.alpha_used is True
    assert texture.target == "DXT5"


def test_fourcc_texture_is_reported_as_already_compressed(tmp_path):
    texture = audit.parse(_write(tmp_path, "done.dds", _fourcc(8, 8)))
    assert texture.compressed is True
    assert texture.fourcc == "DXT1"


def test_alpha_scan_is_skipped_below_the_floor(tmp_path):
    """Under the floor the target never matters, so the scan is not paid for."""
    path = _write(tmp_path, "tiny.dds", _uncompressed(8, 8, alpha_rows={0: 0x40}))
    assert audit.parse(path, alpha_floor=1 << 20).alpha_used is False


# --- DX10 containers -------------------------------------------------------


def test_dx10_block_compressed_payload_counts_as_compressed(tmp_path):
    texture = audit.parse(_write(tmp_path, "bc7.dds", _dx10(8, 8, 98)))
    assert texture.compressed is True
    assert texture.fourcc == "BC7"


def test_dx10_uncompressed_payload_is_still_a_candidate(tmp_path):
    """B8G8R8A8_UNORM behind a DX10 container is not compressed."""
    texture = audit.parse(_write(tmp_path, "bgra.dds", _dx10(8, 8, 87)))
    assert texture.compressed is False
    assert texture.fourcc is None


# --- malformed input -------------------------------------------------------


def test_a_runaway_mip_count_is_clamped(tmp_path):
    """dwMipMapCount is attacker controlled and must not drive the loop."""
    blob = _uncompressed(8, 8, declared_mips=0xFFFFFFFF)
    texture = audit.parse(_write(tmp_path, "evil.dds", blob))
    assert texture.mipmaps == audit._mip_levels(8, 8) == 4
    assert texture.projected_size() > 0


def test_zero_dimensions_are_rejected(tmp_path):
    assert audit.parse(_write(tmp_path, "zero.dds", _uncompressed(0, 0))) is None


def test_truncated_file_is_rejected(tmp_path):
    assert audit.parse(_write(tmp_path, "short.dds", b"DDS " + b"\x00" * 16)) is None


def test_non_dds_file_is_rejected(tmp_path):
    assert audit.parse(_write(tmp_path, "notdds.dds", b"PNG!" + b"\x00" * 200)) is None


def test_truncated_dx10_extension_is_rejected(tmp_path):
    pf = _pixelformat(audit.DDPF_FOURCC, fourcc=struct.unpack("<I", b"DX10")[0])
    blob = dds_header(DDS_MAGIC, DDSD_CAPS, 8, 8, 0, pf, DDSCAPS_TEXTURE, 1) + b"\x00" * 4
    assert audit.parse(_write(tmp_path, "cut.dds", blob)) is None


# --- projection and geometry ----------------------------------------------


def test_block_alignment_gates_the_recommendation(tmp_path):
    assert audit.parse(_write(tmp_path, "ok.dds", _uncompressed(8, 8))).block_aligned is True
    assert audit.parse(_write(tmp_path, "odd.dds", _uncompressed(7, 8))).block_aligned is False


def test_projection_counts_every_mip_level(tmp_path):
    single = audit.parse(_write(tmp_path, "one.dds", _uncompressed(8, 8, mip_count=1)))
    chained = audit.parse(_write(tmp_path, "many.dds", _uncompressed(8, 8, mip_count=4)))
    assert chained.projected_size() > single.projected_size()


def test_dxt1_projection_is_half_of_dxt5(tmp_path):
    opaque = audit.parse(_write(tmp_path, "a.dds", _uncompressed(8, 8)))
    glass = audit.parse(_write(tmp_path, "b.dds", _uncompressed(8, 8, alpha_rows={0: 0x40})))
    assert (glass.projected_size() - audit.HEADER) == 2 * (opaque.projected_size() - audit.HEADER)


# --- reporting and output modes -------------------------------------------


def test_report_splits_candidates_from_misaligned(tmp_path):
    _write(tmp_path, "big.dds", _uncompressed(64, 64))
    _write(tmp_path, "odd.dds", _uncompressed(63, 64))
    _write(tmp_path, "done.dds", _fourcc(64, 64))
    convert, skipped, counts, _ = audit.build_report([tmp_path], floor=0)
    assert [t.path.name for t in convert] == ["big.dds"]
    assert [t.path.name for t in skipped] == ["odd.dds"]
    assert counts["DXT1"] == 1


def test_texconv_command_writes_the_mip_count_explicitly(tmp_path):
    texture = audit.parse(_write(tmp_path, "one.dds", _uncompressed(8, 8, mip_count=1)))
    command = audit.texconv_command(texture)
    assert "-m 1" in command and "-m 0" not in command
    assert "BC1_UNORM" in command


def test_texconv_command_uses_bc3_when_alpha_is_used(tmp_path):
    texture = audit.parse(_write(tmp_path, "glass.dds", _uncompressed(8, 8, alpha_rows={0: 0x40})))
    assert "BC3_UNORM" in audit.texconv_command(texture)


def test_json_output_lists_candidates(tmp_path, capsys):
    _write(tmp_path, "big.dds", _uncompressed(64, 64))
    audit.main([str(tmp_path), "--min-kb", "0", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["convert"][0]["target"] == "DXT1"
    assert payload["total_saving_bytes"] > 0


def test_emit_commands_mode_prints_one_line_per_file(tmp_path, capsys):
    _write(tmp_path, "big.dds", _uncompressed(64, 64))
    audit.main([str(tmp_path), "--min-kb", "0", "--emit-commands"])
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.startswith("texconv")]
    assert len(lines) == 1


def test_text_report_and_by_dir_both_render(tmp_path, capsys):
    _write(tmp_path, "big.dds", _uncompressed(64, 64))
    _write(tmp_path, "odd.dds", _uncompressed(63, 64))
    audit.main([str(tmp_path), "--min-kb", "0"])
    out = capsys.readouterr().out
    assert "DDS INVENTORY" in out and "SKIPPED" in out
    audit.main([str(tmp_path), "--min-kb", "0", "--by-dir"])
    assert "MB" in capsys.readouterr().out


def test_collect_accepts_a_single_file(tmp_path):
    path = _write(tmp_path, "one.dds", _uncompressed(8, 8))
    assert list(audit.collect([path])) == [path]


def test_mip_level_helper_matches_the_chain_length():
    assert audit._mip_levels(1, 1) == 1
    assert audit._mip_levels(8, 8) == 4
    # 1920 halves ten times before reaching 1, so the chain is eleven levels.
    assert audit._mip_levels(1920, 1080) == 11
