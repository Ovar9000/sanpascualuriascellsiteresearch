# San Pascual (Burias Island, Masbate) — Cell‑Site Technical Review for the Sangguniang Bayan

Independent technical review supporting the Sangguniang Bayan's decision on a **Resolution of No Objection (RONO)** for a proposed telecom tower in **deeper Barangay Bolod near the Pinamasingan Road**.

## Bottom line

| | Contractor's site (deeper Bolod / Pinamasingan Rd) | Ridge alternatives on the same road network |
|---|---|---|
| Ground elevation | 60–73 m (35–48 m **below** the existing Bolod hill towers, 1–2 km away) | 123–153 m (ALT‑A, ALT‑B, ALT‑D) |
| Footprint already covered by Bolod | **84–94 %** | 12–58 % |
| Unserved residents added beyond the existing Bolod signal | **≈ 0 (0–43)** | **5,400 – 11,600 per site** |
| Road access | On the road | 0.4–1.0 km spur |
| Microwave line‑of‑sight to Bolod | Trivial (1–2 km) | Clear: 6.3–15 km, 15–40 m masts |

**36,021 of San Pascual's 44,449 residents (81 %)** live in the 18 barangays the Bolod hill towers cannot reach. The contractor's site serves essentially none of them, because a lower antenna next to a higher one sees nothing new. A ridge on the **same Poblacion–Pinamasingan road ~5 km further out (ALT‑A)** adds **~7,500**. The **Malaking Ilog–Mapanique ridge (ALT‑B)** adds **~11,600**. **ALT‑B + Santa Cruz ridge (ALT‑D)** together take the municipality from **30 % to 64 %** within service.

**Recommendation:** No objection *subject to* relocation to a ridge site (ALT‑A minimum, ALT‑B preferred). Alternatively, treat the Bolod site as capacity‑only, tied to a binding, time‑bound commitment to build a ridge site. Insist on co‑location on the existing towers if the goal is only a new operator or more capacity.

> ⚖️ **Legal footing:** EO 32 (s. 2023) lists Sanggunian resolutions among requirements that are no longer prerequisites for tower permits. Confirm the RONO's status with the Municipal Legal Officer and frame the conditions as a MOA (see [doc 4 §4.0](docs/04_sanggunian_hearing_strategy.md)).

## Contents

| # | Document | What it gives you |
|---|---|---|
| 1 | [Coverage Overlap & Terrain Critique](docs/01_coverage_overlap_terrain_critique.md) | Why the contractor's site is redundant and cannot clear the ridges |
| 2 | [Road‑Accessible Alternatives + Board Matrix](docs/02_road_accessible_alternatives.md) | ALT‑A to ALT‑D with coordinates, backhaul, access, ROI matrix and site packages |
| 3 | [Hearing Visualization Guide](docs/03_hearing_visualization_guide.md) | Google Earth Pro (KMZ + Viewshed), HeyWhatsThat and CloudRF steps, plus a 3‑minute script |
| 4 | [Hearing Strategy & RONO Conditions](docs/04_sanggunian_hearing_strategy.md) | 5 questions for councilors, the conditions list, and a draft operative clause |
| 5 | [Methodology & Limitations](docs/05_methodology_and_limitations.md) | Data, RF model, calibration, caveats, how to re‑run |

**Ready‑to‑project files** (`results/`):

- `san_pascual_review.kmz` — open in Google Earth Pro: 3D masts, population columns, coverage layers, microwave links
- `fig_side_by_side.png` — contractor vs. ridge alternative
- `fig_all_sites.png` — every option plus packages
- `fig_profiles.png` — terrain cross‑sections showing the blocking ridges
- `fig_population_bars.png` — net new residents per option
- `review.json`, `candidates.csv`, `selection.json` — every number quoted

## Key coordinates (WGS84)

| ID | Site | Lat | Lon |
|---|---|---|---|
| BOLOD | Existing towers, Bolod hill (SRTM summit; confirm by survey) | 13.1250 | 122.9886 |
| CT‑2 | Contractor scenario (deeper Bolod, Pinamasingan Rd; confirm from application) | 13.1100 | 122.9908 |
| ALT‑A | Pinamasingan ridge — same road, further out | 13.0872 | 123.0317 |
| ALT‑B | Malaking Ilog–Mapanique ridge — inland road | 13.0075 | 123.0556 |
| ALT‑C | Cueva ridge — north‑coast road via Laurente | 13.1017 | 123.0578 |
| ALT‑D | Santa Cruz ridge — west‑coast road via San Rafael | 13.0636 | 122.9717 |

## Reproduce / update

```bash
pip install -r analysis/requirements.txt
bash analysis/fetch_dem.sh
python3 analysis/site_selection.py      # unconstrained hilltop benchmark
python3 analysis/contractor_review.py   # contractor vs. road-accessible ridges, figures, KMZ
```

When the application's exact coordinates, the surveyed Bolod tower positions, or real road traces become available, edit the constants at the top of `analysis/contractor_review.py` and `analysis/site_selection.py`, then re‑run.

## Sources
- Population: PSA 2020 Census via [PhilAtlas — San Pascual, Masbate](https://www.philatlas.com/luzon/r05/masbate/san-pascual.html) and the barangay profile pages; 2024 total from [Wikipedia](https://en.wikipedia.org/wiki/San_Pascual,_Masbate)
- Terrain: SRTM 1″ via [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/)
- Roads: [DPWH Masbate 1st DEO FY2024 APP](https://www.dpwh.gov.ph/DPWH/sites/default/files/filefield_paths/app2024_infra_dpwhmas1deo_region_v.pdf) (Pinamasingan road, Mapanique road, Poblacion–Quintina Road)
- Permitting: [EO No. 32 s. 2023](https://lawphil.net/executive/execord/eo2023/eo_32_2023.html); [Revised JMC No. 01 s. 2021](https://arta.gov.ph/wp-content/uploads/2022/02/ARTA-DICT-DILG-DHSUD-BFP-DPWH-CAAP-NTC-DOH-FDA-Revised-Joint-Memorandum-Circular-No.-01-S.-2021.pdf); [DICT co‑location policy (Circular 008)](https://pnl-law.com/blog/policy-guidelines-on-the-co-location-and-sharing-of-passive-telecommunications-tower-infrastructure-for-macro-cell-sites-dict-circular-no-008/)
- Power context: [Inquirer — "Burias folk struggle for power"](https://newsinfo.inquirer.net/150269/burias-folk-struggle-for-power/amp)
