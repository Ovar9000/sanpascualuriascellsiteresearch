# San Pascual (Burias Island, Masbate) — Cell‑Site Technical Review for the Sangguniang Bayan

Independent technical review supporting the Sangguniang Bayan's decision on a **Resolution of No Objection (RONO)** for a proposed telecom tower in **deeper Barangay Bolod near the Pinamasingan Road**.

**▶ Slide deck (29 slides): [`slides/San_Pascual_Cell_Site_Review.pdf`](slides/San_Pascual_Cell_Site_Review.pdf)**

## Revision 2 — coverage model recalibrated

The first maps over‑predicted range, showed Bolod reaching Laurente, and drew coverage as a single flat fill. The model is now **calibrated to the council's field facts**:

| Field fact | Model |
|---|---|
| Bolod serves Bolod, Terraplin, Nazareno, Busing | 87 %, 77 %, 55 %, 64 % of settled area usable |
| Bolod does not reach Laurente | 1 % |
| Usable signal ends at 3–4 km | median land range 3.2 km |

Maps are now graded **RSRP heatmaps**, on a contour basemap with 1–4 km range rings:

| Class | RSRP |
|---|---|
| Excellent | ≥ −80 dBm |
| Strong | −80 to −90 dBm |
| Good indoor | −90 to −100 dBm |
| Outdoor only | −100 to −110 dBm |
| Edge | −110 to −120 dBm |

## Bottom line

| | Contractor's site (deeper Bolod / Pinamasingan Rd) | Road‑accessible ridge sites |
|---|---|---|
| Antenna top | 100–113 m ASL (35–48 m **below** existing Bolod antennas, 1–2 km away) | 112–193 m ASL, next to unserved barangays |
| Coverage already covered by Bolod | **75–94 %** | 0–22 % |
| Unserved residents added | **0** (all scenarios, 30–45 m mast) | **2,293 – 4,314 per site** |
| Road access | On the road | 43–985 m spur |
| Microwave to Bolod | Trivial | Clear: 2.6–15 km, 15–40 m masts |

- **36,021 of 44,449 residents (81 %)** live in the 18 barangays the Bolod towers cannot reach.
- Signal travels only 3–4 km here, so **a tower must stand near the people it serves**.
- **Phase 1:** the Malaking Ilog–Mapanique ridge (ALT‑D) plus the San Rafael–Santa Cruz ridge (ALT‑C) add **8,403 residents**, taking service from **20 % to 39 %**.
- **Eight‑site plan:** an eight‑site road‑accessible plan reaches **71 %**. Bolod plus the contractor's site stays at **20 %**.

**Recommendation.** No objection *subject to* a ridge site:

- **Preferred:** ALT‑C / ALT‑D.
- **Minimum, on the contractor's own road:** ALT‑A Pinamasingan ridge or ALT‑E Cueva ridge.
- **Fallback:** treat the deeper‑Bolod site as capacity‑only, tied to a binding, time‑bound ridge‑site commitment.
- **If the goal is only a new operator or more capacity:** insist on co‑location on the existing towers.

> ⚖️ **Legal footing:** EO 32 (s. 2023) lists Sanggunian resolutions among requirements that are no longer prerequisites for tower permits. Confirm the RONO's status with the Municipal Legal Officer and frame the conditions as an MOA (see [doc 4 §4.0](docs/04_sanggunian_hearing_strategy.md)).

## Contents

| # | Document | What it gives you |
|---|---|---|
| ▶ | [Slide deck PDF](slides/San_Pascual_Cell_Site_Review.pdf) | 29 slides covering calibration, contractor critique, ridge sites, network plan, matrix, questions, conditions and method |
| 1 | [Coverage Overlap & Terrain Critique](docs/01_coverage_overlap_terrain_critique.md) | Why the contractor's site is redundant and cannot clear the ridges |
| 2 | [Road‑Accessible Alternatives + Network Plan](docs/02_road_accessible_alternatives.md) | ALT‑A to ALT‑E, the N1–N8 build‑out, board matrix, commercial lens |
| 3 | [Hearing Visualization Guide](docs/03_hearing_visualization_guide.md) | Google Earth Pro (KMZ + Viewshed), HeyWhatsThat and CloudRF steps, plus a 3‑minute script |
| 4 | [Hearing Strategy & RONO Conditions](docs/04_sanggunian_hearing_strategy.md) | 5 questions, the conditions list, and a draft operative clause |
| 5 | [Methodology & Limitations](docs/05_methodology_and_limitations.md) | Calibrated model, revision history, caveats, how to re‑run |

**Ready‑to‑project files** (`results/`):

- `san_pascual_review.kmz` — Google Earth Pro: masts, population columns, RSRP overlays, microwave links
- `fig_calibration_bolod.png`, `fig_contractor_overlap.png`, `fig_side_by_side.png`, `fig_profiles.png`
- `fig_alt-a.png` … `fig_alt-e.png`, `fig_network.png`, `fig_buildout.png`, `fig_mw_profiles.png`
- `review.json`, `candidates.csv`, `selection.json` — every number quoted

## Key coordinates (WGS84)

| ID | Site | Lat | Lon |
|---|---|---|---|
| BOLOD | Existing towers, Bolod hill (SRTM summit; confirm by survey) | 13.1250 | 122.9886 |
| CT‑2 | Contractor scenario (deeper Bolod, Pinamasingan Rd; confirm from application) | 13.1100 | 122.9908 |
| ALT‑A | Pinamasingan ridge, same road further out | 13.0875 | 123.0317 |
| ALT‑B | Laurente–Nazareno ridge, north‑coast road | 13.1414 | 123.0061 |
| ALT‑C | San Rafael–Santa Cruz ridge, west‑coast road | 13.0697 | 122.9636 |
| ALT‑D | Malaking Ilog–Mapanique ridge, inland road | 13.0075 | 123.0556 |
| ALT‑E | Cueva ridge, Poblacion–Quintina road | 13.1017 | 123.0578 |

## Reproduce / update

```bash
pip install -r analysis/requirements.txt
bash analysis/fetch_dem.sh
python3 analysis/site_selection.py      # unconstrained hilltop benchmark
python3 analysis/contractor_review.py   # contractor vs. ridges, network plan, figures, KMZ
bash slides/make_pdf.sh                 # rebuild the slide PDF from results/review.json
```

When the application's exact coordinates, the surveyed Bolod tower positions, real road traces or drive‑test data become available:

1. Edit the constants at the top of `analysis/contractor_review.py`, `analysis/site_selection.py` and `analysis/rf.py`.
2. Re‑run the three commands above.

## Sources
- Population: PSA 2020 Census via [PhilAtlas — San Pascual, Masbate](https://www.philatlas.com/luzon/r05/masbate/san-pascual.html) and the barangay profile pages; 2024 total from [Wikipedia](https://en.wikipedia.org/wiki/San_Pascual,_Masbate)
- Terrain: SRTM 1″ via [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/)
- Roads: [DPWH Masbate 1st DEO FY2024 APP](https://www.dpwh.gov.ph/DPWH/sites/default/files/filefield_paths/app2024_infra_dpwhmas1deo_region_v.pdf) (Pinamasingan road, Mapanique road, Poblacion–Quintina Road)
- Permitting: [EO No. 32 s. 2023](https://lawphil.net/executive/execord/eo2023/eo_32_2023.html); [Revised JMC No. 01 s. 2021](https://arta.gov.ph/wp-content/uploads/2022/02/ARTA-DICT-DILG-DHSUD-BFP-DPWH-CAAP-NTC-DOH-FDA-Revised-Joint-Memorandum-Circular-No.-01-S.-2021.pdf); [DICT co‑location policy (Circular 008)](https://pnl-law.com/blog/policy-guidelines-on-the-co-location-and-sharing-of-passive-telecommunications-tower-infrastructure-for-macro-cell-sites-dict-circular-no-008/)
- Power context: [Inquirer — "Burias folk struggle for power"](https://newsinfo.inquirer.net/150269/burias-folk-struggle-for-power/amp)
