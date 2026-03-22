# forkairos/vocabulary.py
"""
Canonical variable vocabulary for forkairos.
All providers map their native variable names to this vocabulary.
Users always receive outputs with these names, units, and CF standard_names.
"""

CANONICAL_VARIABLES = {
    "temperature_2m": {
        "description":   "Air temperature at 2m",
        "units":         "degC",
        "standard_name": "air_temperature",
    },
    "dewpoint_2m": {
        "description":   "Dewpoint temperature at 2m",
        "units":         "degC",
        "standard_name": "dew_point_temperature",
    },
    "precipitation": {
        "description":   "Total precipitation",
        "units":         "mm",
        "standard_name": "precipitation_flux",
    },
    "snowfall": {
        "description":   "Snowfall amount",
        "units":         "mm",
        "standard_name": "snowfall_flux",
    },
    "snow_depth": {
        "description":   "Snow depth",
        "units":         "m",
        "standard_name": "surface_snow_thickness",
    },
    "relative_humidity_2m": {
        "description":   "Relative humidity at 2m",
        "units":         "%",
        "standard_name": "relative_humidity",
    },
    "wind_speed_10m": {
        "description":   "Wind speed at 10m",
        "units":         "m s-1",
        "standard_name": "wind_speed",
    },
    "wind_u_10m": {
        "description":   "U-component of wind at 10m",
        "units":         "m s-1",
        "standard_name": "eastward_wind",
    },
    "wind_v_10m": {
        "description":   "V-component of wind at 10m",
        "units":         "m s-1",
        "standard_name": "northward_wind",
    },
    "wind_direction_10m": {
        "description":   "Wind direction at 10m",
        "units":         "degree",
        "standard_name": "wind_from_direction",
    },
    "surface_pressure": {
        "description":   "Surface pressure",
        "units":         "hPa",
        "standard_name": "surface_air_pressure",
    },
    "shortwave_radiation": {
        "description":   "Downwelling shortwave radiation",
        "units":         "W m-2",
        "standard_name": "surface_downwelling_shortwave_flux_in_air",
    },
    "longwave_radiation": {
        "description":   "Downwelling longwave radiation",
        "units":         "W m-2",
        "standard_name": "surface_downwelling_longwave_flux_in_air",
    },
    "cloud_cover": {
        "description":   "Total cloud cover",
        "units":         "%",
        "standard_name": "cloud_area_fraction",
    },
    "geopotential_height_500hPa": {
        "description":   "Geopotential height at 500 hPa",
        "units":         "m",
        "standard_name": "geopotential_height",
    },
    "geopotential_height_700hPa": {
        "description":   "Geopotential height at 700 hPa",
        "units":         "m",
        "standard_name": "geopotential_height",
    },
    "geopotential_height_850hPa": {
        "description":   "Geopotential height at 850 hPa",
        "units":         "m",
        "standard_name": "geopotential_height",
    },
}


def get_variable_attrs(name: str) -> dict:
    """Return CF-compliant attributes for a canonical variable."""
    if name not in CANONICAL_VARIABLES:
        raise ValueError(f"Unknown canonical variable '{name}'. Available: {list(CANONICAL_VARIABLES)}")
    v = CANONICAL_VARIABLES[name]
    return {
        "long_name":     v["description"],
        "units":         v["units"],
        "standard_name": v["standard_name"],
    }


def validate_variables(variables: list[str]) -> None:
    """Raise ValueError if any variable is not in the canonical vocabulary."""
    unknown = [v for v in variables if v not in CANONICAL_VARIABLES]
    if unknown:
        raise ValueError(
            f"Unknown variables: {unknown}. "
            f"Available: {list(CANONICAL_VARIABLES)}"
        )