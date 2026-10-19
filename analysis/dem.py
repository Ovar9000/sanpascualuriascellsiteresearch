"""SRTM 1-arcsecond DEM mosaic and propagation helpers for Burias Island.

Tiles come from the public AWS Terrain Tiles bucket (skadi layout):
    https://s3.amazonaws.com/elevation-tiles-prod/skadi/N13/N13E122.hgt.gz
Run fetch_dem.sh first; set DEM_DIR to override the tile location.
"""
import math
import os

import numpy as np

DEM_DIR = os.environ.get("DEM_DIR", os.path.join(os.path.dirname(__file__), "..", "dem"))
N = 3601                      # samples per 1-arcsec tile edge
LAT0, LON0 = 14.0, 122.0      # NW corner of the 2x2 mosaic
STEP = 1.0 / 3600.0
EARTH_R = 6_371_000.0


def load_mosaic():
    """Return a (7201, 7201) int16 array covering 12-14N, 122-124E (row 0 = 14N)."""
    m = np.zeros((2 * N - 1, 2 * N - 1), dtype=np.float32)
    for lat in (13, 12):
        for lon in (122, 123):
            path = os.path.join(DEM_DIR, f"N{lat}E{lon}.hgt")
            t = np.fromfile(path, dtype=">i2").reshape(N, N).astype(np.float32)
            t[t < -1000] = 0.0            # voids are almost always open sea here
            r0 = int(round((LAT0 - (lat + 1)) * 3600))
            c0 = int(round((lon - LON0) * 3600))
            m[r0:r0 + N, c0:c0 + N] = t
    return m


def despike(z, lat_n=13.30, lat_s=12.78, lon_w=122.80, lon_e=123.36, tol=80.0):
    """Replace SRTM spikes/pits over Burias with the local 7x7 median.

    The raw skadi tiles contain isolated radar spikes (one reads 1,823 m on an
    island whose true summit is ~330-435 m); left in, they would masquerade as
    perfect tower sites.
    """
    from scipy.ndimage import median_filter
    r0, c0 = int((LAT0 - lat_n) / STEP), int((lon_w - LON0) / STEP)
    r1, c1 = int((LAT0 - lat_s) / STEP), int((lon_e - LON0) / STEP)
    w = z[r0:r1, c0:c1]
    med = median_filter(w, size=7)
    bad = np.abs(w - med) > tol
    w[bad] = med[bad]
    return int(bad.sum())


class DEM:
    def __init__(self):
        self.z = load_mosaic()
        self.spikes_fixed = despike(self.z)

    @staticmethod
    def rc(lat, lon):
        return (LAT0 - lat) / STEP, (lon - LON0) / STEP

    @staticmethod
    def latlon(r, c):
        return LAT0 - r * STEP, LON0 + c * STEP

    def elev(self, lat, lon):
        """Bilinear elevation (m) at arrays of lat/lon."""
        r, c = self.rc(np.asarray(lat, float), np.asarray(lon, float))
        r0 = np.clip(np.floor(r).astype(int), 0, self.z.shape[0] - 2)
        c0 = np.clip(np.floor(c).astype(int), 0, self.z.shape[1] - 2)
        fr, fc = r - r0, c - c0
        z = self.z
        return ((z[r0, c0] * (1 - fr) + z[r0 + 1, c0] * fr) * (1 - fc)
                + (z[r0, c0 + 1] * (1 - fr) + z[r0 + 1, c0 + 1] * fr) * fc)


def dest(lat, lon, bearing_deg, dist_m):
    """Flat-earth destination point; fine for paths < 30 km at 13N."""
    b = np.radians(bearing_deg)
    dlat = dist_m * np.cos(b) / 111_320.0
    dlon = dist_m * np.sin(b) / (111_320.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def dist_m(lat1, lon1, lat2, lon2):
    kx = 111_320.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot((lon2 - lon1) * kx, (lat2 - lat1) * 111_320.0)


def bearing(lat1, lon1, lat2, lon2):
    kx = math.cos(math.radians((lat1 + lat2) / 2))
    return (math.degrees(math.atan2((lon2 - lon1) * kx, lat2 - lat1)) + 360) % 360


def viewshed(dem, lat, lon, tx_agl, rx_agl=1.5, radius=12_000, step=30.0, n_rays=1440, k=4 / 3):
    """Radial viewshed from a mast.

    Returns (lats, lons, dist, excess) arrays of shape (n_rays, n_steps) where
    `excess` is how many metres the receiver sits *below* the terrain horizon
    (<= 0 means clear line of sight).  A small positive excess is a single
    shallow obstruction that sub-GHz LTE usually diffracts over.
    """
    ground = float(dem.elev(lat, lon))
    h_tx = ground + tx_agl
    d = np.arange(step, radius + step, step)
    br = np.linspace(0, 360, n_rays, endpoint=False)
    B, D = np.meshgrid(br, d, indexing="ij")
    la, lo = dest(lat, lon, B, D)
    zt = dem.elev(la, lo)
    bulge = D ** 2 / (2 * k * EARTH_R)
    terrain_ang = (zt - bulge - h_tx) / D
    horizon = np.maximum.accumulate(terrain_ang, axis=1)
    horizon = np.concatenate([np.full((n_rays, 1), -np.inf), horizon[:, :-1]], axis=1)
    rx_ang = (zt + rx_agl - bulge - h_tx) / D
    excess = (horizon - rx_ang) * D
    return la, lo, D, excess, zt


def mw_profile(dem, a, b, ha, hb, f_ghz, k=4 / 3, step=30.0):
    """Microwave path check between (lat, lon) a and b with mast heights ha/hb.

    Returns dict with distance, worst clearance as a fraction of the first
    Fresnel radius, and the position/height of the controlling obstacle.
    Design rule used in the report: >= 0.6 F1 at k=4/3 (and >= 0.3 F1 at
    k=2/3 for the sub-refractive check).
    """
    D = dist_m(*a, *b)
    n = max(int(D // step), 2)
    t = np.linspace(0, 1, n + 1)[1:-1]
    la = a[0] + (b[0] - a[0]) * t
    lo = a[1] + (b[1] - a[1]) * t
    zt = dem.elev(la, lo) + 10.0            # +10 m allowance for tree canopy / SRTM bias
    za = float(dem.elev(*a)) + ha
    zb = float(dem.elev(*b)) + hb
    d1 = t * D
    d2 = D - d1
    ray = za + (zb - za) * t
    bulge = d1 * d2 / (2 * k * EARTH_R)
    lam = 0.299792458 / f_ghz
    f1 = np.sqrt(lam * d1 * d2 / D)
    clear = (ray - zt - bulge) / f1
    i = int(np.argmin(clear))
    return {
        "dist_km": D / 1000,
        "min_f1": float(clear[i]),
        "obs_km": float(d1[i] / 1000),
        "obs_ground": float(zt[i] - 10.0),
    }
