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

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(output_path)
    print(f"[forkairos] Saved → {output_path}")

    return ds
