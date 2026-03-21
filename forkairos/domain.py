# forkairos/domain.py
from pathlib import Path
import geopandas as gpd

class Domain:
    """
    Represents a watershed domain derived from a shapefile.
    Computes a bounding box with an optional buffer for data download.
    """

    def __init__(self, shapefile: str | Path, buffer_km: float = 10.0):
        """
        Parameters
        ----------
        shapefile : path to the basin shapefile (any CRS)
        buffer_km : buffer around the basin in kilometers
        """
        self.shapefile = Path(shapefile)
        self.buffer_km = buffer_km

        # Read and reproject to WGS84
        gdf = gpd.read_file(self.shapefile).to_crs("EPSG:4326")
        self.geometry = gdf.union_all()

        # Compute bbox with buffer
        gdf_proj = gdf.to_crs(gdf.estimate_utm_crs())
        gdf_buffered = gdf_proj.buffer(buffer_km * 1000)
        bbox_buffered = gdf_buffered.to_crs("EPSG:4326").total_bounds

        self.west  = round(float(bbox_buffered[0]), 4)
        self.south = round(float(bbox_buffered[1]), 4)
        self.east  = round(float(bbox_buffered[2]), 4)
        self.north = round(float(bbox_buffered[3]), 4)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """Returns (west, south, east, north) in WGS84."""
        return (self.west, self.south, self.east, self.north)

    def __repr__(self) -> str:
        return (
            f"Domain(shapefile={self.shapefile.name!r}, "
            f"buffer_km={self.buffer_km}, "
            f"bbox=({self.west}, {self.south}, {self.east}, {self.north}))"
        )
