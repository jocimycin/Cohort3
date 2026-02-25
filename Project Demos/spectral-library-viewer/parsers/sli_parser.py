"""
SLI (ENVI Spectral Library) Parser

Supports ENVI .sli/.hdr spectral library format:
  - .hdr header file contains metadata (band count, wavelengths, spectra names)
  - .sli binary file contains spectral data as float32 arrays
"""

import os
import struct
import re
import numpy as np


def _parse_hdr(hdr_content):
    """Parse ENVI .hdr header file content."""
    metadata = {}
    if isinstance(hdr_content, bytes):
        hdr_content = hdr_content.decode("utf-8", errors="replace")

    # Parse key = value pairs, handling multi-line {} blocks
    current_key = None
    current_value = ""
    in_block = False

    for line in hdr_content.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue

        if in_block:
            current_value += " " + line
            if "}" in line:
                in_block = False
                metadata[current_key] = current_value.strip()
                current_key = None
                current_value = ""
            continue

        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip()

            if "{" in value and "}" not in value:
                current_key = key
                current_value = value
                in_block = True
            else:
                metadata[key] = value

    return metadata


def _extract_list(value_str):
    """Extract a list from ENVI header value like {val1, val2, val3}."""
    cleaned = re.sub(r"[{}]", "", value_str)
    items = [item.strip() for item in cleaned.split(",") if item.strip()]
    return items


def parse_sli(file_content, filename="unknown.sli", hdr_content=None):
    """
    Parse ENVI Spectral Library (.sli) data.

    Args:
        file_content: Binary content of the .sli file
        filename: Name of the file
        hdr_content: Content of the accompanying .hdr file (required)

    Returns:
        dict with wavelengths, spectra, and metadata
    """
    if hdr_content is None:
        raise ValueError(
            "SLI format requires an accompanying .hdr header file. "
            "Please upload both the .sli and .hdr files together."
        )

    metadata = _parse_hdr(hdr_content)

    samples = int(metadata.get("samples", 0))
    lines = int(metadata.get("lines", 0))
    bands = int(metadata.get("bands", 0))
    data_type = int(metadata.get("data type", 4))
    byte_order = int(metadata.get("byte order", 0))
    interleave = metadata.get("interleave", "bsq").lower()

    # Determine number of spectra and bands
    # In ENVI spectral libraries: lines = num_spectra, samples = num_bands
    num_spectra = lines if lines > 0 else 1
    num_bands = samples if samples > 0 else bands

    # Data type mapping
    dtype_map = {
        1: np.uint8,
        2: np.int16,
        3: np.int32,
        4: np.float32,
        5: np.float64,
        12: np.uint16,
        13: np.uint32,
        14: np.int64,
        15: np.uint64,
    }
    dtype = dtype_map.get(data_type, np.float32)

    endian = ">" if byte_order == 1 else "<"
    dt = np.dtype(dtype).newbyteorder(endian)

    if isinstance(file_content, str):
        file_content = file_content.encode("latin-1")

    data = np.frombuffer(file_content, dtype=dt)

    if num_spectra > 0 and num_bands > 0:
        expected = num_spectra * num_bands
        if len(data) >= expected:
            data = data[:expected].reshape(num_spectra, num_bands)
        else:
            num_spectra = len(data) // num_bands
            data = data[: num_spectra * num_bands].reshape(num_spectra, num_bands)

    # Extract wavelengths
    wavelengths = []
    if "wavelength" in metadata:
        wl_list = _extract_list(metadata["wavelength"])
        wavelengths = [float(w) for w in wl_list]
    else:
        wavelengths = list(range(1, num_bands + 1))

    # Convert µm to nm if needed
    if len(wavelengths) > 0 and np.median(wavelengths) < 100:
        wavelengths = [w * 1000.0 for w in wavelengths]

    # Extract spectra names
    names = []
    if "spectra names" in metadata:
        names = _extract_list(metadata["spectra names"])
    elif "description" in metadata:
        names = _extract_list(metadata.get("description", ""))

    spectra = []
    for i in range(num_spectra):
        name = names[i] if i < len(names) else f"Spectrum_{i + 1}"
        values = data[i].tolist() if i < len(data) else []
        spectra.append({"name": name.strip(), "values": values})

    return {
        "wavelengths": wavelengths,
        "spectra": spectra,
        "metadata": {
            "filename": filename,
            "format": "SLI (ENVI Spectral Library)",
            "num_spectra": len(spectra),
            "num_bands": len(wavelengths),
            "wavelength_unit": "nm",
            "interleave": interleave,
        },
    }
