# 5. Methodology & Limitations (Revision 2)

## Data
| Input | Source | Notes |
|---|---|---|
| Terrain | SRTM 1‑arc‑second (~30 m), AWS Terrain Tiles (`skadi/N12E122…N13E123`) | 41 radar spikes over Burias removed (7×7 median, > 80 m deviation). Highest real San Pascual terrain is ~197 m. |
| Population | PSA 2020 Census via PhilAtlas, all 22 barangays | Total 44,449. Each barangay's people are spread over land points within 600 m of its reference point. |
| Roads | **Terrain‑inferred proxy**: least‑slope paths between barangay centres along known DPWH corridors | No OSM or Google road file was reachable; replace with real traces. |
| Existing site | Bolod hill SRTM summit, 13.1250 N 122.9886 E, 108 m | Replace with the surveyed coordinates of the two towers. |
| Contractor site | Three scenarios on the inferred Bolod → Pinamasingan road (CT‑1/2/3) | Replace with the application's coordinates. |

## Coverage model (calibrated)
Standard‑Propagation‑Model style, as used by commercial planning tools:

```
Path loss = COST-231 Hata (suburban, 1800 MHz, effective antenna height)
          + 0.6 x Deygout 3-edge terrain diffraction (ITU-R P.526) on the SRTM profile
          + 2 dB
          + 15 dB/km beyond 3.5 km (handset uplink limit)
RSRP = EIRP per resource element (46 dBm / 20 MHz, 17.5 dBi, 1 dB jumper ≈ 31.7 dBm) − path loss
```
- **Effective antenna height** is the mast top above each receiver's ground (20–200 m), so hilltops get their real advantage.
- **Terrain sampling** is nearest‑cell, so obstruction heights do not depend on bearing. This removed the N/S/E/W streaks in early drafts.
- **Usable** means RSRP ≥ −110 dBm; **indoor‑grade** means ≥ −100 dBm.
- **Display classes:**

| Class | RSRP |
|---|---|
| Excellent | ≥ −80 |
| Strong | −80 to −90 |
| Good indoor | −90 to −100 |
| Outdoor only | −100 to −110 |
| Edge | −110 to −120 |
| No service | below −120 (uncoloured) |

### Calibration
The free parameters (diffraction weight, offset, fade) were tuned so the existing Bolod hill site matches the council's field observations:

| Field fact | Model |
|---|---|
| Serves Bolod, Terraplin, Nazareno, Busing | 87 %, 77 %, 55 %, 64 % of settled area usable |
| Does not serve Laurente | 1 % |
| Does not serve Boca Chica, San Rafael, Pinamasingan, others | 17 % (eastern edge), 0 %, 0 %, 0 % |
| Usable range 3–4 km | median 3.2 km over land (most directions 2.8–3.5 km) |

### Revision history
- **Revision 1:** LTE‑700 free‑space + diffraction model with a 10 km land cap. It over‑predicted range, put Bolod signal into Laurente, and drew coverage as a single flat fill that read like a flood map.
- **Revision 2:** this calibrated model, graded RSRP heatmaps on a contour basemap with range rings, and land‑only display. All site rankings were recomputed.

## Microwave
- **Clearance:** ≥ 0.6 F1 at k = 4/3 and ≥ 0.3 F1 at k = 2/3, with +10 m canopy allowance along the whole profile. 15 GHz is the default; 7 GHz is shown for long hops in rain zone P.
- **Masts:** the minimum equal height at both ends is reported (searched 15–75 m).

## Limitations
1. **Calibration is indirect.** It uses the council's observations, not measurements. A drive test (RSRP logs through all 22 barangays) should replace it.
2. **Omni antennas.** Real sectors have azimuths and tilts. This affects all sites alike, so the comparison holds.
3. **Approximate roads and power.** Spur lengths are indicative.
4. **Operator band unknown.** A sub‑GHz layer on new sites would reach further. That would help the ridge sites more than the contractor's, which is blocked by terrain rather than distance.
5. **Indicative ROI figures.**

## Reproduce
```bash
pip install -r analysis/requirements.txt
bash analysis/fetch_dem.sh
python3 analysis/site_selection.py      # unconstrained benchmark
python3 analysis/contractor_review.py   # contractor vs. ridges, network plan, figures, KMZ
bash slides/make_pdf.sh                 # slide deck PDF from results/review.json
```
To change calibration, edit `K_DIFF`, `OFFSET_DB`, `FADE_*` and the thresholds in `analysis/rf.py`.
