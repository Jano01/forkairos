# snowops/pipeline.py
import xarray as xr
from pathlib import Path
from snowops.domain import Domain
from snowops.providers.base import BaseProvider
from snowops.providers.open_meteo import OpenMeteoProvider


PROVIDERS = {
    "open_meteo": OpenMeteoProvider,
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
    print(f"[snowops] Loading domain from {shapefile}")
    domain = Domain(shapefile, buffer_km=buffer_km)
    print(f"[snowops] {domain}")

    print(f"[snowops] Provider: {provider_name}")
    provider = get_provider(provider_name)

    print(f"[snowops] Downloading {variables} | {start} → {end} | {freq}")
    ds = provider.download(domain, variables, start, end, freq)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(output_path)
    print(f"[snowops] Saved → {output_path}")

    return ds