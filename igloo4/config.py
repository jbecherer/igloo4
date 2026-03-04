"""
config.py — App-wide constants, file-type mappings, and per-mode favourites.
"""

# Maps mode label → (engineering extension, science extension)
FILE_MODES = {
    "dbd + ebd  (full resolution)": ("dbd", "ebd"),
    "sbd + tbd  (subset)":          ("sbd", "tbd"),
}

# Extensions that trigger each mode (used for folder-tree filtering)
ALL_EXTENSIONS = {"dbd", "ebd", "sbd", "tbd"}

# Default favourite variables shown in the Favourites tab for each mode
FAVOURITES = {
    "dbd + ebd  (full resolution)": [
        "m_depth",
        "m_pitch",
        "m_roll",
        "m_speed",
        "m_battpos",
        "m_ballast_pumped",
        "sci_water_temp",
        "sci_water_cond",
        "sci_water_pressure",
    ],
    "sbd + tbd  (subset)": [
        "m_depth",
        "m_speed",
        "m_battpos",
        "sci_water_temp",
        "sci_water_cond",
        "sci_water_pressure",
        "sci_oxy4_oxygen",
        "sci_flntu_chlor_units",
    ],
}

# Plot-mode labels shown in the UI
PLOT_MODES = ["vs Time", "vs Depth", "vs Each Other"]

# Depth variable name used when plotting "vs Depth"
DEPTH_VARIABLE = "m_depth"

# Export DPI
EXPORT_DPI = 150
