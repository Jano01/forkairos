# forkairos/pipeline.py
import xarray as xr
from pathlib import Path
from forkairos.domain import Domain
from forkairos.providers.base import BaseProvider
from forkairos.providers.open_meteo import OpenMeteoProvider
from forkairos.providers.era5 import ERA5Provider
from forkairos.providers.gfs import GFSProvider
from forkairos.providers.ecmwf_open import ECMWFOpenProvider

PROVIDERS = {
    "open_meteo": OpenMeteoProvider,
    "era5":       ERA5Provider,
    "gfs":        GFSProvider,
    "ecmwf_open": ECMWFOpenProvider,
}

def get_provider(name: str) -> BaseProvider:
    """
    Returns an instance of the requested provider.

    Parameters
    ----------
    name : provider name. Available: "open_meteo"
    """
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider '{name}'. Available: {list(PROVIDERS)}")
    return PROVIDERS[name]()


def run(
    shapefile: str | Path,
    provider_name: str,
    variables: list[str],
    start: str,
    end: str,
    freq: str = "1h",
    buffer_km: float = 10.0,
    output_path: str | Path = "output.nc",
) -> xr.Dataset:
    """
    Full pipeline: shapefile → download → NetCDF.

    Parameters
    ----------
    shapefile     : path to basin shapefile
    provider_name : e.g. "open_meteo"
    variables     : list of variable names
    start         : start date "YYYY-MM-DD"
    end           : end date "YYYY-MM-DD"
    freq          : temporal resolution e.g. "1h", "6h", "1d"
    buffer_km     : buffer around basin in km
    output_path   : path for the output NetCDF file
    """
    print(f"[forkairos] Loading domain from {shapefile}")
    domain = Domain(shapefile, buffer_km=buffer_km)
    print(f"[forkairos] {domain}")

    print(f"[forkairos] Provider: {provider_name}")
    provider = get_provider(provider_name)

    print(f"[forkairos] Downloading {variables} | {start} → {end} | {freq}")
    ds = provider.download(domain, variables, start, end, freq)

    # Warn if spatial coverage is very limited
    n_lat = len(ds.lat) if "lat" in ds.dims else 1
    n_lon = len(ds.lon) if "lon" in ds.dims else 1
    if n_lat == 1 or n_lon == 1:
        import warnings
        warnings.warn(
            f"[forkairos] Only {n_lat}×{n_lon} grid point(s) available for this domain "
            f"with provider '{provider_name}'. Consider increasing buffer_km for better "
            f"spatial coverage. ERA5 requires ~25 km buffer per grid point.",
            UserWarning,
            stacklevel=2,
        )
    elif n_lat < 3 or n_lon < 3:
        import warnings
        warnings.warn(
            f"[forkairos] Limited spatial coverage: {n_lat}×{n_lon} grid points. "
            f"Consider increasing buffer_km for more spatial coverage.",
            UserWarning,
            stacklevel=2,
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(output_path)
    print(f"[forkairos] Saved → {output_path}")

    def _print_summary(ds: xr.Dataset, provider_name: str, output_path: Path) -> None:
        """Print a concise summary of the downloaded dataset."""
        import pandas as pd

        n_lat  = len(ds.lat)  if "lat"  in ds.dims else 1
        n_lon  = len(ds.lon)  if "lon"  in ds.dims else 1
        n_time = len(ds.time) if "time" in ds.dims else 1

        time_start = pd.Timestamp(ds.time.values[0]).strftime("%Y-%m-%d %H:%M")
        time_end   = pd.Timestamp(ds.time.values[-1]).strftime("%Y-%m-%d %H:%M")

        lat_min = float(ds.lat.min())
        lat_max = float(ds.lat.max())
        lon_min = float(ds.lon.min())
        lon_max = float(ds.lon.max())

        print("\n" + "="*55)
        print("  forkairos — download summary")
        print("="*55)
        print(f"  Provider   : {provider_name}")
        print(f"  Variables  : {list(ds.data_vars)}")
        print(f"  Grid       : {n_lat} lat × {n_lon} lon points")
        print(f"  Lat range  : {lat_min:.4f} → {lat_max:.4f} °N")
        print(f"  Lon range  : {lon_min:.4f} → {lon_max:.4f} °E")
        print(f"  Time steps : {n_time}")
        print(f"  Period     : {time_start} → {time_end} UTC")
        print(f"  Output     : {output_path}")
        print(f"  Size       : {ds.nbytes / 1024:.1f} kB")
        print("="*55 + "\n")

    _print_summary(ds, provider_name, output_path)
    return ds
