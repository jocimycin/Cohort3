"""Unit tests for spectral file parsers."""

import sys
import os
import struct
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers import parse_csv, parse_sli, parse_ascii


def test_csv_basic():
    csv_data = "wavelength,Mineral_A,Mineral_B\n400,0.5,0.8\n500,0.55,0.82\n600,0.6,0.85\n"
    result = parse_csv(csv_data, "test.csv")
    assert len(result["wavelengths"]) == 3
    assert len(result["spectra"]) == 2
    assert result["spectra"][0]["name"] == "Mineral_A"
    assert result["metadata"]["format"] == "CSV"
    print("  PASS: test_csv_basic")


def test_csv_micrometer_conversion():
    csv_data = "wl,spec\n0.4,0.5\n0.5,0.55\n0.6,0.6\n"
    result = parse_csv(csv_data, "test.csv")
    assert result["wavelengths"][0] == 400.0
    assert result["wavelengths"][1] == 500.0
    print("  PASS: test_csv_micrometer_conversion")


def test_csv_tab_delimited():
    csv_data = "wavelength\tMineral\n400\t0.5\n500\t0.55\n"
    result = parse_csv(csv_data, "test.csv")
    assert len(result["spectra"]) == 1
    print("  PASS: test_csv_tab_delimited")


def test_csv_bytes_input():
    csv_data = b"wavelength,spec\n400,0.5\n500,0.55\n"
    result = parse_csv(csv_data, "test.csv")
    assert len(result["wavelengths"]) == 2
    print("  PASS: test_csv_bytes_input")


def test_ascii_multicolumn():
    ascii_data = "# comment\nwavelength\treflectance\n400\t0.5\n500\t0.55\n600\t0.6\n"
    result = parse_ascii(ascii_data, "test.txt")
    assert len(result["wavelengths"]) == 3
    assert len(result["spectra"]) == 1
    print("  PASS: test_ascii_multicolumn")


def test_ascii_usgs_format():
    ascii_data = (
        "USGS Spectral Library splib07a\n"
        "Kaolinite CM9\n"
        "\n"
        "0.4  0.5\n"
        "0.5  0.55\n"
        "0.6  0.6\n"
    )
    result = parse_ascii(ascii_data, "kaolinite.txt")
    assert "USGS" in result["metadata"]["format"]
    assert result["wavelengths"][0] == 400.0
    print("  PASS: test_ascii_usgs_format")


def test_ascii_bytes():
    data = b"wl\tval\n400\t0.5\n500\t0.6\n"
    result = parse_ascii(data, "test.asc")
    assert len(result["wavelengths"]) == 2
    print("  PASS: test_ascii_bytes")


def test_sli_parser():
    # Create minimal ENVI spectral library
    num_spectra = 2
    num_bands = 5
    wavelengths = [400.0, 500.0, 600.0, 700.0, 800.0]

    hdr_content = (
        "ENVI\n"
        f"samples = {num_bands}\n"
        f"lines = {num_spectra}\n"
        f"bands = 1\n"
        "data type = 4\n"
        "byte order = 0\n"
        "interleave = bsq\n"
        "wavelength = {400.0, 500.0, 600.0, 700.0, 800.0}\n"
        "spectra names = {Mineral_A, Mineral_B}\n"
    )

    # Create binary data (float32, little-endian)
    values = [0.5, 0.55, 0.6, 0.65, 0.7, 0.8, 0.82, 0.85, 0.88, 0.9]
    sli_content = struct.pack(f"<{len(values)}f", *values)

    result = parse_sli(sli_content, "test.sli", hdr_content=hdr_content)
    assert len(result["spectra"]) == 2
    assert result["spectra"][0]["name"] == "Mineral_A"
    assert len(result["wavelengths"]) == 5
    assert abs(result["spectra"][0]["values"][0] - 0.5) < 0.01
    print("  PASS: test_sli_parser")


def test_sli_missing_hdr():
    try:
        parse_sli(b"\x00" * 20, "test.sli", hdr_content=None)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("  PASS: test_sli_missing_hdr")


if __name__ == "__main__":
    print("Running parser tests...")
    test_csv_basic()
    test_csv_micrometer_conversion()
    test_csv_tab_delimited()
    test_csv_bytes_input()
    test_ascii_multicolumn()
    test_ascii_usgs_format()
    test_ascii_bytes()
    test_sli_parser()
    test_sli_missing_hdr()
    print("\nAll 9 tests passed!")
