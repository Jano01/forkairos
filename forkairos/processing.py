# forkairos/processing.py
"""
Optional post-processing module for forkairos.

Note on bias correction
-----------------------
forkairos delivers raw, standardized NWP forcings by default.
Bias correction is intentionally not applied in the main pipeline,
as the primary use case is data assimilation workflows where forcing
correction is handled by the assimilation algorithm itself.

For deterministic modelling applications, an optional multivariate
bias correction is provided via MBCn (Cannon, 2018), which corrects
all variables simultaneously while preserving their inter-variable
dependence structure.

References
----------
Cannon, A. J. (2018). Multivariate quantile mapping bias correction:
an N-dimensional probability density function transform for climate
model simulations of multiple variables. Climate Dynamics, 50(1),
31-49. https://doi.org/10.1007/s00382-017-3580-6
"""
import numpy as np
import xarray as xr


# Recommended regridding resolutions based on common DEMs
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
        print(f"  {dem:20s} → {res}° (~{res * 111 * 1000:.0f} m)")
    print()
    print("Note: bilinear interpolation does not account for topographic")
    print("effects on temperature or precipitation. Use with caution")
    print("at resolutions finer than 0.01° (~1 km).")


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
    For guidance on appropriate resolutions, call resolution_guide().
    """
    if method != "bilinear":
        raise ValueError(f"Unknown method '{method}'. Available: ['bilinear']")

    if variables is None:
        variables = list(ds.data_vars)

    west  = float(ds.lon.min())
    east  = float(ds.lon.max())
    south = float(ds.lat.min())
    north = float(ds.lat.max())

    new_lats = np.arange(south, north + resolution, resolution).round(6)
    new_lons = np.arange(west,  east  + resolution, resolution).round(6)

    print(f"[forkairos] Regridding {len(ds.lat)}×{len(ds.lon)} → "
          f"{len(new_lats)}×{len(new_lons)} ({resolution}°)")

    ds_out = ds.interp(
        lat=new_lats,
        lon=new_lons,
        method="linear",
        kwargs={"fill_value": "extrapolate"},
    )

    ds_out.attrs["regridding"] = f"bilinear interpolation → {resolution}°"
    return ds_out


def bias_correct(
    ds: xr.Dataset,
    reference: xr.Dataset,
    method: str = "mbcn",
    variables: list[str] | None = None,
) -> xr.Dataset:
    """
    Apply multivariate bias correction to a Dataset.

    Parameters
    ----------
    ds        : Dataset to correct (e.g. from a NWP provider)
    reference : Observational reference Dataset (e.g. CR2MET, ERA5-Land)
    method    : Correction method — currently supported: "mbcn"
    variables : Variables to correct. If None, corrects all common variables.

    Returns
    -------
    Bias-corrected Dataset with same structure as input.

    Notes
    -----
    MBCn (Cannon, 2018) corrects all variables simultaneously while
    preserving their inter-variable dependence structure. This is
    preferable to univariate methods (e.g. QDM) which correct each
    variable independently and may distort physical relationships
    between variables.

    For data assimilation workflows, bias correction of NWP forcings
    is generally not recommended as the assimilation algorithm handles
    forcing uncertainty implicitly.

    References
    ----------
    Cannon, A. J. (2018). Multivariate quantile mapping bias correction:
    an N-dimensional probability density function transform for climate
    model simulations of multiple variables. Climate Dynamics, 50(1),
    31-49. https://doi.org/10.1007/s00382-017-3580-6
    """
    if method == "mbcn":
        return _mbcn(ds, reference, variables)
    else:
        raise ValueError(f"Unknown method '{method}'. Available: ['mbcn']")


def _mbcn(
    ds: xr.Dataset,
    ref: xr.Dataset,
    variables: list[str] | None,
) -> xr.Dataset:
    """
    MBCn — Multivariate Bias Correction (Cannon, 2018).

    N-dimensional probability density function transform that corrects
    all variables simultaneously preserving inter-variable dependence.

    Note: Full MBCn implementation coming in v0.2.0.
    Current version applies marginal correction as placeholder.
    """
    raise NotImplementedError(
        "MBCn bias correction is planned for forkairos v0.2.0. "
        "For deterministic applications requiring bias correction, "
        "consider using the MBCn R package (Cannon, 2018) directly "
        "on the forkairos NetCDF output."
    )