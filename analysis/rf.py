"""Terrain-aware macro-cell path-loss model, calibrated to field observation.

Model (Standard-Propagation-Model style, as used by planning tools):
    PL = COST-231 Hata (suburban) with effective antenna height
         + K_DIFF * Deygout 3-edge knife-edge diffraction (ITU-R P.526)
         + OFFSET_DB

Calibration targets (field observation by the Technical Advisor):
    * Bolod hill serves Bolod (Pob.), Terraplin/port, Nazareno and Busing
    * Bolod hill does NOT serve Laurente (3.7 km, behind a 40 m spur) or
      any other barangay
    * usable signal on land ends at roughly 3-4 km from the towers
The defaults below were fitted by calibrate.py to meet all three
(K_DIFF = 0.6, OFFSET_DB = +2, usable = RSRP >= -110 dBm, and an uplink fade of
15 dB/km beyond 3.5 km), which ends Bolod's usable signal at 3-4 km on land.
Edit and re-run calibrate.py when drive-test data is available.

Link budget: 2x40 W RRU on a 20 MHz LTE-1800 carrier (1200 subcarriers),
17.5 dBi panel, 1 dB jumper  ->  EIRP per resource element ~ 32.7 dBm.

Signal classes (RSRP):
    >= -80 excellent | -80..-90 strong | -90..-100 good indoor |
    -100..-110 outdoor only | -110..-120 edge | < -120 no service
"""
import numpy as np

from dem import EARTH_R, dest

F_MHZ = 1800.0
EIRP_RE_DBM = 46 - 10 * np.log10(1200) + 17.5 - 1.0
K_DIFF = 0.6
OFFSET_DB = 2.0
FADE_START_KM = 3.5         # beyond this the handset uplink runs out: extra loss per km
FADE_DB_PER_KM = 15.0
MAX_RANGE_KM = 5.0          # computation bound
RSRP_OUTDOOR = -110.0       # usable outdoor / in-vehicle
RSRP_INDOOR = -100.0        # in-building grade
# lower bound of each display class (dBm) and its label
CLASSES = [(-80, "Excellent  >= -80"), (-90, "Strong  -80 to -90"), (-100, "Good indoor  -90 to -100"),
           (-110, "Outdoor only  -100 to -110"), (-120, "Edge / unreliable  -110 to -120")]


def _knife(v):
    vs = np.where(v > -0.78, v, 0.0)
    out = 6.9 + 20 * np.log10(np.sqrt((vs - 0.1) ** 2 + 1) + vs - 0.1)
    return np.where(v > -0.78, out, 0.0)


def _edge(t, H, ta, ya, tb, yb, D, lam):
    """Fresnel parameter v for every sample of a sub-path [ta, tb]."""
    span = np.maximum(tb - ta, 1e-9)
    line = ya + (yb - ya) * (t - ta) / span
    d1 = np.maximum((t - ta) * D, 1.0)
    d2 = np.maximum((tb - t) * D, 1.0)
    v = (H - line) * np.sqrt(2.0 / lam * (d1 + d2) / (d1 * d2))
    return np.where((t > ta) & (t < tb), v, -np.inf)


def hata_suburban(d_km, f_mhz, heff, hm=1.5):
    """COST-231 Hata (f >= 1500 MHz) or Okumura-Hata, with the suburban correction."""
    lf = np.log10(f_mhz)
    ahm = (1.1 * lf - 0.7) * hm - (1.56 * lf - 0.8)
    lh = np.log10(heff)
    a = 46.3 + 33.9 * lf if f_mhz >= 1500 else 69.55 + 26.16 * lf
    L = a - 13.82 * lh - ahm + (44.9 - 6.55 * lh) * np.log10(np.maximum(d_km, 0.05))
    return L - 2 * np.log10(f_mhz / 28.0) ** 2 - 5.4


def path_loss(dem, site_lat, site_lon, tx_agl, lats, lons, rx_agl=1.5, k=4 / 3, n=160,
              f_mhz=None, k_diff=None, offset=None):
    """Path loss (dB) from one mast to many receiver points."""
    f_mhz = F_MHZ if f_mhz is None else f_mhz
    k_diff = K_DIFF if k_diff is None else k_diff
    offset = OFFSET_DB if offset is None else offset
    lats = np.asarray(lats, float)
    lons = np.asarray(lons, float)
    kx = 111_320.0 * np.cos(np.radians(site_lat))
    D = np.hypot((lons - site_lon) * kx, (lats - site_lat) * 111_320.0)
    D = np.maximum(D, 30.0)
    t = np.linspace(0, 1, n + 2)[1:-1][None, :]
    la = site_lat + (lats[:, None] - site_lat) * t
    lo = site_lon + (lons[:, None] - site_lon) * t
    Dm = D[:, None]
    # nearest-cell sampling keeps obstruction heights the same whatever the
    # bearing (bilinear sampling smooths diagonal paths and leaves N/S/E/W streaks)
    H = dem.elev_nn(la, lo) + Dm * t * Dm * (1 - t) / (2 * k * EARTH_R)
    y0 = float(dem.elev(site_lat, site_lon)) + tx_agl
    z_rx = dem.elev(lats, lons)
    y1 = (z_rx + rx_agl)[:, None]
    lam = 299.792458 / f_mhz

    v = _edge(t, H, 0.0, y0, 1.0, y1, Dm, lam)
    im = np.argmax(v, axis=1)
    rows = np.arange(len(D))
    vm = v[rows, im]
    tm = t[0, im][:, None]
    hm_ = H[rows, im][:, None]
    diff = _knife(vm)
    vl = _edge(t, H, 0.0, y0, tm, hm_, Dm, lam).max(axis=1)
    vr = _edge(t, H, tm, hm_, 1.0, y1, Dm, lam).max(axis=1)
    diff = diff + np.where(vm > -0.78, _knife(vl) + _knife(vr), 0.0)

    # effective antenna height: mast top above the receiver's ground, 20-200 m
    heff = np.clip(y0 - np.maximum(z_rx, 0.0), 20.0, 200.0)
    fade = np.maximum(D / 1000.0 - FADE_START_KM, 0.0) * FADE_DB_PER_KM
    return hata_suburban(D / 1000.0, f_mhz, heff) + k_diff * diff + offset + fade


def rsrp(dem, site, lats, lons, chunk=4000, max_range_km=None, **kw):
    """RSRP (dBm); points beyond the service radius are returned as -200."""
    lat, lon, agl = site
    max_range_km = MAX_RANGE_KM if max_range_km is None else max_range_km
    lats = np.asarray(lats, float)
    lons = np.asarray(lons, float)
    out = np.empty(len(lats))
    for i in range(0, len(lats), chunk):
        out[i:i + chunk] = EIRP_RE_DBM - path_loss(dem, lat, lon, agl, lats[i:i + chunk], lons[i:i + chunk], **kw)
    kx = 111_320.0 * np.cos(np.radians(lat))
    far = np.hypot((lons - lon) * kx, (lats - lat) * 111_320.0) > max_range_km * 1000.0
    out[far] = -200.0
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
