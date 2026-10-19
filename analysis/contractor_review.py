"""Technical review of the contractor's 'deeper Bolod / Pinamasingan Road' site.

Uses the field-calibrated model in rf.py (Bolod hill serves Bolod, Terraplin,
Nazareno and Busing only; usable range 3-4 km).

Usage:  DEM_DIR=/path/to/hgt python3 contractor_review.py
Outputs (../results/): review.json, fig_*.png, cov_*.png, san_pascual_review.kmz
"""
import json
import os
import zipfile
from itertools import combinations

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, ListedColormap, LinearSegmentedColormap
from matplotlib.patches import Patch

import rf
from dem import DEM, bearing, dest, dist_m, mw_profile
from roads import RoadProxy
from site_selection import BOLOD, MAST_AGL, MW_GHZ, candidates, coverage, load_barangays, mw_heights

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

# Contractor site is not yet surveyed: three plausible spots on the
# Poblacion -> Pinamasingan road inside Bolod, all below the Bolod hill summit.
CONTRACTOR = [
    {"id": "CT-1", "name": "Contractor scenario 1 (road, 1.0 km S of towers)", "lat": 13.1158, "lon": 122.9892},
    {"id": "CT-2", "name": "Contractor scenario 2 (road, 1.7 km S of towers)", "lat": 13.1100, "lon": 122.9908},
    {"id": "CT-3", "name": "Contractor scenario 3 (road, 2.1 km S of towers)", "lat": 13.1067, "lon": 122.9933},
]
MAX_ROAD_SPUR_M = 1000.0
MAX_MW_KM = 20.0
STEP = 1.0 / 3600.0                       # 1 arcsec (~30 m) coverage rasters
BOX = (13.175, 12.955, 122.86, 123.15)    # island view: N, S, W, E

CLASS_COLORS = ["#0b7a3b", "#58b947", "#f4d03f", "#f08a24", "#d7301f"]   # excellent .. edge
CLASS_EDGES = [-200, -120, -110, -100, -90, -80, 0]


# ----------------------------------------------------------------- rasters
class Grid:
    def __init__(self, dem, box=BOX, step=STEP):
        n, s, w, e = box
        self.box = box
        self.lats = np.arange(n, s, -step)
        self.lons = np.arange(w, e, step)
        LA, LO = np.meshgrid(self.lats, self.lons, indexing="ij")
        self.LA, self.LO = LA, LO
        self.z = dem.elev(LA, LO)
        self.land = self.z > 0.5

    def site_raster(self, dem, site):
        """RSRP raster for one site, computed only inside its service radius."""
        lat, lon, _ = site
        r = np.full(self.LA.shape, -200.0)
        dlat = (rf.MAX_RANGE_KM + 0.2) / 111.32
        dlon = dlat / np.cos(np.radians(lat))
        ii = (self.lats <= lat + dlat) & (self.lats >= lat - dlat)
        jj = (self.lons <= lon + dlon) & (self.lons >= lon - dlon)
        sub = np.ix_(ii, jj)
        vals = rf.rsrp(dem, site, self.LA[sub].ravel(), self.LO[sub].ravel())
        r[sub] = vals.reshape(self.LA[sub].shape)
        return r

    def km2(self, mask):
        cell = (111.32 * STEP) ** 2 * np.cos(np.radians(13.06))
        return float(mask.sum() * cell)


# ----------------------------------------------------------------- drawing
def classify(r):
    c = np.digitize(r, CLASS_EDGES[1:-1])     # 0 = none, 1 = edge ... 5 = excellent
    return np.ma.masked_where(c == 0, c)


def basemap(ax, g, extent_box):
    n, s, w, e = extent_box
    ext = (g.lons[0], g.lons[-1], g.lats[-1], g.lats[0])
    ls = LightSource(azdeg=315, altdeg=40)
    land_cmap = LinearSegmentedColormap.from_list("land", ["#eef0e2", "#dfe3c8", "#cfc9a6", "#b9a983", "#a08d6a"])
    z = np.where(g.land, g.z, np.nan)
    shade = ls.hillshade(np.nan_to_num(g.z), vert_exag=3, dx=30, dy=30)
    ax.imshow(np.ma.masked_where(g.land, np.ones_like(g.z)), cmap=ListedColormap(["#dbe8f2"]), extent=ext, zorder=0)
    ax.imshow(np.ma.masked_invalid(z), cmap=land_cmap, vmin=0, vmax=200, extent=ext, zorder=1, alpha=0.9)
    ax.imshow(np.ma.masked_where(~g.land, shade), cmap="gray", extent=ext, alpha=0.28, zorder=2, vmin=0, vmax=1)
    ax.contour(g.lons, g.lats, np.where(g.land, g.z, -1), levels=np.arange(25, 225, 25), colors="#7d6e55",
               linewidths=0.35, alpha=0.6, zorder=3)
    ax.contour(g.lons, g.lats, g.z, levels=[0.5], colors="#5f7f99", linewidths=0.6, zorder=3)
    ax.set_xlim(w, e)
    ax.set_ylim(s, n)
    ax.set_aspect(1 / np.cos(np.radians((n + s) / 2)))
    ax.tick_params(labelsize=6, colors="#555")
    ax.ticklabel_format(useOffset=False, style="plain")
    for sp in ax.spines.values():
        sp.set_color("#999")


def overlay(ax, g, r, alpha=0.78):
    ext = (g.lons[0], g.lons[-1], g.lats[-1], g.lats[0])
    r = np.where(g.land, r, -200.0)                 # people live on land; keep the sea clear
    ax.imshow(classify(r), cmap=ListedColormap(CLASS_COLORS[::-1]), vmin=1, vmax=5, extent=ext,
              alpha=alpha, zorder=4, interpolation="nearest")


def rings(ax, site, radii=(1, 2, 3, 4), color="#222"):
    br = np.linspace(0, 360, 181)
    for rk in radii:
        la, lo = dest(site["lat"], site["lon"], br, rk * 1000)
        ax.plot(lo, la, color=color, lw=0.6, ls=(0, (3, 3)), alpha=0.7, zorder=6)
        la0, lo0 = dest(site["lat"], site["lon"], 45, rk * 1000)
        ax.text(lo0, la0, f"{rk} km", fontsize=5.5, color=color, zorder=7, clip_on=True,
                path_effects=[pe.withStroke(linewidth=2, foreground="white")])


def labels(ax, brgys, box, served_marks=False):
    n, s, w, e = box
    for b in brgys:
        if not (s < b["lat"] < n and w < b["lon"] < e):
            continue
        ax.plot(b["lon"], b["lat"], "o", ms=3.2, mfc="white", mec="#111", mew=0.8, zorder=8)
        txt = f"{b['barangay'].split(' (')[0]}  {b['pop']:,}"
        if served_marks:
            txt += "  ✓" if b["served"] else "  ✗"
        ax.text(b["lon"] + 0.0018, b["lat"] + 0.0012, txt, fontsize=6, color="#111", zorder=8, clip_on=True,
                path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])


def roads_draw(ax, roads):
    for path in roads.paths.values():
        p = np.array(path)
        ax.plot(p[:, 1], p[:, 0], color="#8a5a2b", lw=0.9, ls=(0, (4, 2)), alpha=0.85, zorder=5)


def site_mark(ax, s, marker="^", size=10):
    ax.plot(s["lon"], s["lat"], marker=marker, ms=size, mfc=s["color"], mec="black", mew=1.0, zorder=9, clip_on=True)
    ax.text(s["lon"] + 0.0025, s["lat"] - 0.0035, s["id"], fontsize=7.5, weight="bold", zorder=9, clip_on=True,
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])


def legend(ax, loc="lower left"):
    hs = [Patch(fc=c, ec="none", alpha=0.8, label=l) for c, (_, l) in zip(CLASS_COLORS, rf.CLASSES)]
    ax.legend(handles=hs, loc=loc, fontsize=5.8, title="Predicted RSRP (dBm)", title_fontsize=6.2, framealpha=0.92)


def scalebar(ax, box, km=2):
    n, s, w, e = box
    lat = s + (n - s) * 0.05
    lon0 = e - (e - w) * 0.05 - km / (111.32 * np.cos(np.radians(lat)))
    lon1 = lon0 + km / (111.32 * np.cos(np.radians(lat)))
    ax.plot([lon0, lon1], [lat, lat], color="k", lw=2.2, zorder=10, solid_capstyle="butt")
    ax.text((lon0 + lon1) / 2, lat + (n - s) * 0.012, f"{km} km", ha="center", fontsize=6, zorder=10,
            path_effects=[pe.withStroke(linewidth=2, foreground="white")])


def zoom_box(lat, lon, half_km=6.0):
    dlat = half_km / 111.32
    dlon = dlat / np.cos(np.radians(lat))
    return (lat + dlat, lat - dlat, lon - dlon, lon + dlon)


def map_panel(ax, g, brgys, roads, box, layers, sites, title, ring_site=None, served_marks=False, legend_loc="lower left"):
    basemap(ax, g, box)
    for r in layers:
        overlay(ax, g, r)
    roads_draw(ax, roads)
    if ring_site is not None:
        rings(ax, ring_site)
    labels(ax, brgys, box, served_marks)
    for s in sites:
        site_mark(ax, s, marker=s.get("marker", "^"))
    scalebar(ax, box)
    legend(ax, legend_loc)
    ax.set_title(title, fontsize=8.5, loc="left")


# ----------------------------------------------------------------- KMZ
def kml_color(hex6, alpha="ff"):
    h = hex6.lstrip("#")
    return alpha + h[4:6] + h[2:4] + h[0:2]


def overlay_png(r, fname):
    c = np.digitize(r, CLASS_EDGES[1:-1])
    rgba = np.zeros(r.shape + (4,))
    for k, col in zip(range(5, 0, -1), CLASS_COLORS):
        rgba[c == k] = (*matplotlib.colors.to_rgb(col), 0.72)
    plt.imsave(os.path.join(OUT, fname), rgba)


def write_kmz(path, brgys, roads, sites, links, overlays):
    styles, pm, bar, rd, lk, ov = [], [], [], [], [], []
    for s in sites:
        sid = s["id"].replace(" ", "").replace("-", "")
        styles.append(f'<Style id="s{sid}"><IconStyle><color>{kml_color(s["color"])}</color><scale>1.3</scale>'
                      f'<Icon><href>http://maps.google.com/mapfiles/kml/shapes/target.png</href></Icon></IconStyle>'
                      f'<PolyStyle><color>{kml_color(s["color"], "cc")}</color></PolyStyle></Style>')
        d = 0.00012
        ring = " ".join(f"{s['lon'] + dx},{s['lat'] + dy},{s['agl']}" for dx, dy in [(-d, -d), (d, -d), (d, d), (-d, d), (-d, -d)])
        pm.append(f'<Placemark><name>{s["id"]} {s["name"]}</name><description>{s.get("desc", "")}</description>'
                  f'<styleUrl>#s{sid}</styleUrl><MultiGeometry><Point><coordinates>{s["lon"]},{s["lat"]},0</coordinates></Point>'
                  f'<Polygon><extrude>1</extrude><altitudeMode>relativeToGround</altitudeMode><outerBoundaryIs><LinearRing>'
                  f'<coordinates>{ring}</coordinates></LinearRing></outerBoundaryIs></Polygon></MultiGeometry></Placemark>')
    for b in brgys:
        d = 0.0012
        h = b["pop"] * 0.08
        ring = " ".join(f"{b['lon'] + dx},{b['lat'] + dy},{h}" for dx, dy in [(-d, -d), (d, -d), (d, d), (-d, d), (-d, -d)])
        col = "#2e7d32" if b["served"] else "#c62828"
        bar.append(f'<Placemark><name>{b["barangay"]} ({b["pop"]:,})</name>'
                   f'<description>2020 Census: {b["pop"]:,}. Served by Bolod today: {"yes" if b["served"] else "no"}</description>'
                   f'<Style><PolyStyle><color>{kml_color(col, "b0")}</color></PolyStyle></Style>'
                   f'<Polygon><extrude>1</extrude><altitudeMode>relativeToGround</altitudeMode><outerBoundaryIs><LinearRing>'
                   f'<coordinates>{ring}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>')
    for name, p in roads.paths.items():
        coords = " ".join(f"{lo},{la},0" for la, lo in p[::2])
        rd.append(f'<Placemark><name>{name} (terrain-inferred)</name><Style><LineStyle><color>ff2b5a8a</color><width>2</width></LineStyle></Style>'
                  f'<LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark>')
    for a, b, label in links:
        lk.append(f'<Placemark><name>{label}</name><Style><LineStyle><color>ff00c000</color><width>3</width></LineStyle></Style>'
                  f'<LineString><altitudeMode>relativeToGround</altitudeMode><coordinates>{a[1]},{a[0]},{a[2]} {b[1]},{b[0]},{b[2]}</coordinates></LineString></Placemark>')
    n, s, w, e = BOX
    for name, fname, visible in overlays:
        ov.append(f'<GroundOverlay><name>{name}</name><visibility>{int(visible)}</visibility>'
                  f'<Icon><href>{fname}</href></Icon><LatLonBox><north>{n}</north><south>{s}</south><east>{e}</east><west>{w}</west></LatLonBox></GroundOverlay>')
    legend_html = "<br/>".join(f'<font color="{c}">&#9632;</font> {l}' for c, (_, l) in zip(CLASS_COLORS, rf.CLASSES))
    kml = ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           '<name>San Pascual cell-site review (Sangguniang Bayan)</name>'
           f'<description><![CDATA[Predicted RSRP, field-calibrated model (usable range 3-4 km).<br/>{legend_html}]]></description>'
           + "".join(styles)
           + '<Folder><name>Sites</name>' + "".join(pm) + '</Folder>'
           + '<Folder><name>Microwave backhaul</name>' + "".join(lk) + '</Folder>'
           + '<Folder><name>Barangay population (3D columns)</name>' + "".join(bar) + '</Folder>'
           + '<Folder><name>Road corridors (terrain-inferred proxy)</name>' + "".join(rd) + '</Folder>'
           + '<Folder><name>Predicted RSRP coverage</name>' + "".join(ov) + '</Folder>'
           + '</Document></kml>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml)
        for _, fname, _ in overlays:
            zf.write(os.path.join(OUT, fname), fname)


# ----------------------------------------------------------------- profiles
def terrain_profile(ax, dem, a, b, ha, hb, color, title, fresnel_ghz=None):
    D = dist_m(*a, *b)
    t = np.linspace(0, 1, 400)
    z = dem.elev(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    za = float(dem.elev(*a)) + ha
    zb = float(dem.elev(*b)) + hb
    x = t * D / 1000
    line = za + (zb - za) * t
    ax.fill_between(x, 0, z, color="#b9a983", zorder=2)
    ax.plot(x, z, color="#7d6e55", lw=0.6, zorder=3)
    if fresnel_ghz:
        lam = 0.299792458 / fresnel_ghz
        d1 = t * D
        f1 = np.sqrt(np.maximum(lam * d1 * (D - d1) / D, 0))
        ax.fill_between(x, line - 0.6 * f1, line + 0.6 * f1, color=color, alpha=0.18, zorder=1)
    ax.plot(x, line, color=color, lw=1.6, zorder=4)
    ax.plot([0, 0], [za - ha, za], color="black", lw=2.5, zorder=5)
    if hb > 2:
        ax.plot([x[-1], x[-1]], [zb - hb, zb], color="black", lw=2.5, zorder=5)
    blocked = bool(np.any(z[3:-3] > line[3:-3]))
    ax.set_title(title + ("  -  BLOCKED by terrain" if blocked else "  -  clear line of sight"), fontsize=8,
                 color="#b71c1c" if blocked else "#1b5e20", loc="left")
    ax.set_ylim(0, max(z.max(), za, zb) * 1.18 + 5)
    ax.set_xlim(0, x[-1])
    ax.tick_params(labelsize=6)
    ax.set_ylabel("m above sea", fontsize=6.5)
    ax.grid(alpha=0.25, lw=0.4)
    return blocked


# ----------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    dem = DEM()
    brgys = load_barangays(dem)
    pops = np.array([b["pop"] for b in brgys])
    unserved = np.array([not b["served"] for b in brgys])
    roads = RoadProxy(dem, brgys)
    g = Grid(dem)
    bolod_ll = (BOLOD["lat"], BOLOD["lon"])
    near_b = lambda la, lo: min(brgys, key=lambda b: dist_m(la, lo, b["lat"], b["lon"]))["barangay"]

    bolod = {"id": "BOLOD", "name": "Existing towers, Bolod hill", "lat": BOLOD["lat"], "lon": BOLOD["lon"],
             "agl": BOLOD["agl"], "color": "#2e7d32", "ground": float(dem.elev(*bolod_ll)), "near": "Bolod"}
    bolod["raster"] = g.site_raster(dem, (bolod["lat"], bolod["lon"], bolod["agl"]))
    bolod["cov"] = coverage(dem, (bolod["lat"], bolod["lon"], bolod["agl"]), brgys)
    bolod_cov, bolod_cov_in = bolod["cov"][:, 0], bolod["cov"][:, 1]
    bolod_served = (bolod["raster"] >= rf.RSRP_OUTDOOR) & g.land

    # calibration record: usable range along every land radial from Bolod hill
    br = np.arange(0, 360, 2)
    ds = np.arange(50, 6001, 50)
    BB, DD = np.meshgrid(br, ds, indexing="ij")
    la, lo = dest(bolod["lat"], bolod["lon"], BB, DD)
    rr = rf.rsrp(dem, (bolod["lat"], bolod["lon"], bolod["agl"]), la.ravel(), lo.ravel()).reshape(la.shape)
    landr = dem.elev(la, lo) > 0.5
    rng = []
    for i in range(len(br)):
        ok = (rr[i] >= rf.RSRP_OUTDOOR) & landr[i]
        if landr[i].any():
            rng.append(float(ds[ok].max()) / 1000 if ok.any() else 0.0)
    calib = {
        "model": f"COST-231 Hata suburban @ {rf.F_MHZ:.0f} MHz + {rf.K_DIFF} x Deygout diffraction, service radius {rf.MAX_RANGE_KM} km",
        "usable_dBm": rf.RSRP_OUTDOOR, "indoor_dBm": rf.RSRP_INDOOR,
        "bolod_land_range_km": {"median": round(float(np.median(rng)), 2), "p25": round(float(np.percentile(rng, 25)), 2),
                                "p75": round(float(np.percentile(rng, 75)), 2)},
        "bolod_per_barangay": {b["barangay"]: {"usable": round(float(bolod_cov[i]), 2), "indoor": round(float(bolod_cov_in[i]), 2),
                                               "field": "served" if b["served"] else "not served",
                                               "km": round(dist_m(*bolod_ll, b["lat"], b["lon"]) / 1000, 1)}
                               for i, b in enumerate(brgys)},
    }
    print("calibration", json.dumps(calib["bolod_land_range_km"]),
          {k: v["usable"] for k, v in calib["bolod_per_barangay"].items() if v["usable"] > 0.02})

    def beyond(cov, col=0):
        ref = bolod_cov if col == 0 else bolod_cov_in
        return float((np.maximum(cov[:, col] - ref, 0) * pops * unserved).sum())

    def describe(s):
        s["ground"] = float(dem.elev(s["lat"], s["lon"]))
        s["cov"] = coverage(dem, (s["lat"], s["lon"], s["agl"]), brgys)
        s["raster"] = g.site_raster(dem, (s["lat"], s["lon"], s["agl"]))
        served = (s["raster"] >= rf.RSRP_OUTDOOR) & g.land
        s["served_land_km2"] = round(g.km2(served), 1)
        s["new_land_km2"] = round(g.km2(served & ~bolod_served), 1)
        s["overlap_with_bolod"] = round(float((served & bolod_served).sum() / max(served.sum(), 1)), 3)
        s["reach_unserved"] = int(round((s["cov"][:, 0] * pops * unserved).sum()))
        s["beyond_bolod"] = int(round(beyond(s["cov"])))
        s["beyond_bolod_indoor"] = int(round(beyond(s["cov"], 1)))
        s["dist_bolod_km"] = round(dist_m(*bolod_ll, s["lat"], s["lon"]) / 1000, 2)
        s["bearing"] = round(bearing(*bolod_ll, s["lat"], s["lon"]))
        s["antenna_top_asl"] = round(s["ground"] + s["agl"])
        return s

    # --- contractor -----------------------------------------------------------
    cts = []
    for c in CONTRACTOR:
        c = dict(c, agl=MAST_AGL, color="#e08214", marker="v", near="Bolod")
        describe(c)
        c["sensitivity"] = {}
        for h in (30, 45, 60):
            c["sensitivity"][h] = int(round(beyond(coverage(dem, (c["lat"], c["lon"], h), brgys))))
        c["mw"] = mw_profile(dem, bolod_ll, (c["lat"], c["lon"]), 40, MAST_AGL, MW_GHZ)
        cts.append(c)
        print(c["id"], round(c["ground"]), "overlap", c["overlap_with_bolod"], "beyond", c["beyond_bolod"], c["sensitivity"])
    ct = cts[1]

    # --- road-accessible hilltop pool ---------------------------------------
    pool = []
    for c in candidates(dem):
        c["road_m"] = roads.dist_to_road_m(c["lat"], c["lon"])
        if c["road_m"] > MAX_ROAD_SPUR_M:
            continue
        c["agl"] = MAST_AGL
        c["cov"] = coverage(dem, (c["lat"], c["lon"], MAST_AGL), brgys)
        c["beyond_bolod"] = beyond(c["cov"])
        pool.append(c)
    print(len(pool), "road-accessible hilltops")

    def mw_ok(a, b):
        if dist_m(a["lat"], a["lon"], b["lat"], b["lon"]) > MAX_MW_KM * 1000:
            return None
        h, _ = mw_heights(dem, (a["lat"], a["lon"]), (b["lat"], b["lon"]), MW_GHZ)
        return h if h is not None and h <= 45 else None

    # Ridge alternatives anchored on the directions the council asked about:
    # the best road-accessible hilltop within ANCHOR_KM of each target barangay
    # that also has a direct microwave hop to Bolod.
    ANCHOR_KM = 3.5
    anchor_specs = [
        ("ALT-A", "#1565c0", "Pinamasingan", "Pinamasingan ridge", "same Poblacion-Pinamasingan road, further out"),
        ("ALT-B", "#00897b", "Laurente", "Laurente-Nazareno ridge", "north-coast road to Laurente"),
        ("ALT-C", "#ad1457", "San Rafael", "San Rafael-Santa Cruz ridge", "west-coast road via San Rafael"),
        ("ALT-D", "#6a1b9a", "Malaking Ilog", "Malaking Ilog-Mapanique ridge", "inland Pinamasingan-San Pedro-Mapanique road"),
        ("ALT-E", "#ef6c00", "Cueva", "Cueva ridge", "Poblacion-Quintina road via Cueva"),
    ]
    by_name = {b["barangay"]: b for b in brgys}
    alts = []
    for aid, col, anchor, label, desc in anchor_specs:
        A = by_name[anchor]
        ranked = sorted((c for c in pool if dist_m(c["lat"], c["lon"], A["lat"], A["lon"]) <= ANCHOR_KM * 1000),
                        key=lambda c: -c["beyond_bolod"])
        for c in ranked:
            if any(dist_m(c["lat"], c["lon"], x["lat"], x["lon"]) < 2500 for x in alts):
                continue
            h = mw_ok(bolod, c)
            if h is None:
                continue
            a = {"id": aid, "color": col, "lat": c["lat"], "lon": c["lon"], "agl": MAST_AGL, "road_m": round(c["road_m"]),
                 "corridor": desc, "anchor": anchor, "mw_mast_m": h, "parent": "BOLOD"}
            a["near"] = near_b(a["lat"], a["lon"])
            a["name"] = label
            describe(a)
            a["mw"] = mw_profile(dem, bolod_ll, (a["lat"], a["lon"]), h, h, MW_GHZ)
            a["mw_7ghz_mast"] = mw_heights(dem, bolod_ll, (a["lat"], a["lon"]), 7.0)[0]
            alts.append(a)
            print(aid, a["name"], a["lat"], a["lon"], round(a["ground"]), "beyond", a["beyond_bolod"], a["beyond_bolod_indoor"],
                  "ovl", a["overlap_with_bolod"], "mw", h, a["mw_7ghz_mast"], a["dist_bolod_km"], "road", a["road_m"],
                  {k: round(float(a["cov"][i, 0]), 2) for i, k in enumerate(by_name) if a["cov"][i, 0] > 0.05})
            break

    # --- greedy network build-out (backhaul to Bolod or to an earlier pick) ----
    best = np.where(unserved, bolod_cov, 1.0)              # Bolod's fringe counts once
    on_air = [bolod]
    build = []
    remaining = list(pool)
    for step in range(8):
        def gain(c):
            if any(dist_m(c["lat"], c["lon"], s["lat"], s["lon"]) < 2500 for s in on_air):
                return -1.0
            return float(((np.maximum(best, c["cov"][:, 0]) - best) * pops).sum())
        remaining.sort(key=gain, reverse=True)
        pick = None
        for c in remaining[:40]:
            if gain(c) < 300:
                break
            for parent in on_air:
                h = mw_ok(parent, c)
                if h is not None:
                    pick = (c, parent, h)
                    break
            if pick:
                break
        if not pick:
            break
        c, parent, h = pick
        gval = gain(c)
        best = np.maximum(best, c["cov"][:, 0])
        s = {"id": f"N{step + 1}", "color": "#1565c0", "lat": c["lat"], "lon": c["lon"], "agl": MAST_AGL,
             "road_m": round(c["road_m"]), "parent": parent["id"], "mw_mast_m": h}
        s["near"] = near_b(s["lat"], s["lon"])
        s["name"] = f"{s['near']} hill"
        same = [a for a in alts if (a["lat"], a["lon"]) == (s["lat"], s["lon"])]
        if same:
            s["alt"], s["name"] = same[0]["id"], same[0]["name"]
        describe(s)
        s["gain"] = int(round(gval))
        s["cum_total"] = int(round((best * pops).sum()))
        s["mw"] = mw_profile(dem, (parent["lat"], parent["lon"]), (s["lat"], s["lon"]), h, h, MW_GHZ)
        on_air.append(s)
        build.append(s)
        remaining.remove(c)
        print(s["id"], s["name"], s["lat"], s["lon"], round(s["ground"]), "gain", s["gain"], "cum", s["cum_total"], "via", parent["id"], h)

    total_today = int(pops[~unserved].sum())
    ct_total = int(round((np.where(unserved, np.maximum(bolod_cov, ct["cov"][:, 0]), 1.0) * pops).sum()))
    bolod_total = int(round((np.where(unserved, bolod_cov, 1.0) * pops).sum()))

    packages = []
    for k in (1, 2, 3):
        for combo in combinations(alts, k):
            cov = np.maximum.reduce([bolod_cov] + [c["cov"][:, 0] for c in combo])
            packages.append({"sites": [c["id"] for c in combo], "beyond_bolod": int(round(((cov - bolod_cov) * pops * unserved).sum())),
                             "total": int(round((np.where(unserved, cov, 1.0) * pops).sum()))})
    best_pkg = {k: max((p for p in packages if len(p["sites"]) == k), key=lambda p: p["beyond_bolod"]) for k in (1, 2, 3)}

    # ------------------------------------------------------------- figures
    plt.rcParams.update({"font.family": "Inter", "font.size": 7})
    zb = zoom_box(13.118, 122.99, 5.5)

    fig, ax = plt.subplots(figsize=(8.2, 7.4), dpi=200)
    map_panel(ax, g, brgys, roads, zb, [bolod["raster"]], [bolod],
              "Existing Bolod hill towers: field-calibrated prediction  (✓ served / ✗ not served, per council)",
              ring_site=bolod, served_marks=True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_calibration_bolod.png"))
    plt.close(fig)

    fig, axs = plt.subplots(1, 3, figsize=(17, 6.2), dpi=180)
    map_panel(axs[0], g, brgys, roads, zb, [bolod["raster"]], [bolod], "A. Existing Bolod hill towers", ring_site=bolod)
    map_panel(axs[1], g, brgys, roads, zb, [ct["raster"]], [bolod, ct],
              f"B. Contractor {ct['id']} alone (antenna top {ct['antenna_top_asl']} m vs {round(bolod['ground'] + bolod['agl'])} m ASL)", ring_site=ct)
    basemap(axs[2], g, zb)
    ext = (g.lons[0], g.lons[-1], g.lats[-1], g.lats[0])
    ct_served = (ct["raster"] >= rf.RSRP_OUTDOOR) & g.land
    axs[2].imshow(np.ma.masked_where(~(ct_served & bolod_served), np.ones_like(g.z)), cmap=ListedColormap(["#8c8c8c"]),
                  extent=ext, alpha=0.7, zorder=4)
    axs[2].imshow(np.ma.masked_where(~(ct_served & ~bolod_served), np.ones_like(g.z)), cmap=ListedColormap(["#e08214"]),
                  extent=ext, alpha=0.95, zorder=4)
    roads_draw(axs[2], roads)
    labels(axs[2], brgys, zb)
    site_mark(axs[2], bolod)
    site_mark(axs[2], ct, "v")
    scalebar(axs[2], zb)
    axs[2].legend(handles=[Patch(fc="#8c8c8c", label=f"Already usable from Bolod ({ct['overlap_with_bolod']:.0%} of its area)"),
                           Patch(fc="#e08214", label=f"Newly usable land ({ct['new_land_km2']} km², ~{ct['beyond_bolod']:,} residents)")],
                  loc="lower left", fontsize=6.2, framealpha=0.92)
    axs[2].set_title("C. What the contractor site adds (RSRP >= -110 dBm)", fontsize=8.5, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_contractor_overlap.png"))
    plt.close(fig)

    alt_a = alts[0]
    sb = zoom_box((ct["lat"] + alt_a["lat"]) / 2, (ct["lon"] + alt_a["lon"]) / 2, 6.0)
    fig, axs = plt.subplots(1, 2, figsize=(14, 7.0), dpi=180)
    map_panel(axs[0], g, brgys, roads, sb, [ct["raster"]], [bolod, ct],
              f"Contractor {ct['id']}: {ct['overlap_with_bolod']:.0%} overlap with Bolod, ~{ct['beyond_bolod']:,} new residents", ring_site=ct)
    map_panel(axs[1], g, brgys, roads, sb, [alt_a["raster"]], [bolod, alt_a],
              f"{alt_a['id']} {alt_a['name']}, same road: ~{alt_a['beyond_bolod']:,} new residents", ring_site=alt_a)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_side_by_side.png"))
    plt.close(fig)

    for a in alts + build:
        fig, ax = plt.subplots(figsize=(8.2, 7.4), dpi=180)
        map_panel(ax, g, brgys, roads, zoom_box(a["lat"], a["lon"], 5.0), [a["raster"]], [bolod, a],
                  f"{a['id']} - {a['name']}" + (f" ({a['corridor']})" if "corridor" in a else ""), ring_site=a)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f"fig_{a['id'].lower()}.png"))
        plt.close(fig)

    net = np.maximum.reduce([bolod["raster"]] + [s["raster"] for s in build])
    fig, axs = plt.subplots(1, 2, figsize=(15, 6.4), dpi=180)
    map_panel(axs[0], g, brgys, roads, BOX, [np.maximum(bolod["raster"], ct["raster"])], [bolod, ct], "Bolod + contractor site, as proposed")
    map_panel(axs[1], g, brgys, roads, BOX, [net], [bolod] + build, f"Bolod + {len(build)} road-accessible hill sites (N1-N{len(build)})")
    for s in build:
        p = next(x for x in on_air if x["id"] == s["parent"])
        axs[1].plot([p["lon"], s["lon"]], [p["lat"], s["lat"]], color="#0d47a1", lw=0.9, alpha=0.8, zorder=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_network.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 3.8), dpi=200)
    xs = ["Today\n(council)", "Bolod\n(model)"] + [f"+{s['id']}\n{s['name'].replace(' ridge', '').replace(' hill', '').replace('-', '-\n')}" for s in build]
    ys = [total_today, bolod_total] + [s["cum_total"] for s in build]
    ax.bar(xs, ys, color=["#9e9e9e", "#2e7d32"] + ["#1565c0"] * len(build))
    ax.axhline(ct_total, color="#e08214", lw=1.4, ls="--")
    ax.text(len(xs) - 0.6, ct_total - 2600, f"Bolod + contractor site: {ct_total:,} ({ct_total / pops.sum():.0%})", color="#b35c00",
            ha="right", fontsize=7.5, weight="bold", bbox=dict(fc="white", ec="none", pad=1.5), zorder=5)
    for i, v in enumerate(ys):
        ax.text(i, v + 400, f"{v:,}\n{v / pops.sum():.0%}", ha="center", fontsize=6.5)
    ax.set_ylim(0, pops.sum() * 1.08)
    ax.axhline(pops.sum(), color="#555", lw=0.6)
    ax.text(-0.4, pops.sum() * 1.015, f"All residents {pops.sum():,}", fontsize=6.5, color="#555")
    ax.set_ylabel("Residents with usable signal", fontsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_buildout.png"))
    plt.close(fig)

    targets = ["Pinamasingan", "Laurente", "Santa Cruz", "San Pedro"]
    fig, axs = plt.subplots(len(targets), 2, figsize=(13, 2.3 * len(targets)), dpi=180)
    prof = {}
    for row, tname in zip(axs, targets):
        tb = next(b for b in brgys if b["barangay"] == tname)
        tgt = (tb["lat"], tb["lon"])
        blk = terrain_profile(row[0], dem, (ct["lat"], ct["lon"]), tgt, MAST_AGL, 1.5, "#e08214",
                              f"{ct['id']} (contractor) -> {tname}, {dist_m(ct['lat'], ct['lon'], *tgt) / 1000:.1f} km")
        show = min(alts + build, key=lambda s: dist_m(s["lat"], s["lon"], *tgt))
        blk2 = terrain_profile(row[1], dem, (show["lat"], show["lon"]), tgt, MAST_AGL, 1.5, "#1565c0",
                               f"{show['id']} ({show['near']}) -> {tname}, {dist_m(show['lat'], show['lon'], *tgt) / 1000:.1f} km")
        prof[tname] = {"contractor_blocked": blk, "contractor_km": round(dist_m(ct["lat"], ct["lon"], *tgt) / 1000, 1),
                       "alt": show["id"], "alt_blocked": blk2, "alt_km": round(dist_m(show["lat"], show["lon"], *tgt) / 1000, 1)}
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_profiles.png"))
    plt.close(fig)

    links = [(bolod, a, a["mw_mast_m"]) for a in alts] + [(next(x for x in on_air if x["id"] == s["parent"]), s, s["mw_mast_m"])
                                                          for s in build if not s.get("alt")]
    nrow = (len(links) + 2) // 3
    fig, axs = plt.subplots(nrow, 3, figsize=(17, 2.5 * nrow), dpi=160)
    for ax, (p, s, h) in zip(axs.flat, links):
        terrain_profile(ax, dem, (p["lat"], p["lon"]), (s["lat"], s["lon"]), h, h, "#1565c0",
                        f"{p['id']} -> {s['id']} ({s['name'].split(' (')[0]}): {dist_m(p['lat'], p['lon'], s['lat'], s['lon']) / 1000:.1f} km, {h} m",
                        fresnel_ghz=MW_GHZ)
    for ax in list(axs.flat)[len(links):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_mw_profiles.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=200)
    rows = cts + alts
    ax.barh([s["id"] for s in rows][::-1], [s["beyond_bolod"] for s in rows][::-1], color=[s["color"] for s in rows][::-1])
    for i, s in enumerate(rows[::-1]):
        ax.text(s["beyond_bolod"] + 40, i, f"{s['beyond_bolod']:,}", va="center", fontsize=7)
    ax.set_xlabel("Residents of unserved barangays newly given usable signal (RSRP >= -110 dBm, 2020 Census)", fontsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_population_bars.png"))
    plt.close(fig)

    # ------------------------------------------------------------- KMZ
    for f in os.listdir(OUT):
        if f.startswith("cov_") and f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    overlays = []
    allsites = [bolod] + cts + alts + build
    for s in allsites:
        fn = f"cov_{s['id'].lower()}.png"
        overlay_png(np.where(g.land, s["raster"], -200.0), fn)
        overlays.append((f"{s['id']} {s['name']}", fn, s["id"] in ("BOLOD", "CT-2")))
        s["desc"] = (f"Ground {s['ground']:.0f} m ASL, mast {s['agl']:.0f} m (antenna top {s['ground'] + s['agl']:.0f} m ASL). "
                     f"Unserved residents newly covered: {s.get('beyond_bolod', 0):,}.")
    kml_links = [((p["lat"], p["lon"], h - 2), (s["lat"], s["lon"], h - 2),
                  f"MW {p['id']}-{s['id']} {dist_m(p['lat'], p['lon'], s['lat'], s['lon']) / 1000:.1f} km") for p, s, h in links]
    write_kmz(os.path.join(OUT, "san_pascual_review.kmz"), brgys, roads, allsites, kml_links, overlays)
    with open(os.path.join(OUT, "road_proxy.csv"), "w") as f:
        f.write("corridor,lat,lon\n")
        for name, p in roads.paths.items():
            for la_, lo_ in p:
                f.write(f"{name},{la_:.5f},{lo_:.5f}\n")

    # ------------------------------------------------------------- JSON
    keep = ["id", "name", "anchor", "lat", "lon", "ground", "agl", "antenna_top_asl", "reach_unserved", "beyond_bolod",
            "beyond_bolod_indoor", "served_land_km2", "new_land_km2", "overlap_with_bolod", "dist_bolod_km", "bearing",
            "sensitivity", "road_m", "mw_mast_m", "mw_7ghz_mast", "near", "corridor", "parent", "alt", "gain", "cum_total", "mw"]

    def ser(s):
        d = {k: s[k] for k in keep if k in s}
        d["per_barangay_usable"] = {b["barangay"]: round(float(s["cov"][i, 0]), 2) for i, b in enumerate(brgys) if s["cov"][i, 0] >= 0.05}
        d["per_barangay_indoor"] = {b["barangay"]: round(float(s["cov"][i, 1]), 2) for i, b in enumerate(brgys) if s["cov"][i, 1] >= 0.05}
        return d

    out = {
        "calibration": calib,
        "population_total_2020": int(pops.sum()),
        "served_today": total_today,
        "unserved_today": int(pops[unserved].sum()),
        "bolod": ser(bolod) | {"total_model": bolod_total},
        "contractor": [ser(s) for s in cts],
        "contractor_total_with_bolod": ct_total,
        "alternatives": [ser(s) for s in alts],
        "packages": packages,
        "best_package": best_pkg,
        "buildout": [ser(s) for s in build],
        "profiles": prof,
        "pool_size": len(pool),
    }
    with open(os.path.join(OUT, "review.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({"best_package": best_pkg, "profiles": prof, "ct_total": ct_total, "bolod_total": bolod_total}, indent=1))


if __name__ == "__main__":
    main()
