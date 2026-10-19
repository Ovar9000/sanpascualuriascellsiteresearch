# 5. Methodology & Limitations

## Data
| Input | Source | Notes |
|---|---|---|
| Terrain | SRTM 1‑arc‑second (~30 m), AWS Terrain Tiles (`skadi/N12E122…N13E123`) | 41 radar spikes over Burias removed (7×7 median, >80 m deviation). Without that step a spurious 1,823 m peak appears. Highest real San Pascual terrain is ~197 m. |
| Population | PSA 2020 Census via PhilAtlas, all 22 barangays | Total 44,449. Each barangay's people are spread over land points within 600 m of its PhilAtlas reference point. |
| Barangay coordinates | PhilAtlas reference points | San Pedro and Quintina pages carry a second, conflicting point (see `data/barangays.csv`). |
| Roads | **Terrain‑inferred proxy**: least‑slope paths between barangay centres along known DPWH corridors (Poblacion–Quintina Road via Pinamasingan, Pinamasingan and Mapanique road projects in DPWH FY2024 APP) | No OSM or Google road file was reachable. Replace with real traces. |
| Existing site | Bolod hill SRTM summit, 13.1250 N 122.9886 E, 108 m | Replace with the surveyed coordinates of the two towers. |
| Contractor site | Three scenarios on the inferred Bolod → Pinamasingan road (CT‑1/2/3) | Replace with the coordinates in the application. |

## RF model
- **Band / budget:** LTE Band 28 (758 MHz), 10 MHz carrier, 2×40 W RRU, 16.5 dBi panel, 1 dB jumper. EIRP is ≈ 33.7 dBm per resource element.
- **Path loss:** free space + **3‑edge Deygout knife‑edge diffraction (ITU‑R P.526)** on a 160‑point SRTM profile with k = 4/3 earth curvature, + **10 dB rural clutter**.
- **Service thresholds:** **outdoor** RSRP ≥ −110 dBm; **indoor‑grade** ≥ −100 dBm.
- **Range cap:** paths with more than 10 km of land are treated as unserved; over‑water paths are allowed up to 20 km. The Deygout model is optimistic over long multi‑ridge paths, and real sectors are down‑tilted and uplink‑limited.
- **Calibration:** the model reproduces the council's ground truth. Bolod Pob., Terraplin, Nazareno and Busing come out 84–98 % covered from Bolod hill. Boca Chica, Iniwaran, Laurente, Santa Cruz and Cueva sit in a 25–75 % fringe, consistent with "signal sometimes, unusable indoors."
- **"Net new beyond Bolod":** unserved‑barangay residents whose location reaches the threshold from the new site but **not** from the modelled Bolod signal. This is the fair test of whether a site *extends* coverage.

## Microwave
- **Clearance criterion:** ≥ 0.6 F1 at k = 4/3 and ≥ 0.3 F1 at k = 2/3, with +10 m canopy allowance on the whole profile. 15 GHz is the default; 7 GHz is shown as the rain‑robust option for long hops.
- **Masts:** the minimum equal mast height at both ends is reported (searched 15–75 m in 5 m steps).

## Limitations (say these out loud at the hearing — it builds credibility)
1. **Terrain only.** SRTM is a 30 m surface model with ±5–10 m vertical error. Tall coconut stands and buildings are not explicitly modelled beyond the flat clutter loss.
2. **Antennas modelled as omnidirectional** at full power. A real 3‑sector design with tilt will be somewhat smaller near the edges, but *equally* so for all sites, so **the comparison holds**.
3. **Approximate road and power alignment.** Spur lengths are indicative.
4. **Indicative ROI figures.** Replace them with operator data.
5. **Not a substitute for a drive test.** Treat this as an independent screening study. It is exactly why the council should demand the contractor's own propagation study and a post‑build drive test.

## Reproduce
```bash
pip install -r analysis/requirements.txt
bash analysis/fetch_dem.sh                 # downloads SRTM tiles into ./dem
python3 analysis/site_selection.py         # unconstrained benchmark  -> results/selection.json, candidates.csv
python3 analysis/contractor_review.py      # contractor vs ridge review -> results/review.json, figures, KMZ
```
To use the real contractor coordinates, edit `CONTRACTOR` in `analysis/contractor_review.py`. To use surveyed Bolod coordinates, edit `BOLOD` in `analysis/site_selection.py`.
