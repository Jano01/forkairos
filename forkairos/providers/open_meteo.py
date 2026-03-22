# forkairos/providers/open_meteo.py
import openmeteo_requests
import requests_cache
import pandas as pd
import xarray as xr
import numpy as np
from retry_requests import retry
from forkairos.providers.base import BaseProvider
from forkairos.domain import Domain
from forkairos.vocabulary import CANONICAL_VARIABLES, get_variable_attrs


class OpenMeteoProvider(BaseProvider):

    name = "open_meteo"
    mode = "both"

    # Mapping canonical forkairos names → Open-Meteo API names
    NATIVE_NAMES = {
        "temperature_2m":            "temperature_2m",
        "dewpoint_2m":               "dew_point_2m",
        "precipitation":             "precipitation",
        "snowfall":                  "snowfall",
        "snow_depth":                "snow_depth",
        "relative_humidity_2m":      "relative_humidity_2m",
        "wind_speed_10m":            "wind_speed_10m",
        "wind_u_10m":                "wind_u_component_10m",
        "wind_v_10m":                "wind_v_component_10m",
        "wind_direction_10m":        "wind_direction_10m",
        "surface_pressure":          "surface_pressure",
        "shortwave_radiation":       "shortwave_radiation",
        "longwave_radiation":        "terrestrial_radiation",
        "cloud_cover":               "cloud_cover",
        "geopotential_height_500hPa": "geopotential_height_500hPa",
        "geopotential_height_700hPa": "geopotential_height_700hPa",
        "geopotential_height_850hPa": "geopotential_height_850hPa",
    }

    # Unit conversion factors: native → canonical
    # (multiply native value by factor to get canonical units)
    UNIT_CONVERSIONS = {
        "wind_speed_10m": 1 / 3.6,   # km/h → m/s
        "wind_u_10m":     1 / 3.6,   # km/h → m/s
        "wind_v_10m":     1 / 3.6,   # km/h → m/s
        "surface_pressure": 1.0,     # already hPa
    }

    FREQUENCIES = ["1h", "3h", "6h", "1d"]

    def available_variables(self) -> dict[str, str]:
        return {k: CANONICAL_VARIABLES[k]["description"] for k in self.NATIVE_NAMES}

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

        for v in variables:
            if v not in self.NATIVE_NAMES:
                raise ValueError(f"Variable '{v}' not available. Choose from: {list(self.NATIVE_NAMES)}")
        if freq not in self.FREQUENCIES:
            raise ValueError(f"Frequency '{freq}' not available. Choose from: {self.FREQUENCIES}")

        # Translate to native API names
        native_vars = [self.NATIVE_NAMES[v] for v in variables]

        west, south, east, north = domain.bbox
        lats = np.arange(south, north + 0.25, 0.25).round(4)
        lons = np.arange(west,  east  + 0.25, 0.25).round(4)

        cache_session = requests_cache.CachedSession(".cache_openmeteo", expire_after=-1)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        client = openmeteo_requests.Client(session=retry_session)

        today  = pd.Timestamp.today().normalize()
        end_dt = pd.Timestamp(end)
        if end_dt < today - pd.Timedelta(days=7):
            url = "https://archive-api.open-meteo.com/v1/archive"
        else:
            url = "https://api.open-meteo.com/v1/forecast"

        rows = []
        for lat in lats:
            cols = []
            for lon in lons:
                params = {
                    "latitude":   lat,
                    "longitude":  lon,
                    "hourly":     native_vars,
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
                    values = hourly.Variables(i).ValuesAsNumpy()
                    # Apply unit conversion if needed
                    if v in self.UNIT_CONVERSIONS:
                        values = values * self.UNIT_CONVERSIONS[v]
                    data_vars[v] = (["time"], values)

                ds_point = xr.Dataset(
                    data_vars,
                    coords={"time": times},
                ).expand_dims(lat=[lat], lon=[lon])

                cols.append(ds_point)
            rows.append(xr.concat(cols, dim="lon"))

        ds = xr.concat(rows, dim="lat")

        # Apply CF-compliant attributes from canonical vocabulary
        for v in variables:
            ds[v].attrs = get_variable_attrs(v)

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