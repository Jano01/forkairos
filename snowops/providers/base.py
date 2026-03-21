# snowops/providers/base.py
from abc import ABC, abstractmethod
from typing import Any
import xarray as xr
from snowops.domain import Domain


class BaseProvider(ABC):
    """
    Abstract base class for all NWP providers.
    Every provider must implement these four methods.
    """

    name: str          # e.g. "era5", "gfs"
    mode: str          # "forecast", "reanalysis", or "both"

    @abstractmethod
    def available_variables(self) -> dict[str, str]:
        """
        Returns a dictionary of available variables.

        Returns
        -------
        dict where key = variable name, value = description
        e.g. {"temperature_2m": "Air temperature at 2m (°C)"}
        """

    @abstractmethod
    def available_date_range(self) -> tuple[str, str]:
        """
        Returns the available date range for this provider.

        Returns
        -------
        tuple (start_date, end_date) as strings "YYYY-MM-DD"
        end_date can be "present" for operational providers
        """

    @abstractmethod
    def available_frequencies(self) -> list[str]:
        """
        Returns the temporal resolutions available.

        Returns
        -------
        list e.g. ["1h", "3h", "6h", "1d"]
        """

    @abstractmethod
    def download(
        self,
        domain: Domain,
        variables: list[str],
        start: str,
        end: str,
        freq: str,
    ) -> xr.Dataset:
        """
        Download data and return a CF-compliant xarray Dataset.

        Parameters
        ----------
        domain    : Domain object with bbox
        variables : list of variable names from available_variables()
        start     : start date "YYYY-MM-DD"
        end       : end date "YYYY-MM-DD"
        freq      : temporal resolution from available_frequencies()
        """