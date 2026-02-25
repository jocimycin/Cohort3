"""
ASCII Spectral Library Parser

Supports common ASCII/text spectral formats:
  - USGS ASCII spectral library format
  - ASD FieldSpec ASCII export
  - Generic whitespace/tab-delimited spectral files
  - Two-column (wavelength, reflectance) format
  - Multi-column format with header
"""

import re
import numpy as np


def _is_numeric_line(line):
    """Check if a line contains only numeric values."""
    parts = line.strip().split()
    if not parts:
        return False
    try:
        for p in parts:
            float(p)
        return True
    except ValueError:
        return False


def _detect_usgs_format(text):
    """Detect USGS ASCII spectral library format."""
    lines = text.strip().splitlines()
    for line in lines[:20]:
        if "USGS" in line.upper() or "Clark" in line or "splib" in line.lower():
            return True
    return False


def _parse_usgs_ascii(text, filename):
    """Parse USGS ASCII spectral library format."""
    lines = text.strip().splitlines()

    header_lines = []
    data_lines = []
    data_started = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not data_started and _is_numeric_line(stripped):
            data_started = True
        if data_started:
            if _is_numeric_line(stripped):
                data_lines.append(stripped)
        else:
            header_lines.append(stripped)

    # Extract mineral name from header
    name = filename.replace(".txt", "").replace(".asc", "")
    if header_lines:
        name = header_lines[0].strip()

    wavelengths = []
    values = []

    for line in data_lines:
        parts = line.split()
        if len(parts) >= 2:
            wl = float(parts[0])
            val = float(parts[1])
            if val > -1.0:  # USGS uses -1.23e+34 for no-data
                wavelengths.append(wl)
                values.append(val)

    # Convert µm to nm
    if wavelengths and np.median(wavelengths) < 100:
        wavelengths = [w * 1000.0 for w in wavelengths]

    return {
        "wavelengths": wavelengths,
        "spectra": [{"name": name, "values": values}],
        "metadata": {
            "filename": filename,
            "format": "ASCII (USGS)",
            "num_spectra": 1,
            "num_bands": len(wavelengths),
            "wavelength_unit": "nm",
        },
    }


def _parse_multicolumn_ascii(text, filename):
    """Parse multi-column ASCII spectral data."""
    lines = text.strip().splitlines()

    # Find header and data start
    header_names = []
    data_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue
        if _is_numeric_line(stripped):
            data_lines.append(stripped)
        elif not data_lines:
            # This might be a header row
            parts = re.split(r"[\t,;]+|\s{2,}", stripped)
            if len(parts) >= 2:
                header_names = [p.strip() for p in parts]

    if not data_lines:
        raise ValueError("No numeric data found in ASCII file")

    # Parse data
    all_values = []
    for line in data_lines:
        parts = line.split()
        row = []
        for p in parts:
            try:
                row.append(float(p))
            except ValueError:
                row.append(np.nan)
        all_values.append(row)

    data = np.array(all_values)
    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError("ASCII data must have at least 2 columns")

    wavelengths = data[:, 0]
    if np.median(wavelengths) < 100:
        wavelengths = wavelengths * 1000.0
    wavelengths = wavelengths.tolist()

    spectra = []
    for j in range(1, data.shape[1]):
        name = header_names[j] if j < len(header_names) else f"Spectrum_{j}"
        vals = data[:, j]
        # Handle no-data values
        vals = np.where(np.abs(vals) > 1e10, np.nan, vals)
        spectra.append({"name": name, "values": vals.tolist()})

    return {
        "wavelengths": wavelengths,
        "spectra": spectra,
        "metadata": {
            "filename": filename,
            "format": "ASCII (Multi-column)",
            "num_spectra": len(spectra),
            "num_bands": len(wavelengths),
            "wavelength_unit": "nm",
        },
    }


def parse_ascii(file_content, filename="unknown.txt"):
    """
    Parse ASCII spectral data in various formats.

    Returns:
        dict with wavelengths, spectra, and metadata
    """
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8", errors="replace")

    if _detect_usgs_format(file_content):
        return _parse_usgs_ascii(file_content, filename)

    return _parse_multicolumn_ascii(file_content, filename)
