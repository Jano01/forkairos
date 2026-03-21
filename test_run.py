# test_run.py
from snowops import run, get_provider

# Ver qué variables están disponibles
provider = get_provider("open_meteo")
print("Variables disponibles:")
for k, v in provider.available_variables().items():
    print(f"  {k}: {v}")
print()
print("Rango de fechas:", provider.available_date_range())
print("Frecuencias:", provider.available_frequencies())
print()

# Descarga de prueba — 3 días
ds = run(
    shapefile=r"C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp",
    provider_name="open_meteo",
    variables=["temperature_2m", "precipitation", "snowfall"],
    start="2024-06-01",
    end="2024-06-03",
    freq="1h",
    buffer_km=5.0,
    output_path="outputs/test_elyeso.nc",
)

print(ds)

# Test ERA5
print("\n--- ERA5 ---")
provider_era5 = get_provider("era5")
print("Variables:", list(provider_era5.available_variables().keys()))
print("Rango:", provider_era5.available_date_range())

ds_era5 = run(
    shapefile=r"C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp",
    provider_name="era5",
    variables=["temperature_2m", "precipitation"],
    start="2024-06-01",
    end="2024-06-03",
    freq="1h",
    buffer_km=5.0,
    output_path="outputs/test_elyeso_era5.nc",
)
print(ds_era5)

# Test GFS
print("\n--- GFS ---")
provider_gfs = get_provider("gfs")
print("Variables:", list(provider_gfs.available_variables().keys()))
print("Rango:", provider_gfs.available_date_range())

ds_gfs = run(
    shapefile=r"C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp",
    provider_name="gfs",
    variables=["temperature_2m", "precipitation", "snowfall"],
    start="2026-03-21",
    end="2026-03-23",
    freq="1h",
    buffer_km=5.0,
    output_path="outputs/test_elyeso_gfs.nc",
)
print(ds_gfs)

# Test ECMWF Open Data
print("\n--- ECMWF Open Data ---")
provider_ecmwf = get_provider("ecmwf_open")
print("Variables:", list(provider_ecmwf.available_variables().keys()))
print("Rango:", provider_ecmwf.available_date_range())

ds_ecmwf = run(
    shapefile=r"C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp",
    provider_name="ecmwf_open",
    variables=["temperature_2m", "precipitation"],
    start="2026-03-21",
    end="2026-03-23",
    freq="6h",
    buffer_km=5.0,
    output_path="outputs/test_elyeso_ecmwf.nc",
)
print(ds_ecmwf)