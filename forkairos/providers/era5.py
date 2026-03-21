# forkairos/providers/era5.py
import cdsapi
import xarray as xr
import numpy as np
from pathlib import Path
from forkairos.providers.base import BaseProvider
from forkairos.domain import Domain


class ERA5Provider(BaseProvider):

    name = "era5"
    mode = "reanalysis"

    VARIABLES = {
        "temperature_2m":        "Air temperature at 2m (°C)",
        "precipitation":         "Total precipitation (m)",
        "snowfall":              "Snowfall (m of water equivalent)",
        "snow_depth":            "Snow depth (m of water equivalent)",
        "surface_pressure":      "Surface pressure (Pa)",
        "wind_speed_10m_u":      "U-component of wind at 10m (m/s)",
        "wind_speed_10m_v":      "V-component of wind at 10m (m/s)",
        "relative_humidity":     "Relative humidity (%)",
        "shortwave_radiation":   "Surface solar radiation downwards (J/m²)",
        "longwave_radiation":    "Surface thermal radiation downwards (J/m²)",
        "snow_cover":            "Fraction of snow cover (0-1)",
    }

    # Mapping forkairos variable names → CDS parameter names
    CDS_NAMES = {
        "temperature_2m":      "2m_temperature",
        "precipitation":       "total_precipitation",
        "snowfall":            "snowfall",
        "snow_depth":          "snow_depth",
        "surface_pressure":    "surface_pressure",
        "wind_speed_10m_u":    "10m_u_component_of_wind",
        "wind_speed_10m_v":    "10m_v_component_of_wind",
        "relative_humidity":   "relative_humidity",
        "shortwave_radiation": "surface_solar_radiation_downwards",
        "longwave_radiation":  "surface_thermal_radiation_downwards",
        "snow_cover":          "fraction_of_snow_cover",
    }

    # Mapping CDS short names (what ERA5 actually returns) → forkairos names
    CDS_SHORT_NAMES = {
        "t2m":   "temperature_2m",
        "tp":    "precipitation",
        "sf":    "snowfall",
        "sd":    "snow_depth",
        "sp":    "surface_pressure",
        "u10":   "wind_speed_10m_u",
        "v10":   "wind_speed_10m_v",
        "r":     "relative_humidity",
        "ssrd":  "shortwave_radiation",
        "strd":  "longwave_radiation",
        "fscov": "snow_cover",
    }

    FREQUENCIES = ["1h"]

    def available_variables(self) -> dict[str, str]:
        return self.VARIABLES

    def available_date_range(self) -> tuple[str, str]:
        import pandas as pd
        end = (pd.Timestamp.today() - pd.DateOffset(months=3)).strftime("%Y-%m-%d")
        return ("1940-01-01", end)
    
    def available_frequencies(self) -> list[str]:
        return self.FREQUENCIES

    def download(
        self,
        domain: Domain,
        variables: list[str],
        start: str,
        end: str,
        freq: str = "1h",
        cache_dir: str | Path = ".cache_era5",
    ) -> xr.Dataset:

        # Validate inputs
        for v in variables:
            if v not in self.VARIABLES:
                raise ValueError(f"Variable '{v}' not available. Choose from: {list(self.VARIABLES)}")

        # Translate to CDS names
        cds_vars = [self.CDS_NAMES[v] for v in variables]

        # Build date range
        import pandas as pd
        dates = pd.date_range(start, end, freq="D")
        years  = list(dict.fromkeys(str(d.year) for d in dates))
        months = list(dict.fromkeys(f"{d.month:02d}" for d in dates))
        days   = list(dict.fromkeys(f"{d.day:02d}" for d in dates))

        # Bbox: CDS expects [north, west, south, east]
        west, south, east, north = domain.bbox
        area = [north, west, south, east]

        # Download
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(exist_ok=True)
        zip_file   = cache_dir / f"era5_{'_'.join(variables)}_{start}_{end}.zip"
        output_file = cache_dir / f"era5_{'_'.join(variables)}_{start}_{end}.nc"

        if not output_file.exists():
            client = cdsapi.Client()
            partial_files = []

            for var_name, cds_var in zip(variables, cds_vars):
                var_zip  = cache_dir / f"era5_{var_name}_{start}_{end}.zip"
                var_nc   = cache_dir / f"era5_{var_name}_{start}_{end}.nc"
                partial_files.append(var_nc)

                if not var_nc.exists():
                    client.retrieve(
                        "reanalysis-era5-single-levels",
                        {
                            "product_type": "reanalysis",
                            "variable":     [cds_var],
                            "year":         years,
                            "month":        months,
                            "day":          days,
                            "time":         [f"{h:02d}:00" for h in range(24)],
                            "area":         area,
                            "format":       "netcdf",
                        },
                        str(var_zip),
                    )
                    import zipfile
                    if zipfile.is_zipfile(var_zip):
                        with zipfile.ZipFile(var_zip, "r") as z:
                            names = z.namelist()
                            nc_name = next(n for n in names if n.endswith(".nc"))
                            z.extract(nc_name, cache_dir)
                            (cache_dir / nc_name).rename(var_nc)
                        var_zip.unlink()
                    else:
                        # Already a NetCDF
                        var_zip.rename(var_nc)
                else:
                    print(f"[era5] Using cached file: {var_nc}")

            # Merge all variables into one dataset
            datasets = [xr.open_dataset(f) for f in partial_files]
            merged = xr.merge(datasets, compat="override")
            merged.to_netcdf(output_file)
            for ds_tmp in datasets:
                ds_tmp.close()

        else:
            print(f"[era5] Using cached file: {output_file}")

        # Load and rename short CDS names → forkairos names
        ds = xr.open_dataset(output_file)
        rename_dict = {var: self.CDS_SHORT_NAMES[var] for var in ds.data_vars if var in self.CDS_SHORT_NAMES}
        ds = ds.rename(rename_dict)

        # Rename coordinates to match forkairos convention
        coord_map = {}
        if "valid_time" in ds.coords:
            coord_map["valid_time"] = "time"
        if "latitude" in ds.coords:
            coord_map["latitude"] = "lat"
        if "longitude" in ds.coords:
            coord_map["longitude"] = "lon"
        if coord_map:
            ds = ds.rename(coord_map)

        # Drop auxiliary coords not needed
        for c in ["expver", "number"]:
            if c in ds.coords:
                ds = ds.drop_vars(c)

        ds.attrs = {
            "source":      "ERA5 reanalysis (Copernicus CDS)",
            "provider":    self.name,
            "domain":      repr(domain),
            "Conventions": "CF-1.8",
        }

        return ds
