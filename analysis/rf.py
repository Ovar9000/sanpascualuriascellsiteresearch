"""Vectorised terrain path-loss model (FSPL + 3-edge Deygout, ITU-R P.526).

Link budget (LTE Band 28, 10 MHz, 2x40 W RRU, 16.5 dBi panel, 1 dB jumper):
    EIRP per resource element  = 46 - 10*log10(600) + 16.5 - 1   ~ 33.7 dBm
    Outdoor service  RSRP >= -110 dBm  ->  max path loss 143.7 dB
    Indoor service   RSRP >= -100 dBm  ->  max path loss 133.7 dB
A flat 10 dB rural clutter loss (coconut canopy, light-construction houses)
is added on top of terrain loss.  The 3-edge Deygout model gets optimistic on
long multi-ridge land paths, so any point whose path crosses more than
MAX_LAND_KM of land is treated as unserved (sub-GHz rural cell-edge practice
with downtilted panels and a 23 dBm handset uplink).  Over-water paths are
allowed up to MAX_TOTAL_KM.
"""
import numpy as np

from dem import EARTH_R, dest

F_MHZ = 758.0
EIRP_RE_DBM = 33.7
CLUTTER_DB = 10.0
RSRP_OUTDOOR = -110.0
RSRP_INDOOR = -100.0
MAX_LAND_KM = 10.0
MAX_TOTAL_KM = 20.0


def _knife(v):
    vs = np.where(v > -0.78, v, 0.0)
    out = 6.9 + 20 * np.log10(np.sqrt((vs - 0.1) ** 2 + 1) + vs - 0.1)
    return np.where(v > -0.78, out, 0.0)


def _edge(t, H, ta, ya, tb, yb, D, lam, mask_extra=None):
    """Fresnel parameter v for every sample of a sub-path [ta, tb]."""
    span = np.maximum(tb - ta, 1e-9)
    frac = (t - ta) / span
    line = ya + (yb - ya) * frac
    d1 = np.maximum((t - ta) * D, 1.0)
    d2 = np.maximum((tb - t) * D, 1.0)
    v = (H - line) * np.sqrt(2.0 / lam * (d1 + d2) / (d1 * d2))
    inside = (t > ta) & (t < tb)
    if mask_extra is not None:
        inside &= mask_extra
    return np.where(inside, v, -np.inf)


def path_loss(dem, site_lat, site_lon, tx_agl, lats, lons, rx_agl=1.5, k=4 / 3, n=160):
    """Path loss (dB) from one mast to many receiver points."""
    lats = np.asarray(lats, float)
    lons = np.asarray(lons, float)
    kx = 111_320.0 * np.cos(np.radians(site_lat))
    D = np.hypot((lons - site_lon) * kx, (lats - site_lat) * 111_320.0)
    D = np.maximum(D, 30.0)
    t = np.linspace(0, 1, n + 2)[1:-1][None, :]
    la = site_lat + (lats[:, None] - site_lat) * t
    lo = site_lon + (lons[:, None] - site_lon) * t
    Dm = D[:, None]
    H = dem.elev(la, lo) + Dm * t * Dm * (1 - t) / (2 * k * EARTH_R)
    y0 = float(dem.elev(site_lat, site_lon)) + tx_agl
    y1 = (dem.elev(lats, lons) + rx_agl)[:, None]
    lam = 299.792458 / F_MHZ

    # main edge over full path
    v = _edge(t, H, 0.0, y0, 1.0, y1, Dm, lam)
    im = np.argmax(v, axis=1)
    rows = np.arange(len(D))
    vm = v[rows, im]
    tm = t[0, im][:, None]
    hm = H[rows, im][:, None]
    loss = _knife(vm)
    # secondary edges either side of the main edge (only when main edge counts)
    vl = _edge(t, H, 0.0, y0, tm, hm, Dm, lam).max(axis=1)
    vr = _edge(t, H, tm, hm, 1.0, y1, Dm, lam).max(axis=1)
    active = vm > -0.78
    loss = loss + np.where(active, _knife(vl) + _knife(vr), 0.0)
    fspl = 32.45 + 20 * np.log10(F_MHZ) + 20 * np.log10(D / 1000.0)
    land_km = (dem.elev(la, lo) > 0.5).mean(axis=1) * D / 1000.0
    pl = fspl + loss + CLUTTER_DB
    too_far = (land_km > MAX_LAND_KM) | (D / 1000.0 > MAX_TOTAL_KM)
    return np.where(too_far, 250.0, pl)


def rsrp(dem, site, lats, lons, chunk=4000):
    lat, lon, agl = site
    out = np.empty(len(lats))
    for i in range(0, len(lats), chunk):
        out[i:i + chunk] = EIRP_RE_DBM - path_loss(dem, lat, lon, agl, lats[i:i + chunk], lons[i:i + chunk])
    return out


def settlement_points(dem, lat, lon, radius=600.0, spacing=90.0):
    """Land sample points around a barangay centre (proxy for where people live)."""
    g = np.arange(-radius, radius + 1, spacing)
    X, Y = np.meshgrid(g, g)
    keep = np.hypot(X, Y) <= radius
    br = np.degrees(np.arctan2(X[keep], Y[keep]))
    ds = np.hypot(X[keep], Y[keep])
    la, lo = dest(lat, lon, br, ds)
    land = dem.elev(la, lo) > 1.0
    if land.sum() < 3:          # coastal point sitting in the sea pixel
        land = np.ones_like(land)
    return la[land], lo[land]
