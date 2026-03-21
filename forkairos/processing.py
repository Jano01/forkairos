# forkairos/processing.py
import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator


# Resoluciones sugeridas según DEM
DEM_RESOLUTION_GUIDE = {
    "SRTM 90m":    0.001,
    "SRTM 30m":    0.0003,
    "ALOS 12.5m":  0.0001,
    "TanDEM 12m":  0.0001,
    "COP-DEM 30m": 0.0003,
}


def resolution_guide() -> None:
    """Print suggested regridding resolutions based on common DEMs."""
    print("Suggested regridding resolutions by DEM:")
    for dem, res in DEM_RESOLUTION_GUIDE.items():
        print(f"  {dem:20s} → {res}° (~{res * 111:.0f} km)")
    print()
    print("Note: bilinear interpolation does not account for topographic")
    print("effects on temperature or precipitation. Use with caution")
    print("at resolutions finer than 0.01° (~1 km).")


def bias_correct(
    ds: xr.Dataset,
    reference: xr.Dataset,
    method: str = "qdm",
    variables: list[str] | None = None,
) -> xr.Dataset:
    """
    Apply bias correction to a Dataset using a reference Dataset.

    Parameters
    ----------
    ds        : Dataset to correct (e.g. from a NWP provider)
    reference : Observational reference Dataset (e.g. CR2MET, ERA5-Land)
    method    : Correction method — currently supported: "qdm"
    variables : Variables to correct. If None, corrects all common variables.

    Returns
    -------
    Bias-corrected Dataset with same structure as input.
    """
    if method == "qdm":
        return _qdm(ds, reference, variables)
    else:
        raise ValueError(f"Unknown method '{method}'. Available: ['qdm']")


def _qdm(
    ds: xr.Dataset,
    ref: xr.Dataset,
    variables: list[str] | None,
) -> xr.Dataset:
    """
    Quantile Delta Mapping (Cannon et al. 2015).

    Preserves the model's relative changes while correcting systematic bias.
    Applied independently per variable and per grid cell.
    """
    if variables is None:
        variables = [v for v in ds.data_vars if v in ref.data_vars]

    if not variables:
        raise ValueError("No common variables found between ds and reference.")

    ds_out = ds.copy(deep=True)
    n_quantiles = 100
    quantiles = np.linspace(0, 1, n_quantiles)

    for var in variables:
        if var not in ref.data_vars:
            print(f"[forkairos] Warning: '{var}' not in reference — skipping.")
            continue

        print(f"[forkairos] Bias correcting '{var}' with QDM...")

        mod = ds[var]
        obs = ref[var]

        # Interpolate reference to model grid if needed
        if not (obs.lat.values == mod.lat.values).all() or \
           not (obs.lon.values == mod.lon.values).all():
            obs = obs.interp(lat=mod.lat, lon=mod.lon, method="linear")

        # Apply QDM per grid cell
        corrected = mod.copy(deep=True)

        for i in range(len(mod.lat)):
            for j in range(len(mod.lon)):
                mod_cell = mod.isel(lat=i, lon=j).values
                obs_cell = obs.isel(lat=i, lon=j).values

                # Remove NaNs for quantile computation
                mod_clean = mod_cell[~np.isnan(mod_cell)]
                obs_clean = obs_cell[~np.isnan(obs_cell)]

                if len(mod_clean) == 0 or len(obs_clean) == 0:
                    continue

                # Compute quantile mapping
                mod_quantiles = np.quantile(mod_clean, quantiles)
                obs_quantiles = np.quantile(obs_clean, quantiles)

                # For each model value, find its quantile and apply delta
                for t in range(len(mod_cell)):
                    if np.isnan(mod_cell[t]):
                        continue
                    # Find quantile of current value in model distribution
                    q = np.interp(mod_cell[t], mod_quantiles, quantiles)
                    # Get observed value at same quantile
                    obs_val = np.interp(q, quantiles, obs_quantiles)
                    # Apply delta (QDM preserves relative change)
                    delta = mod_cell[t] - np.interp(q, quantiles, mod_quantiles)
                    corrected.values[i, j, t] = obs_val + delta

        ds_out[var] = corrected

    ds_out.attrs["bias_correction"] = f"QDM — reference: user-provided"
    return ds_out


def regrid(
    ds: xr.Dataset,
    resolution: float,
    method: str = "bilinear",
    variables: list[str] | None = None,
) -> xr.Dataset:
    """
    Regrid a Dataset to a finer resolution using interpolation.

    Parameters
    ----------
    ds         : Input Dataset with lat/lon dimensions
    resolution : Target resolution in degrees
    method     : Interpolation method — currently supported: "bilinear"
    variables  : Variables to regrid. If None, regrids all.

    Returns
    -------
    Regridded Dataset at target resolution.

    Notes
    -----
    Bilinear interpolation does not account for topographic effects.
    For guidance on appropriate resolutions, call forkairos.processing.resolution_guide().
    """
    if method != "bilinear":
        raise ValueError(f"Unknown method '{method}'. Available: ['bilinear']")

    if variables is None:
        variables = list(ds.data_vars)

    # Build target grid
    west  = float(ds.lon.min())
    east  = float(ds.lon.max())
    south = float(ds.lat.min())
    north = float(ds.lat.max())

    new_lats = np.arange(south, north + resolution, resolution).round(6)
    new_lons = np.arange(west,  east  + resolution, resolution).round(6)

    ds_out = ds.interp(
        lat=new_lats,
        lon=new_lons,
        method="linear",
        kwargs={"fill_value": "extrapolate"},
    )

    ds_out.attrs["regridding"] = f"bilinear interpolation → {resolution}°"
    return ds_out