# forkairos

**Operational pipeline for meteorological forcing data in CF-compliant NetCDF**

forkairos downloads NWP forecast and reanalysis data from free providers for any
user-defined watershed, and delivers CF-compliant NetCDF files ready for
hydrological or land surface models. Variable names, units, and metadata are
standardized across all providers — the output format is always the same,
regardless of the data source.

## Installation
```bash
pip install forkairos
```

## Quick start
```python
from forkairos import run, get_provider

# See what a provider offers
provider = get_provider("open_meteo")
print(provider.available_variables())
print(provider.available_date_range())
print(provider.available_frequencies())

# Download data for a watershed
ds = run(
    shapefile="my_basin.shp",
    provider_name="open_meteo",
    variables=["temperature_2m", "precipitation", "snowfall",
               "wind_speed_10m", "shortwave_radiation", "longwave_radiation"],
    start="2024-06-01",
    end="2024-06-30",
    freq="1h",
    buffer_km=10.0,
    output_path="output.nc",
)
print(ds)
```

## Providers

| Provider | Mode | Resolution | Credentials |
|---|---|---|---|
| `open_meteo` | forecast + reanalysis | 0.25° / hourly | none |
| `era5` | reanalysis | 0.25° / hourly | CDS (free) |
| `gfs` | forecast | 0.25° / hourly | none |
| `ecmwf_open` | forecast | 0.25° / hourly | none |

## Canonical variable vocabulary

All providers use the same variable names in the output NetCDF:

| Variable | Description | Units |
|---|---|---|
| `temperature_2m` | Air temperature at 2m | °C |
| `dewpoint_2m` | Dewpoint temperature at 2m | °C |
| `precipitation` | Total precipitation | mm |
| `snowfall` | Snowfall amount | mm w.e. |
| `snow_depth` | Snow depth | m |
| `relative_humidity_2m` | Relative humidity at 2m | % |
| `wind_speed_10m` | Wind speed at 10m | m/s |
| `wind_u_10m` | U-component of wind at 10m | m/s |
| `wind_v_10m` | V-component of wind at 10m | m/s |
| `wind_direction_10m` | Wind direction at 10m | ° |
| `surface_pressure` | Surface pressure | hPa |
| `shortwave_radiation` | Downwelling shortwave radiation | W/m² |
| `longwave_radiation` | Downwelling longwave radiation | W/m² |
| `cloud_cover` | Total cloud cover | % |
| `geopotential_height_500hPa` | Geopotential height at 500 hPa | m |
| `geopotential_height_700hPa` | Geopotential height at 700 hPa | m |
| `geopotential_height_850hPa` | Geopotential height at 850 hPa | m |

Not all variables are available from every provider. Use `provider.available_variables()`
to check what is available before downloading.

## Optional post-processing

forkairos includes two optional post-processing steps that can be applied
independently after downloading. Both are modular — new methods can be added
as plugins in future versions.

### Spatial regridding

NWP data is typically available at coarse resolutions (0.25°, ~25 km). For
hydrological applications over complex terrain such as the Andes, finer
spatial resolution is often required.

forkairos implements **bilinear interpolation** to regrid data to a
user-specified target resolution. The target resolution should be chosen
based on the digital elevation model (DEM) used in the downstream model.
```python
from forkairos.processing import regrid, resolution_guide

# Print recommended resolutions based on common DEMs
resolution_guide()

# Regrid to 0.05° (~5 km)
ds_fine = regrid(ds, resolution=0.05)
```

> **Note:** Bilinear interpolation does not account for topographic effects
> on temperature lapse rates or orographic precipitation enhancement. For
> applications requiring physically consistent downscaling, the regridded
> output should be combined with a topographic correction scheme applied
> externally (e.g. Liston & Elder, 2006; Fiddes & Gruber, 2014).

### Bias correction

For deterministic modelling applications requiring bias correction, forkairos
provides an optional **MBCn (Multivariate Bias Correction)** module (Cannon, 2018).
MBCn corrects all variables simultaneously while preserving their inter-variable
dependence structure — preferable to univariate methods such as QDM which correct
each variable independently and may distort physical relationships.
```python
from forkairos.processing import bias_correct

ds_ref = xr.open_dataset("reference_dataset.nc")  # e.g. CR2MET, ERA5-Land
ds_corrected = bias_correct(ds, reference=ds_ref, method="mbcn")
```

> **Note for data assimilation workflows:** bias correction of NWP forcings is
> generally not recommended when forkairos feeds a DA pipeline. The assimilation
> algorithm handles forcing uncertainty implicitly — applying statistical bias
> correction beforehand may be redundant or counterproductive.

**References**

- Cannon, A. J. (2018). Multivariate quantile mapping bias correction:
  an N-dimensional probability density function transform for climate model
  simulations of multiple variables. *Climate Dynamics*, 50(1), 31–49.
  https://doi.org/10.1007/s00382-017-3580-6

## ERA5 credentials

ERA5 requires a free account at the
[Copernicus Climate Data Store](https://cds.climate.copernicus.eu).
After registering, create a file `~/.cdsapirc` with your credentials:
```
url: https://cds.climate.copernicus.eu/api
key: YOUR-API-KEY
```

## License

MIT — see [LICENSE](LICENSE)

## Citation

If you use forkairos in your research, please cite it using the metadata
available in the GitHub repository.
