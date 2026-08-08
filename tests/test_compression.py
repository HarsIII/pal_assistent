import struct
import zlib

import pytest

from save.adapters.compression import decompress, detect_format, SaveCompressionFormat


def test_detect_format_uncompressed_gvas():
    data = b"GVAS" + b"\x00" * 20
    assert detect_format(data) is SaveCompressionFormat.UNCOMPRESSED_GVAS


def test_detect_format_plz():
    data = b"\x00" * 8 + b"PlZ" + bytes([0x31]) + b"payload"
    assert detect_format(data) is SaveCompressionFormat.PLZ_ZLIB


def test_detect_format_plm():
    data = b"\x00" * 8 + b"PlM" + bytes([0x31]) + b"payload"
    assert detect_format(data) is SaveCompressionFormat.PLM_OODLE


def test_detect_format_cnk():
    data = b"\x00" * 8 + b"CNK" + bytes([0x31]) + b"payload"
    assert detect_format(data) is SaveCompressionFormat.CNK_CHUNK


def test_detect_format_unknown_raises():
    data = b"\x00" * 8 + b"???" + bytes([0x31])
    with pytest.raises(ValueError):
        detect_format(data)


def test_decompress_uncompressed_gvas_passthrough():
    data = b"GVAS" + b"hello world"
    result = decompress(data)
    assert result.detected_format is SaveCompressionFormat.UNCOMPRESSED_GVAS
    assert result.raw_gvas == data


def test_decompress_plz_single_zlib_roundtrip():
    original = b"GVAS" + b"some fake gvas payload bytes"
    compressed = zlib.compress(original)
    header = struct.pack("<II", len(original), len(compressed)) + b"PlZ" + bytes([0x31])
    data = header + compressed

    result = decompress(data)
    assert result.detected_format is SaveCompressionFormat.PLZ_ZLIB
    assert result.raw_gvas == original
    assert result.save_type == 0x31
