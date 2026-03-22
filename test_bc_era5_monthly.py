# test_bc_era5_monthly.py
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from forkairos import Domain, run
from forkairos.datasets import load_cr2met
from forkairos.processing import bias_correct

SHAPEFILE = r"C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp"
PR_PATH   = r"G:\Mi unidad\RESEARCH\forkairos\dataset camels\CR2MET_pr_v2.0_mon_1979_2019_005deg.nc"
T2M_PATH  = r"G:\Mi unidad\RESEARCH\forkairos\dataset camels\CR2MET_t2m_v2.0_mon_1979_2019_005deg.nc"

domain = Domain(SHAPEFILE, buffer_km=10.0)

# Load CR2MET reference
print("Loading CR2MET reference...")
ds_ref = load_cr2met(
    pr_path=PR_PATH,
    t2m_path=T2M_PATH,
    domain=domain,
    start="1990-01-01",
    end="2019-12-31",
)

# Download ERA5 monthly for reference period
print("\nDownloading ERA5 monthly 1990-2019...")
ds_era5 = run(
    shapefile=SHAPEFILE,
    provider_name="open_meteo",
    variables=["temperature_2m", "precipitation"],
    start="1990-01-01",
    end="2019-12-31",
    freq="1d",
    buffer_km=10.0,
    output_path="outputs/elyeso_open_meteo_1990_2019_daily.nc",
)

# Resample ERA5 daily → monthly
print("\nResampling to monthly...")
ds_monthly = xr.Dataset({
    "temperature_2m": ds_era5["temperature_2m"].resample(time="MS").mean(),
    "precipitation":  ds_era5["precipitation"].resample(time="MS").sum(),
})
print(ds_monthly)

# Apply bias correction
print("\nApplying QDM bias correction...")
ds_corrected = bias_correct(
    ds_monthly,
    reference=ds_ref,
    variables=["temperature_2m", "precipitation"],
)

# Plot comparison
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

ds_monthly["temperature_2m"].mean(["lat","lon"]).plot(
    ax=axes[0], label="Open-Meteo raw", color="steelblue", alpha=0.7)
ds_corrected["temperature_2m"].mean(["lat","lon"]).plot(
    ax=axes[0], label="QDM corrected", color="tomato", alpha=0.7)
ds_ref["temperature_2m"].mean(["lat","lon"]).plot(
    ax=axes[0], label="CR2MET reference", color="green", alpha=0.7)
axes[0].set_title("Temperature at 2m — spatial mean over El Yeso")
axes[0].set_ylabel("°C")
axes[0].legend()

ds_monthly["precipitation"].mean(["lat","lon"]).plot(
    ax=axes[1], label="Open-Meteo raw", color="steelblue", alpha=0.7)
ds_corrected["precipitation"].mean(["lat","lon"]).plot(
    ax=axes[1], label="QDM corrected", color="tomato", alpha=0.7)
ds_ref["precipitation"].mean(["lat","lon"]).plot(
    ax=axes[1], label="CR2MET reference", color="green", alpha=0.7)
axes[1].set_title("Precipitation — spatial mean over El Yeso")
axes[1].set_ylabel("mm")
axes[1].legend()

plt.tight_layout()
plt.savefig("outputs/bc_era5_monthly_check.png", dpi=150)
plt.show()
print("\nSaved to outputs/bc_era5_monthly_check.png")