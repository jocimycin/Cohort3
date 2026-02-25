"""
Generate realistic sample spectral library data for built-in demonstration.

Creates synthetic but scientifically representative spectra for common minerals,
vegetation, and other materials based on published spectral characteristics.
"""

import json
import numpy as np
import os


def gaussian(x, center, width, depth):
    """Generate Gaussian absorption feature."""
    return depth * np.exp(-0.5 * ((x - center) / width) ** 2)


def generate_wavelengths():
    """Generate wavelength array from 350nm to 2500nm (VNIR-SWIR range)."""
    return np.arange(350, 2501, 2).tolist()


def make_spectrum(wavelengths, baseline, absorptions, noise_level=0.002):
    """Create a spectrum with absorption features and realistic noise."""
    wl = np.array(wavelengths)
    spectrum = np.full_like(wl, baseline, dtype=float)

    # Add slight slope
    slope = np.random.uniform(-0.00002, 0.00002)
    spectrum += slope * (wl - wl.mean())

    for center, width, depth in absorptions:
        spectrum -= gaussian(wl, center, width, depth)

    # Add realistic noise
    spectrum += np.random.normal(0, noise_level, len(wl))
    spectrum = np.clip(spectrum, 0.0, 1.0)

    return spectrum.tolist()


def generate_sample_library():
    """Generate a comprehensive sample spectral library."""
    wavelengths = generate_wavelengths()

    minerals = [
        {
            "name": "Kaolinite (Clay Mineral)",
            "category": "Minerals",
            "baseline": 0.75,
            "absorptions": [
                (1400, 30, 0.25),
                (1900, 40, 0.20),
                (2160, 25, 0.30),
                (2205, 20, 0.35),
                (950, 80, 0.03),
                (500, 100, 0.08),
            ],
            "description": "Phyllosilicate clay mineral with diagnostic Al-OH absorption doublet near 2.2 µm",
        },
        {
            "name": "Montmorillonite (Smectite)",
            "category": "Minerals",
            "baseline": 0.62,
            "absorptions": [
                (1400, 35, 0.22),
                (1900, 55, 0.35),
                (2205, 30, 0.20),
                (500, 120, 0.10),
            ],
            "description": "Swelling clay mineral with broad water absorption and Al-OH feature",
        },
        {
            "name": "Muscovite (Mica)",
            "category": "Minerals",
            "baseline": 0.70,
            "absorptions": [
                (1400, 25, 0.30),
                (1900, 35, 0.18),
                (2200, 18, 0.40),
                (2350, 20, 0.15),
                (500, 80, 0.05),
            ],
            "description": "Potassium aluminum phyllosilicate with sharp 2.2 µm Al-OH absorption",
        },
        {
            "name": "Calcite (Carbonate)",
            "category": "Minerals",
            "baseline": 0.85,
            "absorptions": [
                (1900, 30, 0.08),
                (2335, 20, 0.30),
                (2160, 25, 0.05),
                (1400, 25, 0.05),
                (2530, 20, 0.10),
            ],
            "description": "Calcium carbonate with diagnostic CO3 absorption near 2.34 µm",
        },
        {
            "name": "Dolomite (Carbonate)",
            "category": "Minerals",
            "baseline": 0.82,
            "absorptions": [
                (1900, 30, 0.07),
                (2320, 20, 0.28),
                (2160, 20, 0.04),
                (1400, 25, 0.05),
                (2510, 20, 0.12),
            ],
            "description": "Ca-Mg carbonate with CO3 absorption shifted to 2.32 µm compared to calcite",
        },
        {
            "name": "Hematite (Iron Oxide)",
            "category": "Minerals",
            "baseline": 0.30,
            "absorptions": [
                (530, 60, 0.08),
                (650, 40, 0.03),
                (860, 100, 0.12),
                (400, 30, 0.10),
            ],
            "description": "Iron oxide with strong visible absorption and charge transfer features",
        },
        {
            "name": "Goethite (Iron Oxyhydroxide)",
            "category": "Minerals",
            "baseline": 0.40,
            "absorptions": [
                (480, 40, 0.10),
                (670, 50, 0.05),
                (900, 80, 0.15),
                (400, 25, 0.12),
                (1400, 25, 0.03),
                (1900, 30, 0.04),
            ],
            "description": "Hydrated iron oxide with crystal field and OH absorptions",
        },
        {
            "name": "Gypsum (Sulfate)",
            "category": "Minerals",
            "baseline": 0.88,
            "absorptions": [
                (1000, 20, 0.02),
                (1200, 20, 0.03),
                (1400, 20, 0.10),
                (1450, 15, 0.08),
                (1750, 20, 0.05),
                (1900, 30, 0.15),
                (1945, 15, 0.10),
                (2215, 15, 0.08),
                (2270, 15, 0.06),
            ],
            "description": "Hydrated calcium sulfate with multiple water and OH absorptions",
        },
        {
            "name": "Alunite (Sulfate)",
            "category": "Minerals",
            "baseline": 0.72,
            "absorptions": [
                (1400, 25, 0.20),
                (1480, 20, 0.18),
                (1760, 15, 0.10),
                (1900, 35, 0.12),
                (2165, 20, 0.25),
                (2325, 15, 0.08),
                (500, 80, 0.05),
            ],
            "description": "Potassium aluminum sulfate hydroxide with diagnostic 1.48 and 2.17 µm features",
        },
        {
            "name": "Chlorite (Phyllosilicate)",
            "category": "Minerals",
            "baseline": 0.35,
            "absorptions": [
                (700, 60, 0.05),
                (900, 70, 0.08),
                (1400, 30, 0.12),
                (1900, 40, 0.08),
                (2250, 20, 0.15),
                (2340, 20, 0.12),
            ],
            "description": "Fe-Mg phyllosilicate with Mg-OH absorption near 2.35 µm",
        },
        {
            "name": "Epidote (Sorosilicate)",
            "category": "Minerals",
            "baseline": 0.28,
            "absorptions": [
                (450, 40, 0.06),
                (600, 60, 0.03),
                (1000, 80, 0.08),
                (1550, 20, 0.02),
                (1830, 20, 0.03),
                (2250, 15, 0.05),
                (2340, 15, 0.08),
            ],
            "description": "Ca-Al-Fe sorosilicate with Fe3+ crystal field absorptions",
        },
        {
            "name": "Talc (Phyllosilicate)",
            "category": "Minerals",
            "baseline": 0.80,
            "absorptions": [
                (1390, 20, 0.15),
                (1900, 30, 0.05),
                (2310, 18, 0.30),
                (2390, 15, 0.10),
            ],
            "description": "Mg phyllosilicate with strong Mg-OH absorption near 2.31 µm",
        },
        {
            "name": "Quartz (Tectosilicate)",
            "category": "Minerals",
            "baseline": 0.92,
            "absorptions": [
                (1400, 20, 0.02),
                (1900, 25, 0.03),
            ],
            "description": "SiO2 with minimal VNIR-SWIR absorptions; diagnostic features in thermal IR",
        },
        {
            "name": "Olivine - Forsterite",
            "category": "Minerals",
            "baseline": 0.55,
            "absorptions": [
                (1050, 120, 0.20),
                (850, 80, 0.08),
                (500, 60, 0.08),
            ],
            "description": "Mg-rich olivine with broad 1 µm Fe2+ crystal field absorption",
        },
        {
            "name": "Pyroxene - Augite",
            "category": "Minerals",
            "baseline": 0.30,
            "absorptions": [
                (1000, 100, 0.10),
                (2000, 150, 0.08),
                (600, 60, 0.03),
            ],
            "description": "Ca-Mg-Fe pyroxene with 1 and 2 µm Fe2+ crystal field absorptions",
        },
    ]

    vegetation = [
        {
            "name": "Green Vegetation (Healthy Leaf)",
            "category": "Vegetation",
            "baseline": 0.50,
            "absorptions": [],
            "description": "Healthy green vegetation with chlorophyll absorption and red edge",
            "custom": True,
        },
        {
            "name": "Dry Vegetation (Senescent)",
            "category": "Vegetation",
            "baseline": 0.45,
            "absorptions": [],
            "description": "Dry/senescent vegetation with cellulose-lignin absorptions",
            "custom": True,
        },
    ]

    other = [
        {
            "name": "Water (Clear)",
            "category": "Liquids",
            "baseline": 0.05,
            "absorptions": [],
            "description": "Clear water with strong NIR-SWIR absorption",
            "custom": True,
        },
        {
            "name": "Concrete (Construction)",
            "category": "Artificial Materials",
            "baseline": 0.35,
            "absorptions": [
                (1400, 30, 0.05),
                (1900, 40, 0.08),
                (2335, 20, 0.05),
            ],
            "description": "Construction concrete with carbonate and water features",
        },
        {
            "name": "Asphalt (Road Surface)",
            "category": "Artificial Materials",
            "baseline": 0.08,
            "absorptions": [
                (1730, 30, 0.02),
                (2300, 30, 0.01),
                (1900, 30, 0.01),
            ],
            "description": "Dark road surface asphalt with hydrocarbon absorptions",
        },
        {
            "name": "Desert Soil (Arid Region)",
            "category": "Soils & Mixtures",
            "baseline": 0.35,
            "absorptions": [
                (500, 80, 0.06),
                (900, 100, 0.04),
                (1400, 25, 0.05),
                (1900, 35, 0.06),
                (2200, 20, 0.04),
            ],
            "description": "Arid region soil with iron oxide and clay mineral features",
        },
    ]

    wl = np.array(wavelengths)
    spectra_list = []

    for item in minerals + other:
        if item.get("custom"):
            continue
        values = make_spectrum(wavelengths, item["baseline"], item["absorptions"])
        spectra_list.append(
            {
                "name": item["name"],
                "category": item["category"],
                "values": values,
                "description": item["description"],
            }
        )

    # Custom vegetation spectra
    # Healthy green vegetation
    veg_spectrum = np.ones_like(wl, dtype=float) * 0.05
    # Chlorophyll absorption in blue and red
    veg_spectrum -= gaussian(wl, 450, 30, 0.03)
    veg_spectrum -= gaussian(wl, 680, 25, 0.04)
    # Green peak
    veg_spectrum += gaussian(wl, 550, 40, 0.04)
    # Red edge (~700-750nm) ramp up
    red_edge = 1.0 / (1.0 + np.exp(-0.05 * (wl - 720)))
    veg_spectrum = veg_spectrum * (1 - red_edge) + 0.48 * red_edge
    # NIR plateau
    veg_spectrum += gaussian(wl, 900, 200, 0.02)
    # Water absorptions
    veg_spectrum -= gaussian(wl, 970, 30, 0.04)
    veg_spectrum -= gaussian(wl, 1200, 40, 0.06)
    veg_spectrum -= gaussian(wl, 1450, 40, 0.15)
    veg_spectrum -= gaussian(wl, 1940, 50, 0.20)
    veg_spectrum -= gaussian(wl, 2500, 100, 0.08)
    veg_spectrum = np.clip(veg_spectrum, 0.0, 1.0)
    veg_spectrum += np.random.normal(0, 0.002, len(wl))
    veg_spectrum = np.clip(veg_spectrum, 0.0, 1.0)

    spectra_list.append(
        {
            "name": "Green Vegetation (Healthy Leaf)",
            "category": "Vegetation",
            "values": veg_spectrum.tolist(),
            "description": vegetation[0]["description"],
        }
    )

    # Dry vegetation
    dry_spectrum = np.ones_like(wl, dtype=float) * 0.15
    dry_ramp = np.clip((wl - 400) / 600, 0, 1) * 0.30
    dry_spectrum += dry_ramp
    dry_spectrum -= gaussian(wl, 1730, 25, 0.04)
    dry_spectrum -= gaussian(wl, 2100, 30, 0.06)
    dry_spectrum -= gaussian(wl, 2300, 25, 0.05)
    dry_spectrum -= gaussian(wl, 1400, 30, 0.05)
    dry_spectrum -= gaussian(wl, 1900, 40, 0.08)
    dry_spectrum += np.random.normal(0, 0.002, len(wl))
    dry_spectrum = np.clip(dry_spectrum, 0.0, 1.0)

    spectra_list.append(
        {
            "name": "Dry Vegetation (Senescent)",
            "category": "Vegetation",
            "values": dry_spectrum.tolist(),
            "description": vegetation[1]["description"],
        }
    )

    # Water
    water_spectrum = np.ones_like(wl, dtype=float) * 0.06
    water_spectrum -= gaussian(wl, 600, 200, 0.02)
    water_spectrum += gaussian(wl, 480, 60, 0.02)
    water_ramp = np.clip((wl - 700) / 300, 0, 1) * 0.055
    water_spectrum -= water_ramp
    water_spectrum -= gaussian(wl, 970, 30, 0.01)
    water_spectrum = np.clip(water_spectrum, 0.001, 1.0)
    water_spectrum[wl > 1100] = 0.001
    water_spectrum += np.random.normal(0, 0.001, len(wl))
    water_spectrum = np.clip(water_spectrum, 0.0, 1.0)

    spectra_list.append(
        {
            "name": "Water (Clear)",
            "category": "Liquids",
            "values": water_spectrum.tolist(),
            "description": "Clear water with strong NIR-SWIR absorption",
        }
    )

    library = {
        "wavelengths": wavelengths,
        "spectra": spectra_list,
        "metadata": {
            "filename": "Built-in Sample Library",
            "format": "Generated",
            "num_spectra": len(spectra_list),
            "num_bands": len(wavelengths),
            "wavelength_unit": "nm",
            "description": "Synthetic spectral library based on published mineral spectral characteristics (USGS, JPL, ASTER spectral libraries)",
        },
    }

    return library


if __name__ == "__main__":
    library = generate_sample_library()
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static",
        "data",
        "sample_library.json",
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(library, f)
    print(f"Generated sample library with {library['metadata']['num_spectra']} spectra")
    print(f"Saved to {output_path}")
