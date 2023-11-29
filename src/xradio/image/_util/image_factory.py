from astropy.wcs import WCS
import numpy as np
import xarray as xr
from typing import Union
from .common import _c, _compute_world_sph_dims, _l_m_attr_notes
from ..._utils.common import _deg_to_rad


def _make_empty_sky_image(
    xds: xr.Dataset,
    phase_center: Union[list, np.ndarray],
    image_size: Union[list, np.ndarray],
    cell_size: Union[list, np.ndarray],
    chan_coords: Union[list, np.ndarray],
    pol_coords: Union[list, np.ndarray],
    time_coords: Union[list, np.ndarray],
    direction_reference: str,
    projection: str,
    spectral_reference: str,
    do_sky_coords: bool,
) -> xr.Dataset:
    if len(image_size) != 2:
        raise ValueError("image_size must have exactly two elements")
    if len(phase_center) != 2:
        raise ValueError("phase_center must have exactly two elements")
    if len(cell_size) != 2:
        raise ValueError("cell_size must have exactly two elements")
    if do_sky_coords:
        long, lat = _compute_world_sph_dims(
            projection=projection,
            shape=image_size,
            ctype=["RA", "Dec"],
            crpix=[image_size[0] // 2, image_size[1] // 2],
            crval=phase_center,
            cdelt=[-abs(cell_size[0]), abs(cell_size[1])],
            cunit=["rad", "rad"],
        )["value"]
    l_coords = [
        (i - image_size[0] // 2) * abs(cell_size[0]) for i in range(image_size[0])
    ]
    m_coords = [
        (i - image_size[1] // 2) * abs(cell_size[1]) for i in range(image_size[1])
    ]

    if not isinstance(chan_coords, list) and not isinstance(chan_coords, np.ndarray):
        chan_coords = [chan_coords]
    chan_coords = np.array(chan_coords, dtype=np.float64)
    restfreq = chan_coords[len(chan_coords) // 2]
    vel = (1 - chan_coords / restfreq) * _c
    if not isinstance(time_coords, list) and not isinstance(time_coords, np.ndarray):
        time_coords = [time_coords]
    time_coords = np.array(time_coords, dtype=np.float64)
    if do_sky_coords:
        coords = {
            "time": time_coords,
            "polarization": pol_coords,
            "frequency": chan_coords,
            "velocity": ("frequency", vel),
            "l": l_coords,
            "m": m_coords,
            "right_ascension": (("l", "m"), long),
            "declination": (("l", "m"), lat),
        }
    else:
        coords = {
            "time": time_coords,
            "polarization": pol_coords,
            "frequency": chan_coords,
            "velocity": ("frequency", vel),
            "l": l_coords,
            "m": m_coords,
        }
    xds = xds.assign_coords(coords)
    xds.time.attrs = {"format": "MJD", "scale": "UTC", "units": "d"}
    xds.frequency.attrs = {
        "rest_frequency": {
            "type": "quantity",
            "units": "Hz",
            "value": restfreq,
        },
        "frame": spectral_reference.upper(),
        "units": "Hz",
        "wave_unit": "mm",
        "crval": chan_coords[len(chan_coords) // 2],
        "cdelt": (chan_coords[1] - chan_coords[0] if len(chan_coords) > 1 else 1000.0),
        "pc": 1.0,
    }
    xds.velocity.attrs = {"doppler_type": "RADIO", "units": "m/s"}
    attr_note = _l_m_attr_notes()
    xds.l.attrs = {
        "type": "quantity",
        "crval": 0.0,
        "cdelt": -abs(cell_size[0]),
        "units": "rad",
        "type": "quantity",
        "note": attr_note["l"]
    }
    xds.m.attrs = {
        "type": "quantity",
        "crval": 0.0,
        "cdelt": abs(cell_size[1]),
        "units": "rad",
        "type": "quantity",
        "note": attr_note["m"]
    }
    xds.attrs = {
        "direction": {
            "reference": {
                "type": "sky_coord",
                "frame": direction_reference,
                "equinox": "J2000",
                "value": list(phase_center),
                "units": ["rad", "rad"],
                "cdelt": [-abs(cell_size[0]), abs(cell_size[1])],
            },
            "long_pole": 0.0,
            "lat_pole": 0.0,
            "pc": [[1.0, 0.0], [0.0, 1.0]],
            "projection": projection,
            "projection_parameters": [0.0, 0.0],
        },
        "active_mask": "",
        "beam": None,
        "object_name": "",
        "obsdate": {
            "scale": "UTC",
            "format": "MJD",
            "value": time_coords[0],
            "units": "d",
        },
        "observer": "Karl Jansky",
        "pointing_center": {"value": list(phase_center), "initial": True},
        "description": "",
        "telescope": {
            "name": "ALMA",
            "position": {
                "type": "position",
                "ellipsoid": "GRS80",
                "units": ["rad", "rad", "m"],
                "value": [-1.1825465955049892, -0.3994149869262738, 6379946.01326443],
            },
        },
        "history": None,
    }
    return xds
