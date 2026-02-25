"""
CSV Spectral Library Parser

Supports common CSV formats for spectral data:
  - First column: wavelength (nm, µm auto-detected)
  - Remaining columns: reflectance/emissivity values per mineral/material
  - Header row with mineral names expected
"""

import io
import csv
import numpy as np
import pandas as pd


def _detect_delimiter(text):
    """Auto-detect CSV delimiter."""
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(text[:4096])
        return dialect.delimiter
    except csv.Error:
        for delim in [",", "\t", ";", " "]:
            if delim in text[:1024]:
                return delim
        return ","


def _normalize_wavelengths(wavelengths):
    """Convert wavelengths to nanometers if they appear to be in micrometers."""
    if len(wavelengths) == 0:
        return wavelengths
    median_val = np.median(wavelengths)
    if median_val < 100:
        return wavelengths * 1000.0
    return wavelengths


def parse_csv(file_content, filename="unknown.csv"):
    """
    Parse CSV spectral data.

    Returns:
        dict with keys:
            - wavelengths: list of wavelength values (nm)
            - spectra: list of dicts with 'name' and 'values'
            - metadata: dict with parsing info
    """
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8", errors="replace")

    delimiter = _detect_delimiter(file_content)

    df = pd.read_csv(io.StringIO(file_content), delimiter=delimiter)

    if df.empty or df.shape[1] < 2:
        raise ValueError("CSV must have at least 2 columns (wavelength + 1 spectrum)")

    # First column is wavelengths
    wavelength_col = df.columns[0]
    wavelengths = pd.to_numeric(df[wavelength_col], errors="coerce").dropna().values
    wavelengths = _normalize_wavelengths(wavelengths).tolist()

    spectra = []
    for col in df.columns[1:]:
        values = pd.to_numeric(df[col], errors="coerce").values
        valid_mask = ~np.isnan(values[: len(wavelengths)])
        cleaned = np.where(valid_mask, values[: len(wavelengths)], 0.0).tolist()
        spectra.append({"name": str(col).strip(), "values": cleaned})

    return {
        "wavelengths": wavelengths,
        "spectra": spectra,
        "metadata": {
            "filename": filename,
            "format": "CSV",
            "num_spectra": len(spectra),
            "num_bands": len(wavelengths),
            "wavelength_unit": "nm",
        },
    }
