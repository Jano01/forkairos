# tests/conftest.py
import pytest
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
from shapely.geometry import box
from pathlib import Path
from forkairos.domain import Domain


@pytest.fixture
def synthetic_shapefile(tmp_path):
    """Cuenca rectangular sintética en los Andes centrales."""
    geom = box(-70.5, -33.8, -70.0, -33.3)
    gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
    path = tmp_path / "test_basin.shp"
    gdf.to_file(path)
    return path


@pytest.fixture
def synthetic_domain(synthetic_shapefile):
    """Domain construido desde cuenca sintética."""
    return Domain(synthetic_shapefile, buffer_km=5.0)


@pytest.fixture
def mock_dataset():
    """Dataset NWP sintético CF-compliant con 3 días de datos."""
    time = pd.date_range("2024-06-01", periods=72, freq="1h")
    lat  = np.array([-33.8, -33.55, -33.3])
    lon  = np.array([-70.5, -70.25, -70.0])

    rng = np.random.default_rng(42)
    return xr.Dataset(
        {
            "temperature_2m": (["lat", "lon", "time"],
                               rng.normal(275, 10, (3, 3, 72)).astype("float32")),
            "precipitation":  (["lat", "lon", "time"],
                               rng.exponential(1, (3, 3, 72)).astype("float32")),
        },
        coords={"time": time, "lat": lat, "lon": lon},
        attrs={"Conventions": "CF-1.8", "provider": "mock"},
    )


@pytest.fixture
def mock_reference():
    """Dataset de referencia sintético para bias correction."""
    time = pd.date_range("2000-01-01", periods=365 * 10, freq="1D")
    lat  = np.array([-33.8, -33.55, -33.3])
    lon  = np.array([-70.5, -70.25, -70.0])

    rng = np.random.default_rng(99)
    return xr.Dataset(
        {
            "temperature_2m": (["lat", "lon", "time"],
                               rng.normal(270, 8, (3, 3, len(time))).astype("float32")),
            "precipitation":  (["lat", "lon", "time"],
                               rng.exponential(0.8, (3, 3, len(time))).astype("float32")),
        },
        coords={"time": time, "lat": lat, "lon": lon},
        attrs={"Conventions": "CF-1.8", "provider": "mock_reference"},
    )