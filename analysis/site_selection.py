"""Rank hilltop candidates in San Pascual for the next macro site(s).

Usage:  DEM_DIR=/path/to/hgt python3 site_selection.py
Writes ../results/candidates.csv and ../results/selection.json
"""
import csv
import json
import os

import numpy as np
from scipy.ndimage import maximum_filter

import rf
from dem import DEM, bearing, dist_m, mw_profile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

# Existing site: SRTM summit of the Bolod hill ridge ~1 km ESE of the poblacion.
# Replace with surveyed coordinates of the two towers when available.
BOLOD = {"name": "Bolod hill (existing)", "lat": 13.1250, "lon": 122.9886, "agl": 40.0}
MAST_AGL = 40.0          # proposed greenfield tower
MW_GHZ = 15.0            # common licensed MW band in PH; 7/8 GHz checked as fallback
MIN_SEPARATION_KM = 3.0


def load_barangays(dem):
    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "data", "barangays.csv"))))
    for b in rows:
        b["lat"], b["lon"], b["pop"] = float(b["lat"]), float(b["lon"]), int(b["pop_2020"])
        b["served"] = b["bolod_served_today"] == "yes"
        b["pts"] = rf.settlement_points(dem, b["lat"], b["lon"])
    return rows


def coverage(dem, site, brgys):
    """Per-barangay (outdoor_fraction, indoor_fraction) for a site tuple."""
    out = []
    for b in brgys:
        r = rf.rsrp(dem, site, *b["pts"])
        out.append((float(np.mean(r >= rf.RSRP_OUTDOOR)), float(np.mean(r >= rf.RSRP_INDOOR))))
    return np.array(out)


def candidates(dem):
    z = dem.z
    r0, c0 = map(int, dem.rc(13.17, 122.93))
    r1, c1 = map(int, dem.rc(12.96, 123.14))
    w = z[r0:r1, c0:c1]
    peaks = np.argwhere((w == maximum_filter(w, size=21)) & (w >= 60))
    seen, out = set(), []
    for r, c in peaks:
        la, lo = dem.latlon(r0 + r, c0 + c)
        key = (round(la, 3), round(lo, 3))
        if key in seen:
            continue
        seen.add(key)
        out.append({"lat": round(la, 5), "lon": round(lo, 5), "ground": float(w[r, c])})
    return out


def mw_heights(dem, a, b, f_ghz):
    """Smallest equal mast height (m) giving >=0.6 F1 @k=4/3 and >=0.3 F1 @k=2/3."""
    for h in range(15, 76, 5):
        p43 = mw_profile(dem, a, b, h, h, f_ghz, k=4 / 3)
        p23 = mw_profile(dem, a, b, h, h, f_ghz, k=2 / 3)
        if p43["min_f1"] >= 0.6 and p23["min_f1"] >= 0.3:
            return h, p43
    return None, mw_profile(dem, a, b, 40, 40, f_ghz)


def nearest_barangay(brgys, lat, lon):
    return min(brgys, key=lambda b: dist_m(lat, lon, b["lat"], b["lon"]))["barangay"]


def main():
    os.makedirs(OUT, exist_ok=True)
    dem = DEM()
    brgys = load_barangays(dem)
    pops = np.array([b["pop"] for b in brgys])
    unserved = np.array([not b["served"] for b in brgys])
    bolod_site = (BOLOD["lat"], BOLOD["lon"], BOLOD["agl"])
    bolod_cov = coverage(dem, bolod_site, brgys)

    cands = candidates(dem)
    print(f"{len(cands)} hilltop candidates")
    bolod_ll = (BOLOD["lat"], BOLOD["lon"])
    for i, c in enumerate(cands):
        cov = coverage(dem, (c["lat"], c["lon"], MAST_AGL), brgys)
        c["cov"] = cov
        c["pop_out"] = int(round((cov[:, 0] * pops * unserved).sum()))
        c["pop_in"] = int(round((cov[:, 1] * pops * unserved).sum()))
        c["dist_bolod_km"] = round(dist_m(*bolod_ll, c["lat"], c["lon"]) / 1000, 2)
        h, prof = mw_heights(dem, bolod_ll, (c["lat"], c["lon"]), MW_GHZ)
        c["mw_mast_m"] = h
        c["mw_clear_f1_at40"] = round(mw_profile(dem, bolod_ll, (c["lat"], c["lon"]), 40, 40, MW_GHZ)["min_f1"], 2)
        c["near"] = nearest_barangay(brgys, c["lat"], c["lon"])
        if i % 20 == 0:
            print(f"  {i}/{len(cands)}")

    with open(os.path.join(OUT, "candidates.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lat", "lon", "ground_m", "nearest_barangay", "dist_bolod_km",
                    "pop_outdoor_new", "pop_indoor_new", "mw_equal_mast_m_15GHz", "mw_clear_F1_at_40m"])
        for c in sorted(cands, key=lambda c: -c["pop_out"]):
            w.writerow([c["lat"], c["lon"], c["ground"], c["near"], c["dist_bolod_km"],
                        c["pop_out"], c["pop_in"], c["mw_mast_m"], c["mw_clear_f1_at40"]])

    # Greedy build-out: every pick must have its own clear MW path to Bolod
    # with masts <= 45 m, and be >= MIN_SEPARATION_KM from earlier picks.
    best_out = np.where(unserved, 0.0, 1.0)   # Bolod-served barangays count as covered
    best_in = best_out.copy()
    picks = []
    for _ in range(3):
        def gain(c):
            if c["mw_mast_m"] is None or c["mw_mast_m"] > 45:
                return -1
            if any(dist_m(c["lat"], c["lon"], p["lat"], p["lon"]) < MIN_SEPARATION_KM * 1000 for p in picks):
                return -1
            return (np.maximum(best_out, c["cov"][:, 0]) - best_out) @ pops
        c = max(cands, key=gain)
        g_out = (np.maximum(best_out, c["cov"][:, 0]) - best_out) @ pops
        g_in = (np.maximum(best_in, c["cov"][:, 1]) - best_in) @ pops
        best_out = np.maximum(best_out, c["cov"][:, 0])
        best_in = np.maximum(best_in, c["cov"][:, 1])
        c["inc_out"], c["inc_in"] = int(round(g_out)), int(round(g_in))
        picks.append(c)

    def ser(c):
        prof = mw_profile(dem, bolod_ll, (c["lat"], c["lon"]), c["mw_mast_m"] or 40, c["mw_mast_m"] or 40, MW_GHZ)
        return {
            "lat": c["lat"], "lon": c["lon"], "ground_m": c["ground"], "near": c["near"],
            "dist_bolod_km": c["dist_bolod_km"],
            "bearing_from_bolod": round(bearing(*bolod_ll, c["lat"], c["lon"]), 1),
            "standalone_pop_outdoor": c["pop_out"], "standalone_pop_indoor": c["pop_in"],
            "incremental_pop_outdoor": c.get("inc_out"), "incremental_pop_indoor": c.get("inc_in"),
            "mw_equal_mast_m": c["mw_mast_m"], "mw_profile": prof,
            "per_barangay": {b["barangay"]: [round(x, 2) for x in c["cov"][i]] for i, b in enumerate(brgys)},
        }

    result = {
        "assumptions": {
            "band_MHz": rf.F_MHZ, "eirp_per_RE_dBm": rf.EIRP_RE_DBM, "clutter_dB": rf.CLUTTER_DB,
            "rsrp_outdoor_dBm": rf.RSRP_OUTDOOR, "rsrp_indoor_dBm": rf.RSRP_INDOOR,
            "max_land_km": rf.MAX_LAND_KM, "mast_agl_m": MAST_AGL, "mw_GHz": MW_GHZ,
        },
        "bolod": {**BOLOD, "per_barangay": {b["barangay"]: [round(x, 2) for x in bolod_cov[i]] for i, b in enumerate(brgys)}},
        "population_total_2020": int(pops.sum()),
        "population_served_today": int(pops[~unserved].sum()),
        "picks": [ser(c) for c in picks],
        "network_after_3_outdoor": int(round(best_out @ pops)),
        "network_after_3_indoor": int(round(best_in @ pops)),
        "top_standalone": [ser(c) for c in sorted(cands, key=lambda c: -c["pop_out"])[:12]],
    }
    with open(os.path.join(OUT, "selection.json"), "w") as f:
        json.dump(result, f, indent=1)
    for p in result["picks"]:
        print(json.dumps({k: v for k, v in p.items() if k != "per_barangay"}))
    print("after 3:", result["network_after_3_outdoor"], result["network_after_3_indoor"])


if __name__ == "__main__":
    main()
