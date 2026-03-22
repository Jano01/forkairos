# forkairos/datasets.py
"""
Reference datasets for bias correction.
Currently supports CR2MET for Chile (Boisier et al., 2018).
"""
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
from forkairos.domain import Domain


def load_cr2met(
    pr_path: str | Path,
    t2m_path: str | Path,
    domain: Domain,
    start: str,
    end: str,
) -> xr.Dataset:
    """
    Load CR2MET reference dataset clipped to a watershed domain.

    CR2MET is a high-resolution (0.05°) gridded climate dataset for Chile
    covering 1979-2019, based on station observations and reanalysis data
    (Boisier et al., 2018).

    Parameters
    ----------
    pr_path  : path to CR2MET precipitation NetCDF file
    t2m_path : path to CR2MET temperature NetCDF file
    domain   : Domain object with watershed bbox
    start    : start date "YYYY-MM-DD"
    end      : end date "YYYY-MM-DD"

    Returns
    -------
    xr.Dataset with variables 'precipitation' and 'temperature_2m',
    clipped to domain bbox and filtered to the requested period.
    CF-compliant time coordinate in monthly frequency.

    References
    ----------
    Boisier, J.P., Alvarez-Garretón, C., Cepeda, J., Osses, A., Vargas, F.,
    Rondanelli, R. (2018). CR2MET: A high-resolution precipitation and
    temperature dataset for hydroclimatic research in Chile.
    """
    west, south, east, north = domain.bbox

    # --- Precipitation ---
    pr_raw = xr.open_dataset(Path(pr_path), decode_times=False)

    # Build monthly time index from 'months since 1978-12-15'
    origin = pd.Timestamp("1978-12-15")
    time_pr = pd.date_range(
        start=origin + pd.DateOffset(months=int(pr_raw.time.values[0])),
        periods=len(pr_raw.time),
        freq="MS",  # Month Start
    )
    pr_raw = pr_raw.assign_coords(time=time_pr)

    # Clip to domain and period
    pr = pr_raw.sel(
        lat=slice(south, north),
        lon=slice(west, east),
        time=slice(start, end),
    )
    pr = pr.rename({"pr": "precipitation"})

    # --- Temperature ---
    t2m_raw = xr.open_dataset(Path(t2m_path), decode_times=False)

    time_t2m = pd.date_range(
        start=origin + pd.DateOffset(months=int(t2m_raw.time.values[0])),
        periods=len(t2m_raw.time),
        freq="MS",
    )
    t2m_raw = t2m_raw.assign_coords(time=time_t2m)

    t2m = t2m_raw.sel(
        lat=slice(south, north),
        lon=slice(west, east),
        time=slice(start, end),
    )

    # Rename temperature variable — CR2MET uses 't2m'
    t2m_var = [v for v in t2m_raw.data_vars][0]
    t2m = t2m.rename({t2m_var: "temperature_2m"})

    # Do not interpolate — clip each independently and merge with tolerance
    ds = xr.merge(
        [pr[["precipitation"]], t2m[["temperature_2m"]]],
        join="override",
    )

    # CF-compliant metadata
    ds["precipitation"].attrs = {
        "long_name":     "Monthly precipitation",
        "units":         "mm month-1",
        "standard_name": "precipitation_flux",
        "source":        "CR2MET v2.0",
    }
    ds["temperature_2m"].attrs = {
        "long_name":     "Mean air temperature at 2m",
        "units":         "degC",
        "standard_name": "air_temperature",
        "source":        "CR2MET v2.0",
    }
    ds["lat"].attrs = {"units": "degrees_north", "standard_name": "latitude"}
    ds["lon"].attrs = {"units": "degrees_east",  "standard_name": "longitude"}
    ds["time"].attrs = {"standard_name": "time"}
    ds.attrs = {
        "source":      "CR2MET v2.0 (Boisier et al., 2018)",
        "Conventions": "CF-1.8",
        "domain":      repr(domain),
    }

    return ds