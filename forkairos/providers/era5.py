# forkairos/providers/era5.py
import cdsapi
import xarray as xr
import numpy as np
from pathlib import Path
from forkairos.providers.base import BaseProvider
from forkairos.domain import Domain
from forkairos.vocabulary import CANONICAL_VARIABLES, get_variable_attrs


class ERA5Provider(BaseProvider):

    name = "era5"
    mode = "reanalysis"

    # Mapping canonical forkairos names → CDS API parameter names
    # None = derived variable, not downloaded directly
    NATIVE_NAMES = {
        "temperature_2m":       "2m_temperature",
        "dewpoint_2m":          "2m_dewpoint_temperature",
        "precipitation":        "total_precipitation",
        "snowfall":             "snowfall",
        "snow_depth":           "snow_depth",
        "wind_u_10m":           "10m_u_component_of_wind",
        "wind_v_10m":           "10m_v_component_of_wind",
        "wind_speed_10m":       None,  # derived from wind_u_10m and wind_v_10m
        "wind_direction_10m":   None,  # derived from wind_u_10m and wind_v_10m
        "surface_pressure":     "surface_pressure",
        "shortwave_radiation":  "surface_solar_radiation_downwards",
        "longwave_radiation":   "surface_thermal_radiation_downwards",
        "cloud_cover":          "total_cloud_cover",
    }

    # CDS short names → canonical forkairos names
    CDS_SHORT_NAMES = {
        "t2m":  "temperature_2m",
        "d2m":  "dewpoint_2m",
        "tp":   "precipitation",
        "sf":   "snowfall",
        "sd":   "snow_depth",
        "u10":  "wind_u_10m",
        "v10":  "wind_v_10m",
        "sp":   "surface_pressure",
        "ssrd": "shortwave_radiation",
        "strd": "longwave_radiation",
        "tcc":  "cloud_cover",
    }

    # Unit conversions: native ERA5 → canonical forkairos units
    UNIT_CONVERSIONS = {
        "precipitation":       1000.0,    # m → mm
        "snowfall":            1000.0,    # m w.e. → mm w.e.
        "surface_pressure":    0.01,      # Pa → hPa
        "shortwave_radiation": 1 / 3600,  # J/m² → W/m²
        "longwave_radiation":  1 / 3600,  # J/m² → W/m²
    }

    FREQUENCIES = ["1h"]

    DERIVED = {"wind_speed_10m", "wind_direction_10m"}

    def available_variables(self) -> dict[str, str]:
        return {k: CANONICAL_VARIABLES[k]["description"] for k in self.NATIVE_NAMES}

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

        # Validate all requested variables
        for v in variables:
            if v not in self.NATIVE_NAMES:
                raise ValueError(f"Variable '{v}' not available. Choose from: {list(self.NATIVE_NAMES)}")

        # Ensure u and v are downloaded when derived variables are requested
        variables = list(variables)
        if any(v in self.DERIVED for v in variables):
            if "wind_u_10m" not in variables:
                variables.append("wind_u_10m")
            if "wind_v_10m" not in variables:
                variables.append("wind_v_10m")

        # Separate variables to download from derived variables
        variables_to_download = [v for v in variables if v not in self.DERIVED]
        cds_vars = [self.NATIVE_NAMES[v] for v in variables_to_download]

        import pandas as pd
        dates  = pd.date_range(start, end, freq="D")
        years  = list(dict.fromkeys(str(d.year) for d in dates))
        months = list(dict.fromkeys(f"{d.month:02d}" for d in dates))
        days   = list(dict.fromkeys(f"{d.day:02d}" for d in dates))

        west, south, east, north = domain.bbox
        area = [north, west, south, east]

        cache_dir = Path(cache_dir)
        cache_dir.mkdir(exist_ok=True)
        output_file = cache_dir / f"era5_{'_'.join(variables_to_download)}_{start}_{end}.nc"

        if not output_file.exists():
            client = cdsapi.Client()
            partial_files = []

            for var_name, cds_var in zip(variables_to_download, cds_vars):
                var_zip = cache_dir / f"era5_{var_name}_{start}_{end}.zip"
                var_nc  = cache_dir / f"era5_{var_name}_{start}_{end}.nc"
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
                            "data_format":  "netcdf",
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
                        var_zip.rename(var_nc)
                else:
                    print(f"[era5] Using cached file: {var_nc}")

            datasets = [xr.open_dataset(f) for f in partial_files]
            merged = xr.merge(datasets, compat="override")
            merged.to_netcdf(output_file)
            for ds_tmp in datasets:
                ds_tmp.close()
        else:
            print(f"[era5] Using cached file: {output_file}")

        ds = xr.open_dataset(output_file)

        # Rename CDS short names → canonical forkairos names
        rename_dict = {var: self.CDS_SHORT_NAMES[var]
                       for var in ds.data_vars if var in self.CDS_SHORT_NAMES}
        ds = ds.rename(rename_dict)

        # Apply unit conversions
        for v in list(ds.data_vars):
            if v in self.UNIT_CONVERSIONS:
                ds[v] = ds[v] * self.UNIT_CONVERSIONS[v]

        # Rename coordinates
        coord_map = {}
        if "valid_time" in ds.coords:
            coord_map["valid_time"] = "time"
        if "latitude" in ds.coords:
            coord_map["latitude"] = "lat"
        if "longitude" in ds.coords:
            coord_map["longitude"] = "lon"
        if coord_map:
            ds = ds.rename(coord_map)

        for c in ["expver", "number"]:
            if c in ds.coords:
                ds = ds.drop_vars(c)

        # Derive wind_speed_10m and wind_direction_10m from u and v components
        if "wind_u_10m" in ds.data_vars and "wind_v_10m" in ds.data_vars:
            ds["wind_speed_10m"] = np.sqrt(ds["wind_u_10m"]**2 + ds["wind_v_10m"]**2)
            ds["wind_direction_10m"] = (
                270 - np.degrees(np.arctan2(ds["wind_v_10m"], ds["wind_u_10m"]))
            ) % 360

        # Apply CF-compliant attributes from canonical vocabulary
        for v in ds.data_vars:
            if v in CANONICAL_VARIABLES:
                ds[v].attrs = get_variable_attrs(v)

        ds["lat"].attrs  = {"units": "degrees_north", "standard_name": "latitude"}
        ds["lon"].attrs  = {"units": "degrees_east",  "standard_name": "longitude"}
        ds["time"].attrs = {"standard_name": "time"}
        ds.attrs = {
            "source":      "ERA5 reanalysis (Copernicus CDS)",
            "provider":    self.name,
            "domain":      repr(domain),
            "Conventions": "CF-1.8",
        }

        return ds