import numpy as np
import os
import xarray as xr
from .common import (__np_types, __top_level_sub_xds)


def __read_zarr(zarr_store: str) -> xr.Dataset:
    tmp_xds = xr.open_zarr(zarr_store)
    xds = __decode(tmp_xds, zarr_store)
    return xds


def __decode(xds: xr.Dataset, zarr_store:str) -> xr.Dataset:
    xds.attrs = __decode_dict(xds.attrs)
    sub_xdses = __decode_sub_xdses(zarr_store)
    for k, v in sub_xdses.items():
        xds.attrs[k] = v
    return xds


def __decode_dict(my_dict: dict, top_key: str='') -> dict:
    for k, v in my_dict.items():
        if isinstance(v, dict):
            if (
                '__type' in v and v['__type'] == 'numpy.ndarray'
                and '__value' in v and '__dtype' in v
            ):
                my_dict[k] = np.array(v['__value'], dtype=__np_types[v['__dtype']])
            else:
                z = os.sep.join([top_key, k]) if top_key else k
                my_dict[k]  = __decode_dict(v, z)
    return my_dict


def __decode_sub_xdses(zarr_store: str) -> dict:
    sub_xdses = {}
    for root, dirs, files in os.walk(zarr_store):
        print(f'dirs {dirs}')
        for d in dirs:
            if d.startswith(__top_level_sub_xds):
                xds = __read_zarr(os.sep.join([root, d]))
                k = d[len(__top_level_sub_xds) + 2:]
                sub_xdses[k] = xds
    return sub_xdses

