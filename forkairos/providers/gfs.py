# forkairos/providers/gfs.py
import requests
import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path
from forkairos.providers.base import BaseProvider
from forkairos.domain import Domain


class GFSProvider(BaseProvider):

    name = "gfs"
    mode = "forecast"

    VARIABLES = {
        "temperature_2m":       "Air temperature at 2m (°C)",
        "precipitation":        "Total precipitation (kg/m²)",
        "snowfall":             "Snowfall (kg/m²)",
        "surface_pressure":     "Surface pressure (Pa)",
        "wind_speed_10m_u":     "U-component of wind at 10m (m/s)",
        "wind_speed_10m_v":     "V-component of wind at 10m (m/s)",
        "relative_humidity":    "Relative humidity at 2m (%)",
        "shortwave_radiation":  "Downward shortwave radiation (W/m²)",
        "snow_depth":           "Snow depth (m)",
    }

    # Mapping forkairos names → Open-Meteo GFS variable names
    OPENMETEO_NAMES = {
        "temperature_2m":      "temperature_2m",
        "precipitation":       "precipitation",
        "snowfall":            "snowfall",
        "surface_pressure":    "surface_pressure",
        "wind_speed_10m_u":    "wind_u_component_10m",
        "wind_speed_10m_v":    "wind_v_component_10m",
        "relative_humidity":   "relative_humidity_2m",
        "shortwave_radiation": "shortwave_radiation",
        "snow_depth":          "snow_depth",
    }

    FREQUENCIES = ["1h", "3h", "6h", "1d"]

    # GFS via Open-Meteo forecast endpoint
    FORECAST_URL  = "https://api.open-meteo.com/v1/gfs"

    def available_variables(self) -> dict[str, str]:
        return self.VARIABLES

    def available_date_range(self) -> tuple[str, str]:
        start = pd.Timestamp.today().strftime("%Y-%m-%d")
        end   = (pd.Timestamp.today() + pd.Timedelta(days=15)).strftime("%Y-%m-%d")
        return (start, "present+16days")

    def available_frequencies(self) -> list[str]:
        return self.FREQUENCIES

    def download(
        self,
        domain: Domain,
        variables: list[str],
        start: str,
        end: str,
        freq: str = "1h",
    ) -> xr.Dataset:

        import openmeteo_requests
        import requests_cache
        from retry_requests import retry

        # Validate inputs
        for v in variables:
            if v not in self.VARIABLES:
                raise ValueError(f"Variable '{v}' not available. Choose from: {list(self.VARIABLES)}")
        if freq not in self.FREQUENCIES:
            raise ValueError(f"Frequency '{freq}' not available. Choose from: {self.FREQUENCIES}")

        # Translate variable names
        om_vars = [self.OPENMETEO_NAMES[v] for v in variables]

        # Build grid of points covering the bbox
        west, south, east, north = domain.bbox
        lats = np.arange(south, north + 0.25, 0.25).round(4)
        lons = np.arange(west,  east  + 0.25, 0.25).round(4)

        # Setup client
        cache_session = requests_cache.CachedSession(".cache_gfs", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        client = openmeteo_requests.Client(session=retry_session)

        # Download grid
        rows = []
        for lat in lats:
            cols = []
            for lon in lons:
                params = {
                    "latitude":   lat,
                    "longitude":  lon,
                    "hourly":     om_vars,
                    "start_date": start,
                    "end_date":   end,
                    "timezone":   "UTC",
                }
                responses = client.weather_api(self.FORECAST_URL, params=params)
                r = responses[0]
                hourly = r.Hourly()

                times = pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left",
                ).tz_localize(None)

                data_vars = {}
                for i, v in enumerate(variables):
                    data_vars[v] = (["time"], hourly.Variables(i).ValuesAsNumpy())

                ds_point = xr.Dataset(
                    data_vars,
                    coords={"time": times},
                ).expand_dims(lat=[lat], lon=[lon])

                cols.append(ds_point)
            rows.append(xr.concat(cols, dim="lon"))

        ds = xr.concat(rows, dim="lat")

        # CF-compliant metadata
        ds["lat"].attrs  = {"units": "degrees_north", "standard_name": "latitude"}
        ds["lon"].attrs  = {"units": "degrees_east",  "standard_name": "longitude"}
        ds["time"].attrs = {"standard_name": "time"}
        ds.attrs = {
            "source":      "GFS forecast via Open-Meteo API",
            "provider":    self.name,
            "domain":      repr(domain),
            "Conventions": "CF-1.8",
        }

        return ds
