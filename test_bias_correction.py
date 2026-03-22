# test_bias_correction.py
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
print(ds_ref)

# Load ERA5 — use cached output
print("\nLoading ERA5...")
ds_nwp = xr.open_dataset(r"outputs\elyeso_era5_june2024.nc")
print(ds_nwp)

# Apply bias correction
print("\nApplying QDM bias correction...")
ds_corrected = bias_correct(
    ds_nwp,
    reference=ds_ref,
    variables=["temperature_2m", "precipitation"],
)
print(ds_corrected)

# Compare before and after — spatial mean time series
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Temperature
ds_nwp["temperature_2m"].mean(["lat", "lon"]).plot(
    ax=axes[0], label="ERA5 raw", color="steelblue", alpha=0.8
)
ds_corrected["temperature_2m"].mean(["lat", "lon"]).plot(
    ax=axes[0], label="ERA5 QDM corrected", color="tomato", alpha=0.8
)
axes[0].set_title("Temperature at 2m — spatial mean over El Yeso")
axes[0].set_ylabel("°C")
axes[0].legend()

# Precipitation
ds_nwp["precipitation"].mean(["lat", "lon"]).plot(
    ax=axes[1], label="ERA5 raw", color="steelblue", alpha=0.8
)
ds_corrected["precipitation"].mean(["lat", "lon"]).plot(
    ax=axes[1], label="ERA5 QDM corrected", color="tomato", alpha=0.8
)
axes[1].set_title("Precipitation — spatial mean over El Yeso")
axes[1].set_ylabel("mm")
axes[1].legend()

plt.tight_layout()
plt.savefig("outputs/bias_correction_check.png", dpi=150)
plt.show()
print("\nSaved to outputs/bias_correction_check.png")