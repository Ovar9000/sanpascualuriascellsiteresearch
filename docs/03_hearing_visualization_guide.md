# 3. Visualizer Proof for the Sanggunian — Side‑by‑Side in Under 10 Minutes

Goal: on the hearing projector, show **the contractor's Pinamasingan Road blind spots** next to **a ridge site**, live, and let councilors fly over their own barangays.

You have three layers of proof, from zero‑effort to fully independent:

| Level | Tool | Prep time | What it proves |
|---|---|---|---|
| 0 | The PNGs in `results/` | none | Pre‑rendered side‑by‑side maps and terrain cross‑sections |
| 1 | **Google Earth Pro + our KMZ** | 5 min | 3D flyover: towers, population columns, coverage layers, microwave links |
| 2 | **Google Earth Pro Viewshed** | 10 min | Google's own terrain, independent of our model, shows what each mast can "see" |
| 3 | **HeyWhatsThat** | 15 min | Third‑party line‑of‑sight "cloak" maps and a Fresnel‑zone path profiler |
| 4 | **CloudRF** | 20 min | A real RF (Longley‑Rice) RSRP heat‑map, the same kind of map you will demand from the contractor |

> **Tip:** screen interfaces change. Menu names below were current at writing. If one has moved, look for the same function under a similar name.

---

## Level 1 — Google Earth Pro with the review KMZ (3D flyover)

1. Install **Google Earth Pro** (desktop, free).
2. **File → Open →** `results/san_pascual_review.kmz`.
3. **Tools → Options → 3D View → Elevation Exaggeration = 2.0**, then OK. Burias hills are only 100–200 m high, so ×2 makes the ridges obvious to a lay audience.
4. In the **Places** panel you will see five folders:
   - **Sites:** Bolod (green), contractor CT‑1/2/3 (orange), ALT‑A–D. Each is a coloured mast drawn at its true height.
   - **Microwave backhaul to Bolod:** green line = clear path.
   - **Barangay population (3D columns):** red = unserved, green = served. Column height ∝ residents (1 m per 12.5 people).
   - **Road corridors:** terrain‑inferred; replace with real traces if you have them.
   - **Predicted LTE‑700 coverage:** one overlay per site. Strong colour = indoor‑grade, pale = outdoor only.
5. **Build the side‑by‑side story with two saved views:**
   - Tick **Existing Bolod** + **CT‑2**, untick the rest. Tilt (shift + drag) to look south from above Bolod. Right‑click **Sites** → **Snapshot View**.
   - Tick **Existing Bolod** + **ALT‑A** (or ALT‑B), untick CT‑2. Same camera.
   - During the hearing, toggle between the two checkbox sets. The orange layer sits on top of the green; the blue layer spills over the ridges into the red population columns.
6. **Tour (optional):** **Add → Tour**, press record, then fly Bolod → CT‑2 → San Pedro → Mapanique → ALT‑B. Save it in *My Places* so it plays at one click.

## Level 2 — Google Earth Pro Viewshed (independent of our model)

Google Earth's built‑in viewshed uses Google's terrain, not ours, so it is an independent check.

1. **Add → Placemark** at the contractor site (CT‑2: `13.1100, 122.9908`). Name it "Contractor".
2. In the placemark dialog, open the **Altitude** tab. Set **40 m, "Relative to ground"** (the antenna height). Click OK.
3. Right‑click the placemark → **Show Viewshed**. Green is ground the antenna can see directly.
4. Screenshot it (**File → Save → Save Image**), then **Exit viewshed**.
5. Repeat for a ridge site, e.g. **ALT‑A `13.08722, 123.03167`** or **ALT‑B `13.0075, 123.05556`**, also 40 m relative to ground.
6. Repeat for **Bolod hill `13.1250, 122.9886`**. The contractor's green area sits almost entirely inside Bolod's.
7. **Ridge proof:** **Add → Path**, click CT‑2 then San Pedro (`13.0564, 122.9994`). Save, right‑click the path → **Show Elevation Profile**. The profile rises above the start point, so the ridge blocks the path. Do the same from ALT‑D or ALT‑A to compare.

*Viewshed is pure line of sight. It does not include radio diffraction or signal strength, which is what Level 4 adds. It is still the clearest picture for councilors.*

## Level 3 — HeyWhatsThat (line‑of‑sight "cloak" and microwave path)

1. Go to **heywhatsthat.com** and choose **New Panorama**.
2. Enter the contractor site coordinates and **height above ground = 40 m** (check the units). Submit. Processing can take several minutes, so do this **before** the hearing.
3. When ready, open the map view and turn on the **visibility cloak**. Areas the mast cannot see are shaded.
4. Repeat for ALT‑A or ALT‑B. Put the two browser tabs side by side (Windows: Win + ← / Win + →).
5. **Microwave proof:** open HeyWhatsThat's **Path Profiler**. Enter Bolod (`13.1250, 122.9886`, 38 m) to ALT‑B (`13.0075, 123.0556`, 35 m) at the planned frequency. The Fresnel zone should clear the terrain. This shows the council the backhaul objection does not hold.

## Level 4 — CloudRF (signal‑strength heat‑map)

CloudRF produces the same kind of RSRP propagation map you will ask the contractor to submit.

1. Create a free account at **cloudrf.com** and open the web interface. The free tier has resolution and radius limits, which are enough for a 15 km study.
2. Choose an **area / coverage** calculation and set:
   - **Site:** lat/lon of CT‑2; **antenna height 40 m AGL**
   - **Frequency:** 758 MHz (LTE Band 28) — or 850 MHz if the operator uses Band 5
   - **Power:** 40 W (46 dBm); **antenna gain** ~16.5 dBi; feeder loss ~1 dB
   - **Receiver:** 1.5 m height, 0 dBi
   - **Model:** **ITM / Longley‑Rice** (or ITU‑R P.1812), environment **rural / vegetated**
   - **Radius:** 15 km; **resolution:** the finest your tier allows (30–90 m)
   - **Output:** **dBm**, with the legend set to show **−100 dBm (indoor)** and **−110 dBm (outdoor)** contours
3. Run it, then **export KMZ** and open it in Google Earth Pro over our population columns.
4. Repeat for ALT‑A / ALT‑B and for Bolod hill. Use the **"best server"** or **multi‑site** feature if your plan includes it to show Bolod + CT‑2 against Bolod + ALT‑B.
5. Use the **point‑to‑point / path** tool for the Bolod ↔ ridge microwave links.

## 3‑minute hearing script

1. *(PNG: `fig_population_bars.png`)* "36,021 of our 44,449 constituents have no reliable signal. This bar shows how many each tower would add."
2. *(Google Earth: Bolod + CT‑2)* "The orange is the contractor's tower. It sits almost entirely on top of the green we already have. Its antennas would be 46 m lower than the existing ones, 1.7 km away."
3. *(Path elevation profile, CT‑2 → San Pedro)* "Here is the ridge between that site and San Pedro, Pinamasingan and Mapanique. The signal cannot get over it."
4. *(Google Earth: Bolod + ALT‑A or ALT‑B)* "Same road, a few kilometres further, on the ridge. The blue covers the red columns, and the microwave link to Bolod is clear."
5. "We are not saying no to a tower. We are saying build it where our people are."

## Projection checklist

- [ ] Laptop with Google Earth Pro, the KMZ, and **offline cache**: fly over the whole municipality once beforehand. Hearing‑hall Wi‑Fi is unreliable.
- [ ] Saved views or a tour in *My Places*
- [ ] HeyWhatsThat / CloudRF screenshots saved locally as backup
- [ ] `fig_side_by_side.png`, `fig_profiles.png`, `fig_population_bars.png` on a USB stick
- [ ] Printed one‑page matrix (section 2.3) for each councilor
