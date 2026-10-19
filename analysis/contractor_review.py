"""Technical review of the contractor's 'deeper Bolod / Pinamasingan Road' site.

Usage:  DEM_DIR=/path/to/hgt python3 contractor_review.py
Outputs (../results/):
    review.json                    all numbers quoted in the docs
    fig_side_by_side.png           contractor vs. ridge alternative coverage
    fig_all_sites.png              existing + contractor + 3 alternatives
    fig_profiles.png               terrain cross-sections showing ridge blocking
    fig_population_bars.png        new unserved population reached per option
    san_pascual_review.kmz         Google Earth Pro package (3D)
"""
import json
import os
import zipfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

import rf
from dem import DEM, bearing, dist_m, mw_profile
from roads import RoadProxy
from site_selection import BOLOD, MAST_AGL, MW_GHZ, candidates, coverage, load_barangays, mw_heights

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

# Contractor site is not yet surveyed: model three plausible spots along the
# Poblacion -> Pinamasingan road inside Bolod, all below the Bolod hill summit.
CONTRACTOR = [
    {"id": "CT-1", "name": "Contractor scenario 1 (road, 1.0 km S of towers)", "lat": 13.1158, "lon": 122.9892},
    {"id": "CT-2", "name": "Contractor scenario 2 (road, 1.7 km S of towers)", "lat": 13.1100, "lon": 122.9908},
    {"id": "CT-3", "name": "Contractor scenario 3 (road, 2.1 km S of towers)", "lat": 13.1067, "lon": 122.9933},
]
MAX_ROAD_SPUR_M = 1000.0
GRID_STEP = 3.0 / 3600.0
BOX = (13.175, 12.955, 122.86, 123.15)      # N, S, W, E


def raster(dem, site):
    n, s, w, e = BOX
    lats = np.arange(n, s, -GRID_STEP)
    lons = np.arange(w, e, GRID_STEP)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    r = rf.rsrp(dem, site, LA.ravel(), LO.ravel()).reshape(LA.shape)
    land = dem.elev(LA, LO) > 0.5
    return r, land, lats, lons


def site_metrics(dem, brgys, pops, unserved, site, bolod_r, land):
    cov = coverage(dem, site, brgys)
    r, _, _, _ = raster(dem, site)
    served = (r >= rf.RSRP_OUTDOOR) & land
    bolod_served = (bolod_r >= rf.RSRP_OUTDOOR) & land
    overlap = float((served & bolod_served).sum() / max(served.sum(), 1))
    cell_km2 = (111.32 * GRID_STEP) ** 2 * np.cos(np.radians(13.06))
    return {
        "cov": cov,
        "raster": r,
        "new_pop_outdoor": int(round((cov[:, 0] * pops * unserved).sum())),
        "new_pop_indoor": int(round((cov[:, 1] * pops * unserved).sum())),
        "served_land_km2": round(float(served.sum() * cell_km2), 1),
        "new_land_km2": round(float((served & ~bolod_served).sum() * cell_km2), 1),
        "overlap_with_bolod": round(overlap, 3),
    }


def hillshade(z):
    gy, gx = np.gradient(z, 92.0, 92.0)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(315), np.radians(45)
    hs = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos(az - aspect)
    return np.clip(hs, 0, 1)


def draw_map(ax, z, lats, lons, brgys, roads, sites, layers, title):
    ext = (lons[0], lons[-1], lats[-1], lats[0])
    sea = np.ma.masked_where(z > 0.5, np.ones_like(z))
    ax.imshow(hillshade(z), cmap="gray", extent=ext, vmin=-0.2, vmax=1.1)
    ax.imshow(sea, cmap=ListedColormap(["#cfe3f3"]), extent=ext)
    for r, color in layers:
        m = np.ma.masked_where(r < rf.RSRP_OUTDOOR, np.ones_like(r))
        ax.imshow(m, cmap=ListedColormap([color]), extent=ext, alpha=0.55)
    for path in roads.paths.values():
        p = np.array(path)
        ax.plot(p[:, 1], p[:, 0], color="#7a4b16", lw=1.1, ls="--", alpha=0.9)
    for b in brgys:
        ax.plot(b["lon"], b["lat"], "o", ms=3 + b["pop"] / 600, mfc="none", mec="#222", mew=0.8)
        ax.text(b["lon"] + 0.002, b["lat"] + 0.002, f"{b['barangay'].split(' (')[0]}\n{b['pop']:,}", fontsize=5.5, color="#111")
    for s in sites:
        ax.plot(s["lon"], s["lat"], marker=s.get("marker", "^"), ms=9, mfc=s["color"], mec="k")
        ax.text(s["lon"] + 0.003, s["lat"] - 0.004, s["id"], fontsize=7, weight="bold")
    ax.set_xlim(lons[0], lons[-1])
    ax.set_ylim(lats[-1], lats[0])
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=6)
    ax.set_aspect(1 / np.cos(np.radians(13.06)))


def profile_plot(ax, dem, a, b, ha, label, color):
    D = dist_m(*a, *b)
    t = np.linspace(0, 1, 300)
    la = a[0] + (b[0] - a[0]) * t
    lo = a[1] + (b[1] - a[1]) * t
    z = dem.elev(la, lo)
    za = float(dem.elev(*a)) + ha
    zb = float(dem.elev(*b)) + 1.5
    ax.fill_between(t * D / 1000, 0, z, color="#9c8a6a", alpha=0.8)
    ax.plot([0, D / 1000], [za, zb], color=color, lw=1.6, label=label)
    ax.plot([0, 0], [za - ha, za], color="k", lw=3)
    blocked = np.any(z[5:-5] > (za + (zb - za) * t[5:-5]))
    return blocked


def kml_color(hex6, alpha="ff"):
    h = hex6.lstrip("#")
    return alpha + h[4:6] + h[2:4] + h[0:2]


def write_kmz(path, brgys, roads, sites, links, overlays):
    pm = []
    styles = []
    for s in sites:
        sid = s["id"].replace(" ", "")
        styles.append(f'<Style id="s{sid}"><IconStyle><color>{kml_color(s["color"])}</color><scale>1.3</scale>'
                      f'<Icon><href>http://maps.google.com/mapfiles/kml/shapes/target.png</href></Icon></IconStyle>'
                      f'<LineStyle><color>{kml_color(s["color"])}</color><width>4</width></LineStyle>'
                      f'<PolyStyle><color>{kml_color(s["color"], "cc")}</color></PolyStyle></Style>')
        # mast as an extruded thin square from ground to mast top
        d = 0.00012
        ring = " ".join(f"{s['lon'] + dx},{s['lat'] + dy},{s['agl']}" for dx, dy in [(-d, -d), (d, -d), (d, d), (-d, d), (-d, -d)])
        pm.append(f'<Placemark><name>{s["id"]} {s["name"]}</name><description>{s.get("desc", "")}</description>'
                  f'<styleUrl>#s{sid}</styleUrl><MultiGeometry><Point><coordinates>{s["lon"]},{s["lat"]},0</coordinates></Point>'
                  f'<Polygon><extrude>1</extrude><altitudeMode>relativeToGround</altitudeMode><outerBoundaryIs><LinearRing>'
                  f'<coordinates>{ring}</coordinates></LinearRing></outerBoundaryIs></Polygon></MultiGeometry></Placemark>')
    bar = []
    for b in brgys:
        d = 0.0012
        h = b["pop"] * 0.08            # 1 m of column per 12.5 residents
        ring = " ".join(f"{b['lon'] + dx},{b['lat'] + dy},{h}" for dx, dy in [(-d, -d), (d, -d), (d, d), (-d, d), (-d, -d)])
        col = "#2e7d32" if b["served"] else "#c62828"
        bar.append(f'<Placemark><name>{b["barangay"]} ({b["pop"]:,})</name>'
                   f'<description>2020 Census: {b["pop"]:,}. Served by Bolod today: {"yes" if b["served"] else "no"}</description>'
                   f'<Style><PolyStyle><color>{kml_color(col, "b0")}</color></PolyStyle></Style>'
                   f'<Polygon><extrude>1</extrude><altitudeMode>relativeToGround</altitudeMode><outerBoundaryIs><LinearRing>'
                   f'<coordinates>{ring}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>')
    rd = []
    for name, p in roads.paths.items():
        coords = " ".join(f"{lo},{la},0" for la, lo in p[::2])
        rd.append(f'<Placemark><name>{name} (terrain-inferred)</name><Style><LineStyle><color>ff1d4f8a</color><width>2</width></LineStyle></Style>'
                  f'<LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark>')
    lk = []
    for a, b, label, ok in links:
        col = "ff00ff00" if ok else "ff0000ff"
        lk.append(f'<Placemark><name>{label}</name><Style><LineStyle><color>{col}</color><width>3</width></LineStyle></Style>'
                  f'<LineString><altitudeMode>relativeToGround</altitudeMode><coordinates>{a[1]},{a[0]},{a[2]} {b[1]},{b[0]},{b[2]}</coordinates></LineString></Placemark>')
    ov = []
    n, s, w, e = BOX
    for name, fname, visible in overlays:
        ov.append(f'<GroundOverlay><name>{name}</name><visibility>{int(visible)}</visibility><color>a0ffffff</color>'
                  f'<Icon><href>{fname}</href></Icon><LatLonBox><north>{n}</north><south>{s}</south><east>{e}</east><west>{w}</west></LatLonBox></GroundOverlay>')
    kml = ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           '<name>San Pascual cell-site review (Sangguniang Bayan)</name>' + "".join(styles)
           + '<Folder><name>Sites</name>' + "".join(pm) + '</Folder>'
           + '<Folder><name>Microwave backhaul to Bolod</name>' + "".join(lk) + '</Folder>'
           + '<Folder><name>Barangay population (3D columns)</name>' + "".join(bar) + '</Folder>'
           + '<Folder><name>Road corridors (terrain-inferred proxy)</name>' + "".join(rd) + '</Folder>'
           + '<Folder><name>Predicted LTE-700 coverage (RSRP >= -110 dBm)</name>' + "".join(ov) + '</Folder>'
           + '</Document></kml>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml)
        for _, fname, _ in overlays:
            zf.write(os.path.join(OUT, fname), fname)


def overlay_png(r, color, fname):
    rgba = np.zeros(r.shape + (4,))
    c = matplotlib.colors.to_rgb(color)
    good = r >= rf.RSRP_INDOOR
    ok = (r >= rf.RSRP_OUTDOOR) & ~good
    rgba[good] = (*c, 0.75)
    rgba[ok] = (*c, 0.4)
    plt.imsave(os.path.join(OUT, fname), rgba)


def main():
    os.makedirs(OUT, exist_ok=True)
    dem = DEM()
    brgys = load_barangays(dem)
    pops = np.array([b["pop"] for b in brgys])
    unserved = np.array([not b["served"] for b in brgys])
    roads = RoadProxy(dem, brgys)
    bolod_ll = (BOLOD["lat"], BOLOD["lon"])

    bolod_r, land, lats, lons = raster(dem, (BOLOD["lat"], BOLOD["lon"], BOLOD["agl"]))
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    zgrid = dem.elev(LA, LO)

    sites = []
    # --- contractor scenarios, with mast-height sensitivity --------------------
    for c in CONTRACTOR:
        c["ground"] = float(dem.elev(c["lat"], c["lon"]))
        c["agl"] = MAST_AGL
        m = site_metrics(dem, brgys, pops, unserved, (c["lat"], c["lon"], MAST_AGL), bolod_r, land)
        c.update(m)
        c["sensitivity"] = {}
        for h in (30, 45, 60):
            cov = coverage(dem, (c["lat"], c["lon"], h), brgys)
            c["sensitivity"][h] = int(round((cov[:, 0] * pops * unserved).sum()))
        c["dist_bolod_km"] = round(dist_m(*bolod_ll, c["lat"], c["lon"]) / 1000, 2)
        c["ground_below_bolod_m"] = round(float(dem.elev(*bolod_ll)) - c["ground"], 0)
        c["mw"] = mw_profile(dem, bolod_ll, (c["lat"], c["lon"]), 40, MAST_AGL, MW_GHZ)
        c["color"], c["marker"] = "#ff8f00", "v"
        sites.append(c)
        print(c["id"], c["ground"], c["new_pop_outdoor"], c["new_pop_indoor"], c["overlap_with_bolod"], c["sensitivity"])

    # --- road-constrained alternatives -----------------------------------------
    cands = candidates(dem)
    pool = []
    for c in cands:
        c["road_m"] = roads.dist_to_road_m(c["lat"], c["lon"])
        if c["road_m"] > MAX_ROAD_SPUR_M:
            continue
        h, _ = mw_heights(dem, bolod_ll, (c["lat"], c["lon"]), MW_GHZ)
        if h is None or h > 45:
            continue
        c["mw_mast_m"] = h
        c["cov"] = coverage(dem, (c["lat"], c["lon"], MAST_AGL), brgys)
        pool.append(c)
    print(len(pool), "road-accessible candidates with Bolod LoS")
    bolod_cov2 = coverage(dem, (BOLOD["lat"], BOLOD["lon"], BOLOD["agl"]), brgys)
    bolod_cov, bolod_cov_in = bolod_cov2[:, 0], bolod_cov2[:, 1]

    def beyond_bolod(c, col=0):
        """Unserved residents this site adds on top of Bolod's *modelled* fringe."""
        ref = bolod_cov if col == 0 else bolod_cov_in
        return float((np.maximum(c["cov"][:, col] - ref, 0) * pops * unserved).sum())

    # One compromise ridge per road corridor the contractor could follow.
    kx = 111_320.0 * np.cos(np.radians(13.06))

    def corridor_best(name, lat_min=-90, lat_max=90):
        P = np.array(roads.paths[name])
        P = P[(P[:, 0] >= lat_min) & (P[:, 0] <= lat_max)]
        ok = [c for c in pool
              if np.min(np.hypot((P[:, 1] - c["lon"]) * kx, (P[:, 0] - c["lat"]) * 111_320.0)) <= MAX_ROAD_SPUR_M]
        return max(ok, key=beyond_bolod)

    alts = [
        corridor_best("Poblacion-Pinamasingan-Quintina Rd", lat_min=13.08),        # same road, further out
        corridor_best("Inland Pinamasingan-San Pedro-Mapanique"),
        corridor_best("North coast to Laurente"),
        corridor_best("West coast road", lat_min=13.05),                            # San Rafael / Santa Cruz
    ]
    labels = ["same Poblacion-Pinamasingan road, further out", "inland Pinamasingan-San Pedro-Mapanique road",
              "north-coast road via Laurente", "west-coast road via San Rafael"]
    names = ["ALT-A", "ALT-B", "ALT-C", "ALT-D"]
    colors = ["#1565c0", "#6a1b9a", "#00897b", "#ad1457"]
    near = lambda la, lo: min(brgys, key=lambda b: dist_m(la, lo, b["lat"], b["lon"]))["barangay"]
    for c in alts + sites:               # alternatives + contractor scenarios
        c["beyond_bolod"] = int(round(beyond_bolod(c)))
        c["beyond_bolod_indoor"] = int(round(beyond_bolod(c, 1)))
    for c, nm, col, lab in zip(alts, names, colors, labels):
        c["near"] = near(c["lat"], c["lon"])
        c["id"], c["color"], c["agl"] = nm, col, MAST_AGL
        c["name"] = f"{c['near']} ridge ({lab})"
        c.update(site_metrics(dem, brgys, pops, unserved, (c["lat"], c["lon"], MAST_AGL), bolod_r, land))
        c["dist_bolod_km"] = round(dist_m(*bolod_ll, c["lat"], c["lon"]) / 1000, 2)
        c["bearing"] = round(bearing(*bolod_ll, c["lat"], c["lon"]), 0)
        c["mw"] = mw_profile(dem, bolod_ll, (c["lat"], c["lon"]), c["mw_mast_m"], c["mw_mast_m"], MW_GHZ)
        c["mw_7ghz_mast"] = mw_heights(dem, bolod_ll, (c["lat"], c["lon"]), 7.0)[0]
        sites.append(c)
        print(nm, c["lat"], c["lon"], c["ground"], c["near"], round(c["road_m"]), c["new_pop_outdoor"], c["beyond_bolod"], c["overlap_with_bolod"], c["mw_mast_m"])
    # best 1/2/3-site packages from the road-accessible alternatives
    from itertools import combinations
    base = np.where(unserved, 0.0, 1.0)
    packages = []
    for k in (1, 2, 3):
        for combo in combinations(alts, k):
            cov = np.maximum.reduce([base] + [c["cov"][:, 0] for c in combo])
            net = np.maximum.reduce([bolod_cov] + [c["cov"][:, 0] for c in combo]) - bolod_cov
            packages.append({"sites": [c["id"] for c in combo], "total_outdoor": int(round(cov @ pops)),
                             "new_outdoor": int(round((cov - base) @ pops)),
                             "beyond_bolod": int(round((net * pops * unserved).sum()))})
    packages.sort(key=lambda p: (len(p["sites"]), -p["new_outdoor"]))
    best_pkg = {k: max((p for p in packages if len(p["sites"]) == k), key=lambda p: p["new_outdoor"]) for k in (1, 2, 3)}
    for c in sites:
        if c["id"].startswith("CT"):
            cov = np.maximum(base, c["cov"][:, 0])
            c["total_with_bolod"] = int(round(cov @ pops))
    print("packages", best_pkg)

    # --- figures -----------------------------------------------------------------
    bolod_site = {"id": "BOLOD", "name": BOLOD["name"], "lat": BOLOD["lat"], "lon": BOLOD["lon"], "agl": 40, "color": "#2e7d32"}
    ct = sites[1]
    alt = alts[0]                       # same road as the contractor, further out
    fig, axs = plt.subplots(1, 2, figsize=(15, 6.6), dpi=170)
    draw_map(axs[0], zgrid, lats, lons, brgys, roads, [bolod_site, ct], [(bolod_r, "#2e7d32"), (ct["raster"], "#ff8f00")],
             f"Contractor site {ct['id']} (orange) on top of existing Bolod (green)\n"
             f"{ct['overlap_with_bolod']:.0%} of its footprint already served by Bolod - adds ~{ct['beyond_bolod']:,} residents beyond Bolod")
    draw_map(axs[1], zgrid, lats, lons, brgys, roads, [bolod_site, alt], [(bolod_r, "#2e7d32"), (alt["raster"], alt["color"])],
             f"{alt['id']} - {alt['name']} (blue)\n"
             f"{alt['overlap_with_bolod']:.0%} overlap - adds ~{alt['beyond_bolod']:,} residents beyond Bolod")
    fig.suptitle("San Pascual, Masbate - predicted LTE-700 outdoor coverage (RSRP >= -110 dBm), 40 m masts, SRTM 30 m terrain.  Circles = barangay centres (2020 pop.); dashed = terrain-inferred road corridors", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_side_by_side.png"))
    plt.close(fig)

    fig, axs = plt.subplots(2, 4, figsize=(21, 10), dpi=140)
    panels = [(bolod_site, bolod_r)] + [(s, s["raster"]) for s in sites if s["id"] in ("CT-2",)] + [(a, a["raster"]) for a in alts]
    for ax, (s, r) in zip(axs.flat, panels):
        draw_map(ax, zgrid, lats, lons, brgys, roads, [bolod_site, s], [(r, s["color"])], f"{s['id']}: {s['name']}")
    by_id = {a["id"]: a for a in alts}
    pk = best_pkg[2]["sites"]
    comb = np.maximum.reduce([bolod_r] + [by_id[i]["raster"] for i in pk])
    draw_map(axs.flat[6], zgrid, lats, lons, brgys, roads, [bolod_site] + [by_id[i] for i in pk], [(comb, "#1565c0")],
             f"Bolod + {' + '.join(pk)} (best 2-site package)")
    comb_ct = np.maximum(bolod_r, ct["raster"])
    draw_map(axs.flat[7], zgrid, lats, lons, brgys, roads, [bolod_site, ct], [(comb_ct, "#ff8f00")], "Bolod + contractor CT-2 (as proposed)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_all_sites.png"))
    plt.close(fig)

    targets = ["San Pedro", "Pinamasingan", "Mapanique", "Ki-Romero"]
    fig, axs = plt.subplots(len(targets), 2, figsize=(14, 2.4 * len(targets)), dpi=150, sharey=True)
    prof = {}
    for row, tname in zip(axs, targets):
        tb = next(b for b in brgys if b["barangay"] == tname)
        tgt = (tb["lat"], tb["lon"])
        prof[tname] = {}
        clear_alts = []
        for a in alts:
            t = np.linspace(0, 1, 300)[5:-5]
            za = float(dem.elev(a["lat"], a["lon"])) + MAST_AGL
            zb = float(dem.elev(*tgt)) + 1.5
            zt = dem.elev(a["lat"] + (tgt[0] - a["lat"]) * t, a["lon"] + (tgt[1] - a["lon"]) * t)
            blocked = bool(np.any(zt > za + (zb - za) * t))
            prof[tname][a["id"]] = {"blocked": blocked, "km": round(dist_m(a["lat"], a["lon"], *tgt) / 1000, 1)}
            if not blocked:
                clear_alts.append(a)
        show = min(clear_alts or alts, key=lambda a: dist_m(a["lat"], a["lon"], *tgt))
        for ax, s_, col in ((row[0], ct, "#ff8f00"), (row[1], show, show["color"])):
            blk = profile_plot(ax, dem, (s_["lat"], s_["lon"]), tgt, MAST_AGL, "", col)
            D = dist_m(s_["lat"], s_["lon"], *tgt)
            ax.set_title(f"{s_['id']} -> {tname} ({D / 1000:.1f} km): {'BLOCKED by ridge' if blk else 'clear line of sight'}",
                         fontsize=8, color="#b71c1c" if blk else "#1b5e20")
            ax.tick_params(labelsize=6)
            if s_ is ct:
                prof[tname]["contractor_blocked"] = bool(blk)
        row[0].set_ylabel("m above sea", fontsize=7)
    axs[-1][0].set_xlabel("km from contractor site CT-2", fontsize=7)
    axs[-1][1].set_xlabel("km from ridge alternative", fontsize=7)
    fig.suptitle("Terrain cross-sections: contractor road site vs. ridge alternative (SRTM 30 m, 40 m mast, 1.5 m handset)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_profiles.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=160)
    labels = [s["id"] for s in sites]
    vals = [s["beyond_bolod"] for s in sites]
    ax.barh(labels[::-1], vals[::-1], color=[s["color"] for s in sites][::-1])
    for i, v in enumerate(vals[::-1]):
        ax.text(v + 150, i, f"{v:,}", va="center", fontsize=8)
    ax.set_xlabel("Net new residents beyond the existing Bolod signal (outdoor RSRP >= -110 dBm, 2020 Census)", fontsize=8)
    ax.set_title(f"Unserved residents each tower adds (of {int(pops[unserved].sum()):,} currently unserved)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_population_bars.png"))
    plt.close(fig)

    # --- KMZ ---------------------------------------------------------------------
    overlays = [("Existing Bolod", "cov_bolod.png", True)]
    overlay_png(bolod_r, "#2e7d32", "cov_bolod.png")
    for s in sites:
        fn = f"cov_{s['id'].lower()}.png"
        overlay_png(s["raster"], s["color"], fn)
        overlays.append((f"{s['id']} {s['name']}", fn, s["id"] in ("CT-2",)))
    for s in sites:
        s["desc"] = (f"Ground {s['ground']:.0f} m ASL, mast {s['agl']:.0f} m. New unserved residents reached (outdoor): "
                     f"{s['new_pop_outdoor']:,}. Footprint overlap with Bolod: {s['overlap_with_bolod']:.0%}.")
    links = []
    bz = float(dem.elev(*bolod_ll))
    for s in sites:
        ok = s["mw"]["min_f1"] >= 0.6
        links.append(((BOLOD["lat"], BOLOD["lon"], 38), (s["lat"], s["lon"], s["agl"] - 2),
                      f"MW {s['id']} - Bolod {s['mw']['dist_km']:.1f} km, clearance {s['mw']['min_f1']:.1f} F1 @15 GHz", ok))
    write_kmz(os.path.join(OUT, "san_pascual_review.kmz"), brgys, roads, [bolod_site] + sites, links, overlays)
    with open(os.path.join(OUT, "road_proxy.csv"), "w") as f:
        f.write("corridor,lat,lon\n")
        for name, p in roads.paths.items():
            for la, lo in p:
                f.write(f"{name},{la:.5f},{lo:.5f}\n")

    # --- JSON ----------------------------------------------------------------------
    def ser(s):
        keep = ["id", "name", "lat", "lon", "ground", "agl", "new_pop_outdoor", "new_pop_indoor", "served_land_km2",
                "new_land_km2", "overlap_with_bolod", "dist_bolod_km", "sensitivity", "ground_below_bolod_m", "road_m",
                "mw_mast_m", "mw_7ghz_mast", "beyond_bolod", "beyond_bolod_indoor", "total_with_bolod", "near", "bearing", "mw"]
        d = {k: s[k] for k in keep if k in s}
        d["per_barangay_outdoor"] = {b["barangay"]: round(float(s["cov"][i, 0]), 2) for i, b in enumerate(brgys)}
        return d

    out = {
        "bolod": {**BOLOD, "ground": bz},
        "population_total_2020": int(pops.sum()),
        "served_today": int(pops[~unserved].sum()),
        "unserved_today": int(pops[unserved].sum()),
        "contractor": [ser(s) for s in sites if s["id"].startswith("CT")],
        "alternatives": [ser(s) for s in alts],
        "packages": packages,
        "best_package": best_pkg,
        "profiles": prof,
        "pool_size": len(pool),
    }
    with open(os.path.join(OUT, "review.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({"best_package": best_pkg, "profiles": prof}, indent=1, default=float))


if __name__ == "__main__":
    main()
