# snowops/providers/open_meteo.py
import openmeteo_requests
import requests_cache
import pandas as pd
import xarray as xr
import numpy as np
from retry_requests import retry
from snowops.providers.base import BaseProvider
from snowops.domain import Domain


class OpenMeteoProvider(BaseProvider):

    name = "open_meteo"
    mode = "both"

    VARIABLES = {
        "temperature_2m":             "Air temperature at 2m (°C)",
        "precipitation":              "Total precipitation (mm)",
        "snowfall":                   "Snowfall (cm)",
        "snow_depth":                 "Snow depth (m)",
        "surface_pressure":           "Surface pressure (hPa)",
        "wind_speed_10m":             "Wind speed at 10m (km/h)",
        "wind_direction_10m":         "Wind direction at 10m (°)",
        "relative_humidity_2m":       "Relative humidity at 2m (%)",
        "shortwave_radiation":        "Shortwave solar radiation (W/m²)",
        "et0_fao_evapotranspiration": "ET0 FAO evapotranspiration (mm)",
    }

    FREQUENCIES = ["1h", "3h", "6h", "1d"]

    def available_variables(self) -> dict[str, str]:
        return self.VARIABLES

    def available_date_range(self) -> tuple[str, str]:
        return ("1940-01-01", "present")

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

        # Validate inputs
        for v in variables:
            if v not in self.VARIABLES:
                raise ValueError(f"Variable '{v}' not available. Choose from: {list(self.VARIABLES)}")
        if freq not in self.FREQUENCIES:
            raise ValueError(f"Frequency '{freq}' not available. Choose from: {self.FREQUENCIES}")

        # Build grid of points covering the bbox
        west, south, east, north = domain.bbox
        lats = np.arange(south, north + 0.25, 0.25).round(4)
        lons = np.arange(west,  east  + 0.25, 0.25).round(4)

        # Setup Open-Meteo client with cache and retry
        cache_session = requests_cache.CachedSession(".cache_openmeteo", expire_after=-1)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        client = openmeteo_requests.Client(session=retry_session)

        # Choose endpoint: reanalysis vs forecast
        today = pd.Timestamp.today().normalize()
        end_dt = pd.Timestamp(end)
        if end_dt < today - pd.Timedelta(days=7):
            url = "https://archive-api.open-meteo.com/v1/archive"
        else:
            url = "https://api.open-meteo.com/v1/forecast"

        # Download one point per grid cell
        rows = []
        for lat in lats:
            cols = []
            for lon in lons:
                params = {
                    "latitude":   lat,
                    "longitude":  lon,
                    "hourly":     variables,
                    "start_date": start,
                    "end_date":   end,
                    "timezone":   "UTC",
                }
                responses = client.weather_api(url, params=params)
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
            "source":      "Open-Meteo API",
            "provider":    self.name,
            "domain":      repr(domain),
            "Conventions": "CF-1.8",
        }

        return ds