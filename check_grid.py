import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
from forkairos import Domain
from forkairos.datasets import load_cr2met

domain = Domain(r'C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp', buffer_km=10.0)

ds_ref = load_cr2met(
    pr_path=r'G:\Mi unidad\RESEARCH\forkairos\dataset camels\CR2MET_pr_v2.0_mon_1979_2019_005deg.nc',
    t2m_path=r'G:\Mi unidad\RESEARCH\forkairos\dataset camels\CR2MET_t2m_v2.0_mon_1979_2019_005deg.nc',
    domain=domain,
    start='1990-01-01',
    end='2019-12-31',
)

# Plot mean precipitation over the domain
basin = gpd.read_file(r'C:\Users\wings\Desktop\ECMWF_COURARD\SIG\ElYeso_Glaciares_V2.shp').to_crs('EPSG:4326')

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Precipitation
ds_ref['precipitation'].mean('time').plot(ax=axes[0], cmap='Blues')
basin.boundary.plot(ax=axes[0], color='red', linewidth=1.5)
axes[0].set_title('CR2MET — Mean monthly precipitation (mm)')

# Temperature
ds_ref['temperature_2m'].mean('time').plot(ax=axes[1], cmap='RdBu_r')
basin.boundary.plot(ax=axes[1], color='black', linewidth=1.5)
axes[1].set_title('CR2MET — Mean temperature at 2m (°C)')

plt.tight_layout()
plt.savefig('outputs/cr2met_grid_check.png', dpi=150)
plt.show()
print('Saved to outputs/cr2met_grid_check.png')
