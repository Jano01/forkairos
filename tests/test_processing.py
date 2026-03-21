# tests/test_processing.py
import pytest
import numpy as np
import xarray as xr
from forkairos.processing import regrid, bias_correct, resolution_guide


def test_regrid_increases_resolution(mock_dataset):
    """Regrid produces finer grid than input."""
    ds_fine = regrid(mock_dataset, resolution=0.1)
    assert len(ds_fine.lat) > len(mock_dataset.lat)
    assert len(ds_fine.lon) > len(mock_dataset.lon)


def test_regrid_preserves_variables(mock_dataset):
    """Regrid keeps all variables."""
    ds_fine = regrid(mock_dataset, resolution=0.1)
    for var in mock_dataset.data_vars:
        assert var in ds_fine.data_vars


def test_regrid_preserves_time(mock_dataset):
    """Regrid does not alter time dimension."""
    ds_fine = regrid(mock_dataset, resolution=0.1)
    assert len(ds_fine.time) == len(mock_dataset.time)


def test_regrid_adds_metadata(mock_dataset):
    """Regrid adds regridding attribute to dataset."""
    ds_fine = regrid(mock_dataset, resolution=0.1)
    assert "regridding" in ds_fine.attrs


def test_regrid_invalid_method(mock_dataset):
    """Regrid raises ValueError for unknown method."""
    with pytest.raises(ValueError, match="Unknown method"):
        regrid(mock_dataset, resolution=0.1, method="kriging")


def test_bias_correct_output_shape(mock_dataset, mock_reference):
    """Bias correction preserves dataset shape."""
    ds_corrected = bias_correct(mock_dataset, mock_reference)
    for var in mock_dataset.data_vars:
        assert ds_corrected[var].shape == mock_dataset[var].shape


def test_bias_correct_adds_metadata(mock_dataset, mock_reference):
    """Bias correction adds attribute to dataset."""
    ds_corrected = bias_correct(mock_dataset, mock_reference)
    assert "bias_correction" in ds_corrected.attrs


def test_bias_correct_invalid_method(mock_dataset, mock_reference):
    """Bias correction raises ValueError for unknown method."""
    with pytest.raises(ValueError, match="Unknown method"):
        bias_correct(mock_dataset, mock_reference, method="delta")


def test_resolution_guide_runs(capsys):
    """resolution_guide prints without error."""
    resolution_guide()
    captured = capsys.readouterr()
    assert "SRTM" in captured.out