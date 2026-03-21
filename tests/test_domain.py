# tests/test_domain.py
import pytest
from forkairos.domain import Domain


def test_domain_loads(synthetic_shapefile):
    """Domain loads from shapefile without error."""
    domain = Domain(synthetic_shapefile, buffer_km=5.0)
    assert domain is not None


def test_domain_bbox_order(synthetic_domain):
    """Bbox is in correct order: west < east, south < north."""
    west, south, east, north = synthetic_domain.bbox
    assert west < east
    assert south < north


def test_domain_bbox_wgs84(synthetic_domain):
    """Bbox coordinates are in valid WGS84 range."""
    west, south, east, north = synthetic_domain.bbox
    assert -180 <= west <= 180
    assert -180 <= east <= 180
    assert -90  <= south <= 90
    assert -90  <= north <= 90


def test_domain_buffer_expands_bbox(synthetic_shapefile):
    """Buffer increases bbox size."""
    domain_no_buffer   = Domain(synthetic_shapefile, buffer_km=0.0)
    domain_with_buffer = Domain(synthetic_shapefile, buffer_km=10.0)

    w0, s0, e0, n0 = domain_no_buffer.bbox
    w1, s1, e1, n1 = domain_with_buffer.bbox

    assert w1 < w0
    assert s1 < s0
    assert e1 > e0
    assert n1 > n0


def test_domain_repr(synthetic_domain):
    """Domain repr contains shapefile name and bbox."""
    r = repr(synthetic_domain)
    assert "test_basin.shp" in r
    assert "bbox" in r