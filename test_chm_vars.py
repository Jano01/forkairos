# test_chm_vars.py
from forkairos import run, get_provider

SHAPEFILE = r"C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp"

# Canonical variable set — same names work across all providers
VARIABLES_CANONICAL = [
    "temperature_2m",
    "precipitation",
    "snowfall",
    "snow_depth",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_u_10m",
    "wind_v_10m",
    "wind_direction_10m",
    "surface_pressure",
    "shortwave_radiation",
    "longwave_radiation",
    "cloud_cover",
    "geopotential_height_500hPa",
    "geopotential_height_700hPa",
    "geopotential_height_850hPa",
]

def test_provider(name, start, end, output):
    print(f"\n--- {name} ---")
    provider = get_provider(name)
    available = list(provider.available_variables().keys())
    vars_ok  = [v for v in VARIABLES_CANONICAL if v in available]
    missing  = [v for v in VARIABLES_CANONICAL if v not in available]
    print(f"Available:   {vars_ok}")
    print(f"Missing:     {missing}")
    print(f"Date range:  {provider.available_date_range()}")
    print(f"Frequencies: {provider.available_frequencies()}")
    ds = run(
        shapefile=SHAPEFILE,
        provider_name=name,
        variables=vars_ok,
        start=start,
        end=end,
        freq="1h",
        buffer_km=10.0,
        output_path=output,
    )
    print(ds)

# Reanalysis
test_provider("open_meteo", "2024-06-01", "2024-06-30", "outputs/elyeso_open_meteo_june2024.nc")
test_provider("era5",       "2024-06-01", "2024-06-30", "outputs/elyeso_era5_june2024.nc")

# Forecast
test_provider("gfs",        "2026-03-21", "2026-03-25", "outputs/elyeso_gfs_forecast.nc")
test_provider("ecmwf_open", "2026-03-21", "2026-03-25", "outputs/elyeso_ecmwf_forecast.nc")