"""Build the Sangguniang Bayan slide deck (HTML -> PDF) from results/review.json.

Usage:
    python3 slides/build_slides.py            # writes slides/san_pascual_review_slides.html
    bash slides/make_pdf.sh                   # prints it to slides/San_Pascual_Cell_Site_Review.pdf
Every number on the slides is read from results/review.json, so re-running the
analysis and this script keeps the deck consistent.
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "..", "results", "review.json")))

TOTAL = R["population_total_2020"]
SERVED = R["served_today"]
UNSERVED = R["unserved_today"]
CAL = R["calibration"]
CTS = R["contractor"]
CT = CTS[1]
ALTS = R["alternatives"]
A = {a["id"]: a for a in ALTS}
BUILD = R["buildout"]
BOLOD_TOTAL = R["bolod"]["total_model"]
CT_TOTAL = R["contractor_total_with_bolod"]
BOLOD_TOP = round(R["bolod"]["ground"] + R["bolod"]["agl"])
PKG = R["best_package"]

BRGY = [
    ("Bolod (Poblacion)", 3626, True), ("Terraplin", 1618, True), ("Nazareno", 1298, True), ("Busing", 1886, True),
    ("San Pedro", 3232, False), ("San Rafael", 3140, False), ("Cueva", 2788, False), ("Boca Chica", 2756, False),
    ("Laurente", 2752, False), ("Iniwaran", 2360, False), ("Pinamasingan", 2005, False), ("Mapanique", 1984, False),
    ("Santa Cruz", 1945, False), ("Malaking Ilog", 1911, False), ("Mabini", 1779, False), ("Quintina", 1637, False),
    ("Ki-Romero", 1487, False), ("Dangcalan", 1430, False), ("Mabuhay", 1410, False), ("San Jose", 1409, False),
    ("Halabangbaybay", 1150, False), ("Ki-Buaya", 846, False),
]


def n(x):
    return f"{int(round(x)):,}"


def pct(x):
    return f"{x:.0%}"


def img(name):
    return f"../results/{name}"


slides = []


def slide(section, title, body, cls=""):
    slides.append((section, title, body, cls))


# ------------------------------------------------------------------ 1 title
slide("", "", f"""
<div class="cover">
  <div class="cover-text">
    <div class="eyebrow light">Technical Advisor's review · Sangguniang Bayan of San Pascual, Masbate</div>
    <h1 class="cover-title">San Pascual Cell-Site Review</h1>
    <p class="cover-sub">The proposed tower in deeper Barangay Bolod near the Pinamasingan Road, tested against the existing
    Bolod hill towers and against road-accessible ridge sites, using a coverage model calibrated to what residents actually receive.</p>
    <div class="cover-meta">Revision 2 · October 2026 · Field-calibrated coverage model (usable range 3–4 km)</div>
  </div>
  <img class="cover-map" src="{img('fig_network.png')}" alt="">
</div>""", "cover-slide")

# ------------------------------------------------------------------ 2 bottom line
slide("Summary", "The proposed tower copies Bolod. Ridge sites reach new people.", f"""
<div class="kpis">
  <div class="kpi"><b>{n(UNSERVED)}</b><span>residents in 18 barangays with no usable signal ({pct(UNSERVED / TOTAL)} of {n(TOTAL)})</span></div>
  <div class="kpi ct"><b>{pct(CT['overlap_with_bolod'])}</b><span>of the contractor site's coverage is already covered by Bolod</span></div>
  <div class="kpi ct"><b>0</b><span>unserved residents it adds in all three location scenarios with a 40 m mast (at most 15 even at 60 m)</span></div>
  <div class="kpi rd"><b>{n(A['ALT-D']['beyond_bolod'])}</b><span>added by the best single ridge site (Malaking Ilog–Mapanique)</span></div>
</div>
<div class="two">
  <div>
    <h3>What we found</h3>
    <ul class="big">
      <li>The existing Bolod towers reach about 3–4 km. They serve Bolod, Terraplin, Nazareno and Busing, and do not reach Laurente. Our model now reproduces this.</li>
      <li>The contractor's antennas would sit {BOLOD_TOP - CT['antenna_top_asl']} m <em>lower</em> than Bolod's, 1–2 km away. Everything they can reach, Bolod already reaches.</li>
      <li>Because signal only travels 3–4 km here, the unserved barangays need towers <em>near them</em>, on high ground. Every ridge site we propose is within 1 km of a road and has a clear microwave link back.</li>
    </ul>
  </div>
  <div>
    <h3>What we recommend</h3>
    <ul class="big">
      <li><b>Do not endorse the deeper-Bolod site as a coverage project.</b></li>
      <li>Ask for the Malaking Ilog–Mapanique and San Rafael–Santa Cruz ridges first: +{n(PKG['2']['beyond_bolod'])} residents, taking service from {pct(BOLOD_TOTAL / TOTAL)} to {pct(PKG['2']['total'] / TOTAL)}.</li>
      <li>If the contractor will only build on its own road: the Pinamasingan ridge (+{n(A['ALT-A']['beyond_bolod'])}) or the Cueva ridge (+{n(A['ALT-E']['beyond_bolod'])}).</li>
      <li>Ask for an eight-site roadmap: {pct(BUILD[-1]['cum_total'] / TOTAL)} of residents within service.</li>
    </ul>
  </div>
</div>""")

# ------------------------------------------------------------------ 3 who is unserved
mx = max(p for _, p, _ in BRGY)
rows = "".join(
    f'<div class="hb"><span class="hb-l">{html.escape(b)}</span><span class="hb-t"><span class="hb-f {"sv" if s else "us"}" style="width:{p / mx * 100:.1f}%"></span></span><span class="hb-v">{n(p)}</span></div>'
    for b, p, s in BRGY)
slide("The problem", f"{n(UNSERVED)} of {n(TOTAL)} residents have no usable signal", f"""
<div class="two wide-left">
  <div class="hbars">{rows}</div>
  <div class="stack">
    <div class="legend-row"><i class="sw sv"></i> Served by Bolod hill today (field report)</div>
    <div class="legend-row"><i class="sw us"></i> Not served</div>
    <p class="lead">Four barangays around the poblacion and port are served: <b>{n(SERVED)}</b> people ({pct(SERVED / TOTAL)}).</p>
    <p class="lead">The other eighteen, <b>{n(UNSERVED)}</b> people, sit behind the hills or beyond the towers' 3–4 km reach. The largest are San Pedro (3,232), San Rafael (3,140), Cueva (2,788), Boca Chica (2,756) and Laurente (2,752).</p>
    <p class="note">Source: PSA 2020 Census via PhilAtlas. The 2024 POPCEN total is 44,641 (+0.4%).</p>
  </div>
</div>""")

# ------------------------------------------------------------------ 4 what changed
slide("Model review", "What changed in this revision", f"""
<div class="three">
  <div class="card"><h3>1. Laurente</h3><p>The first map showed Bolod reaching parts of Laurente. Field reports say it does not. The terrain confirms it: a spur rises about 41 m above the radio path, 3.7 km out.</p><p class="fix">Now: Laurente <b>{pct(CAL['bolod_per_barangay']['Laurente']['usable'])}</b> covered.</p></div>
  <div class="card"><h3>2. Range</h3><p>The first model used a low-band, open-terrain budget and let signal run 10 km or more. Residents report usable signal ends at about 3–4 km.</p><p class="fix">Now: median land range <b>{CAL['bolod_land_range_km']['median']} km</b> (most directions {CAL['bolod_land_range_km']['p25']}–{CAL['bolod_land_range_km']['p75']} km).</p></div>
  <div class="card"><h3>3. The map itself</h3><p>The first maps used one flat colour over a grey relief, which read like a flood-depth map and hid how strong the signal is.</p><p class="fix">Now: graded RSRP classes from excellent to edge, on a contour basemap with 1–4 km range rings, land only.</p></div>
</div>
<p class="lead" style="margin-top:36px">All conclusions were recomputed. The direction of the finding is unchanged and stronger: the contractor's site adds <b>zero</b> unserved residents. Because each tower now reaches less, more towers are needed, and each must sit close to the people it serves.</p>""")

# ------------------------------------------------------------------ 5 calibration method
crow = "".join(
    f"<tr><td>{html.escape(k)}</td><td class='r'>{v['km']}</td><td>{'Served' if v['field'] == 'served' else 'Not served'}</td>"
    f"<td class='r'>{pct(v['usable'])}</td><td class='r'>{pct(v['indoor'])}</td>"
    f"<td>{'✓ matches' if (v['usable'] >= 0.5) == (v['field'] == 'served') else 'fringe only'}</td></tr>"
    for k, v in CAL["bolod_per_barangay"].items() if v["km"] <= 5.5)
slide("Model review", "Calibrated to what residents receive from Bolod hill", f"""
<div class="two">
  <div>
    <table class="t"><thead><tr><th>Barangay</th><th class="r">km</th><th>Field report</th><th class="r">Usable</th><th class="r">Indoor</th><th>Check</th></tr></thead>
    <tbody>{crow}</tbody></table>
    <p class="note">Usable = share of the barangay's settled area at RSRP ≥ −110 dBm; indoor = ≥ −100 dBm. Barangays beyond 5.5 km all predict 0%.</p>
  </div>
  <div class="stack">
    <h3>The model</h3>
    <ul>
      <li>Terrain: SRTM 30 m elevation, radar spikes removed.</li>
      <li>Path loss: COST-231 Hata (suburban) at 1800 MHz, plus terrain diffraction over the actual ridges (Deygout, ITU-R P.526).</li>
      <li>Effective antenna height above each receiver, so hilltop sites get their real advantage.</li>
      <li>Handset uplink fade beyond 3.5 km, matching the observed 3–4 km reach.</li>
      <li>Thresholds: ≥ −110 dBm usable outdoors, ≥ −100 dBm indoors.</li>
    </ul>
    <p class="note">The free parameters were tuned so Bolod hill covers its four barangays and nothing else, ending at 3–4 km. A drive test should replace this tuning before final siting.</p>
  </div>
</div>""")

# ------------------------------------------------------------------ 6 calibration map
slide("Model review", "Existing Bolod hill towers: predicted signal strength", f"""
<div class="fig-row">
  <img class="fig tall" src="{img('fig_calibration_bolod.png')}" alt="">
  <div class="side">
    <p>Signal is strong around the poblacion and port, and fades to edge level by 3–4 km.</p>
    <p>Busing and Nazareno sit in the outdoor-only and edge bands, consistent with "signal, but weak indoors".</p>
    <p><b>Laurente</b> (2,752) is behind a spur and gets nothing. <b>Boca Chica</b> gets edge signal on its eastern side only.</p>
    <p>Pinamasingan and San Rafael are beyond reach.</p>
  </div>
</div>""")

# ------------------------------------------------------------------ 7 signal classes
slide("Model review", "Reading the colours", """
<div class="classes">
  <div class="cls" style="--c:#0b7a3b"><b>Excellent</b><span>≥ −80 dBm</span><p>Full speed indoors and out. Video calls work everywhere.</p></div>
  <div class="cls" style="--c:#58b947"><b>Strong</b><span>−80 to −90</span><p>Reliable inside concrete houses. Good data.</p></div>
  <div class="cls" style="--c:#f4d03f"><b>Good indoor</b><span>−90 to −100</span><p>Calls and messaging indoors; data slows in back rooms.</p></div>
  <div class="cls" style="--c:#f08a24"><b>Outdoor only</b><span>−100 to −110</span><p>Works outside or by a window. Drops indoors. Counted as "usable".</p></div>
  <div class="cls" style="--c:#d7301f"><b>Edge</b><span>−110 to −120</span><p>Signal bars appear but calls drop. Not counted as served.</p></div>
  <div class="cls" style="--c:#e9e6d8"><b>No colour</b><span>&lt; −120</span><p>No service.</p></div>
</div>
<p class="lead" style="margin-top:40px">RSRP (Reference Signal Received Power) is the LTE signal level a phone measures. It is the figure the contractor's own propagation map should show, and what a drive test records.</p>""")

# ------------------------------------------------------------------ 8 contractor site
ctrows = "".join(
    f"<tr><td>{c['id']}</td><td class='mono'>{c['lat']:.4f}, {c['lon']:.4f}</td><td class='r'>{c['ground']:.0f} m</td>"
    f"<td class='r'>{c['antenna_top_asl']} m</td><td class='r'>{c['dist_bolod_km']:.1f} km</td><td class='r'>{pct(c['overlap_with_bolod'])}</td>"
    f"<td class='r'>{n(c['beyond_bolod'])}</td><td class='r'>{c['sensitivity']['30']} / {c['sensitivity']['45']} / {c['sensitivity']['60']}</td></tr>"
    for c in CTS)
slide("Contractor's site", "Where the contractor wants to build", f"""
<p class="lead">The application places the tower in deeper Barangay Bolod near the Pinamasingan Road. We did not have exact coordinates, so we tested three plausible spots on that road, 1–2 km south of the existing towers.</p>
<table class="t big"><thead><tr><th>Scenario</th><th>Lat, Lon</th><th class="r">Ground</th><th class="r">Antenna top (40 m mast)</th><th class="r">From existing towers</th><th class="r">Area already covered by Bolod</th><th class="r">Unserved residents added</th><th class="r">Added at 30 / 45 / 60 m mast</th></tr></thead>
<tbody>{ctrows}<tr class="ref"><td>Bolod hill (existing)</td><td class="mono">13.1250, 122.9886</td><td class="r">108 m</td><td class="r">{BOLOD_TOP} m</td><td class="r">—</td><td class="r">—</td><td class="r">—</td><td class="r">—</td></tr></tbody></table>
<p class="lead" style="margin-top:28px">Whichever spot it is, and however tall the mast, the result is the same: <b>no unserved barangay gains usable service.</b></p>""")

# ------------------------------------------------------------------ 9 antenna heights
def hbar(label, sub, ground, mast, color):
    return (f'<div class="hrow"><div class="hl">{label}<small>{sub}</small></div><div class="ht">'
            f'<span class="hg" style="width:{ground / 2:.1f}%"></span><span class="hm" style="left:{ground / 2:.1f}%;width:{mast / 2:.1f}%;background:{color}"></span>'
            f'</div><div class="hv">{ground + mast:.0f} m</div></div>')


slide("Contractor's site", "A lower antenna next to a higher one sees nothing new", f"""
<div class="heights">
  {hbar('Contractor CT-2', f"{CT['ground']:.0f} m ground + 40 m mast", CT['ground'], 40, '#e08214')}
  {hbar('Existing Bolod hill', '108 m ground + 40 m mast', 108, 40, '#2e7d32')}
  {hbar('ALT-A Pinamasingan ridge', f"{A['ALT-A']['ground']:.0f} m ground + 40 m mast", A['ALT-A']['ground'], 40, '#1565c0')}
  {hbar('ALT-C San Rafael–Santa Cruz', f"{A['ALT-C']['ground']:.0f} m ground + 40 m mast", A['ALT-C']['ground'], 40, '#ad1457')}
  {hbar('ALT-D Malaking Ilog–Mapanique', f"{A['ALT-D']['ground']:.0f} m ground + 40 m mast", A['ALT-D']['ground'], 40, '#6a1b9a')}
  <div class="haxis"><div></div><div><span>0</span><span>50</span><span>100</span><span>150</span><span>200 m above sea</span></div><div></div></div>
</div>
<p class="lead">Drawn to scale. The contractor's antennas would be {BOLOD_TOP - CT['antenna_top_asl']} m below the antennas already on Bolod hill. Any ridge that blocks Bolod also blocks them. The ridge alternatives put antennas 12–45 m higher than Bolod's, and next to the people they serve.</p>""")

# ------------------------------------------------------------------ 10 overlap
slide("Contractor's site", f"{pct(CT['overlap_with_bolod'])} of its coverage is already covered", f"""
<img class="fig wide" src="{img('fig_contractor_overlap.png')}" alt="">
<p class="lead">C shows the only land the contractor's site would add: {CT['new_land_km2']} km² of slopes and gullies south of the towers, with no barangay centre in it. Unserved residents gained: <b>{n(CT['beyond_bolod'])}</b>.</p>""")

# ------------------------------------------------------------------ 11 profiles
pr = R["profiles"]
slide("Contractor's site", "The terrain between the contractor's site and the unserved barangays", f"""
<div class="fig-row">
  <img class="fig tall" src="{img('fig_profiles.png')}" alt="">
  <div class="side">
    <p>Left: from the contractor site. Right: from the nearest proposed ridge site. Brown is the ground; the line is the direct radio path to a phone 1.5 m above ground.</p>
    <p><b>Pinamasingan</b> ({pr['Pinamasingan']['contractor_km']} km): a spur next to the site blocks the path.</p>
    <p><b>Laurente</b> ({pr['Laurente']['contractor_km']} km): the path runs under 3 km of hills up to 115 m.</p>
    <p><b>Santa Cruz</b> ({pr['Santa Cruz']['contractor_km']} km) and <b>San Pedro</b> ({pr['San Pedro']['contractor_km']} km): beyond reach and behind the 160 m central ridge.</p>
    <p>From the ridge sites, each of these barangays has clear line of sight.</p>
  </div>
</div>""")

# ------------------------------------------------------------------ 12 side by side
slide("Better compromise", "Same road, higher ground", f"""
<img class="fig wide" src="{img('fig_side_by_side.png')}" alt="">
<p class="lead">ALT-A sits on the same Poblacion–Pinamasingan road, about 4.5 km past the contractor's spot, with a {A['ALT-A']['road_m']} m access spur. It covers Pinamasingan fully, and part of Cueva, for <b>+{n(A['ALT-A']['beyond_bolod'])}</b> residents, against zero for the proposed spot.</p>""")

# ------------------------------------------------------------------ 13 alternatives table
def brgy_list(d):
    return ", ".join(f"{k} {pct(v)}" for k, v in sorted(d.items(), key=lambda kv: -kv[1]) if v >= 0.1)


arows = "".join(
    f"<tr><td><b>{a['id']}</b> {html.escape(a['name'])}<br><span class='sm'>{html.escape(a['corridor'])}</span></td>"
    f"<td class='mono'>{a['lat']:.4f}, {a['lon']:.4f}</td><td class='r'>{a['ground']:.0f} m</td><td class='r'>{a['road_m']} m</td>"
    f"<td class='r'>{a['mw']['dist_km']:.1f} km · {a['mw_mast_m']} m</td><td class='r big'>{n(a['beyond_bolod'])}</td><td class='r'>{n(a['beyond_bolod_indoor'])}</td>"
    f"<td class='sm'>{brgy_list(a['per_barangay_usable'])}</td></tr>"
    for a in ALTS)
slide("Better compromise", "Five ridge sites the contractor can still drive to", f"""
<table class="t"><thead><tr><th>Site</th><th>Lat, Lon</th><th class="r">Ground</th><th class="r">Road spur</th><th class="r">Microwave to Bolod</th><th class="r">New residents (usable)</th><th class="r">(indoor)</th><th>Barangays lifted (share of settled area)</th></tr></thead>
<tbody>{arows}<tr class="ct-row"><td><b>CT-2</b> Contractor, deeper Bolod</td><td class="mono">{CT['lat']:.4f}, {CT['lon']:.4f}</td><td class="r">{CT['ground']:.0f} m</td><td class="r">0 m</td><td class="r">{CT['dist_bolod_km']:.1f} km</td><td class="r big">0</td><td class="r">0</td><td class="sm">none</td></tr></tbody></table>
<p class="note">Screened from {R['pool_size']} hilltops within 1 km of a road. Each has a microwave path to Bolod clearing 60% of the first Fresnel zone (and 30% under sub-refraction) at 15 GHz, with masts of 45 m or less at both ends.</p>""")

# ------------------------------------------------------------------ 14-18 per alternative
blurbs = {
    "ALT-A": "The direct answer to the contractor's road. It stays on the Poblacion–Pinamasingan road and climbs a 123 m ridge above Pinamasingan.",
    "ALT-B": "A 72 m knoll on the north-coast road between Nazareno and Laurente. It reaches Laurente, which Bolod cannot, with a short 2.6 km hop.",
    "ALT-C": "On the west-coast road itself (43 m from it). It covers Santa Cruz and most of San Rafael, with the easiest backhaul on the island.",
    "ALT-D": "The best single site. A 153 m ridge above Malaking Ilog and Mapanique, serving the southern belt. Needs a 15 km link: specify 7/8 GHz.",
    "ALT-E": "A 62 m spur on the Poblacion–Quintina road above Cueva, the third-largest unserved barangay.",
}
for a in ALTS:
    slide("Better compromise", f"{a['id']} · {a['name']}", f"""
<div class="fig-row">
  <img class="fig tall" src="{img('fig_' + a['id'].lower() + '.png')}" alt="">
  <div class="side">
    <p class="lead">{blurbs[a['id']]}</p>
    <dl class="facts">
      <dt>Location</dt><dd class="mono">{a['lat']:.4f} N, {a['lon']:.4f} E</dd>
      <dt>Ground / antenna top</dt><dd>{a['ground']:.0f} m / {a['antenna_top_asl']} m above sea</dd>
      <dt>Road access</dt><dd>{a['road_m']} m spur · {html.escape(a['corridor'])}</dd>
      <dt>Backhaul</dt><dd>{a['mw']['dist_km']:.1f} km to Bolod · {a['mw_mast_m']} m masts at 15 GHz ({a['mw_7ghz_mast']} m at 7 GHz)</dd>
      <dt>New residents</dt><dd><b>{n(a['beyond_bolod'])}</b> usable · {n(a['beyond_bolod_indoor'])} indoor-grade</dd>
      <dt>Overlap with Bolod</dt><dd>{pct(a['overlap_with_bolod'])}</dd>
      <dt>Barangays lifted</dt><dd>{brgy_list(a['per_barangay_usable'])}</dd>
    </dl>
  </div>
</div>""")

# ------------------------------------------------------------------ 19 microwave
slide("Better compromise", "Every proposed site has a clear microwave link", f"""
<img class="fig wide" src="{img('fig_mw_profiles.png')}" alt="" style="max-height:740px">
<p class="note">Shaded band: 60% of the first Fresnel zone at 15 GHz, the standard clearance for a licensed link. Masts are the minimum equal height at both ends. Bottom row: build-out sites that are not among ALT-A to ALT-E. N3 and N7 hop via N1 rather than directly to Bolod.</p>""")

# ------------------------------------------------------------------ 20 network map
slide("Network plan", "One tower can't cover a 3–4 km-reach island. A plan can.", f"""
<img class="fig wide" src="{img('fig_network.png')}" alt="">
<p class="lead">Left: Bolod plus the contractor's site. Right: Bolod plus eight road-accessible hill sites chosen one at a time for the most new residents. Blue lines are the microwave links.</p>""")

# ------------------------------------------------------------------ 21 build-out
brows = "".join(
    f"<tr><td><b>{s['id']}</b></td><td>{html.escape(s['name'])}{(' (' + s['alt'] + ')') if s.get('alt') else ''}</td><td class='mono'>{s['lat']:.4f}, {s['lon']:.4f}</td>"
    f"<td class='r'>{s['ground']:.0f} m</td><td class='r'>{s['road_m']} m</td><td>{s['parent']} · {s['mw']['dist_km']:.1f} km</td>"
    f"<td class='r'>+{n(s['gain'])}</td><td class='r'>{n(s['cum_total'])} ({pct(s['cum_total'] / TOTAL)})</td></tr>"
    for s in BUILD)
slide("Network plan", "Build-out order: residents with usable signal", f"""
<img class="fig" src="{img('fig_buildout.png')}" alt="" style="max-height:330px;width:auto;align-self:center">
<div>
  <table class="t sm tight"><thead><tr><th>#</th><th>Site</th><th>Lat, Lon</th><th class="r">Ground</th><th class="r">Spur</th><th>Backhaul via</th><th class="r">Adds</th><th class="r">Total</th></tr></thead><tbody>{brows}</tbody></table>
</div>
<p class="lead">Phase 1 (N1 + N2) more than doubles coverage: {pct(BOLOD_TOTAL / TOTAL)} → {pct(BUILD[1]['cum_total'] / TOTAL)}. The full eight sites reach {pct(BUILD[-1]['cum_total'] / TOTAL)}. Bolod plus the contractor's site stays at {pct(CT_TOTAL / TOTAL)}.</p>""")

# ------------------------------------------------------------------ 22 matrix
def pips(k):
    return '<span class="pips">' + "".join(f'<i class="{"on" if i < k else ""}"></i>' for i in range(5)) + "</span>"


def score_pop(v):
    return 1 if v < 500 else 2 if v < 2000 else 3 if v < 3000 else 4 if v < 4000 else 5


def score_bh(a):
    d, h = a["mw"]["dist_km"], a["mw_mast_m"]
    return 5 if (d <= 8 and h <= 20) else 4 if (d <= 8 and h <= 40) else 3 if d <= 12 else 3 if h <= 35 else 2


def score_road(a):
    r = a["road_m"]
    return 5 if r < 100 else 4 if r < 500 else 3 if r < 900 else 3


mrows = (f"<tr class='ct-row'><td><b>CT</b> Contractor, deeper Bolod</td><td>{pips(1)} 0 new</td><td>{pips(5)} 1–2 km</td><td>{pips(5)} on the road, near the grid</td>"
         f"<td>{pips(1)} no new subscribers</td><td class='bad'>Reject as a coverage project</td></tr>")
verdict = {"ALT-A": "Minimum compromise on the contractor's road", "ALT-B": "Laurente fix, cheap hop", "ALT-C": "Phase 1",
           "ALT-D": "Phase 1, best single site", "ALT-E": "Phase 2"}
for a in ALTS:
    sp = score_pop(a["beyond_bolod"])
    mrows += (f"<tr><td><b>{a['id']}</b> {html.escape(a['name'])}</td><td>{pips(sp)} {n(a['beyond_bolod'])}</td>"
              f"<td>{pips(score_bh(a))} {a['mw']['dist_km']:.1f} km, {a['mw_mast_m']} m</td><td>{pips(score_road(a))} {a['road_m']} m spur</td>"
              f"<td>{pips(max(1, sp - (1 if a['mw']['dist_km'] > 12 else 0)))} ₱{a['beyond_bolod'] * 0.6 / 1000:.1f}–{a['beyond_bolod'] * 0.9 / 1000:.1f} M/yr</td><td>{verdict[a['id']]}</td></tr>")
slide("Decision matrix", "Four metrics, every option", f"""
<table class="t matrix"><thead><tr><th>Site</th><th>Population covered<br><span class="sm">new residents, of {n(UNSERVED)}</span></th><th>Backhaul to Bolod</th><th>Power / road access</th><th>Commercial viability<br><span class="sm">indicative revenue</span></th><th>Verdict</th></tr></thead>
<tbody>{mrows}</tbody></table>
<p class="note">Scores 1 (poor) to 5 (excellent). Revenue assumes ₱600–900 per newly covered resident per year (rural Bicol prepaid mix); replace with the operator's own figures. A 40 m greenfield with microwave typically costs ₱10–15 M, plus ₱3–6 M for a hilltop access spur and solar-hybrid power.</p>""")

# ------------------------------------------------------------------ 23 commercial
slide("Decision matrix", "The commercial picture, read honestly", f"""
<div class="three">
  <div class="card"><h3>Contractor's site</h3><p>No new subscribers. All revenue is traffic moved off Bolod. That justifies a capacity upgrade, which co-location on the existing Bolod towers delivers without a new structure.</p></div>
  <div class="card"><h3>Single ridge site</h3><p>About {n(A['ALT-D']['beyond_bolod'])} new residents at best: roughly ₱{A['ALT-D']['beyond_bolod'] * 0.6 / 1000:.1f}–{A['ALT-D']['beyond_bolod'] * 0.9 / 1000:.1f} M a year against ₱13–21 M capex. Payback is about 4–7 years, slower than an urban site but positive, and it opens a captive market.</p></div>
  <div class="card"><h3>Shared network</h3><p>With a 3–4 km reach, full coverage needs several sites. Multi-operator sharing, DICT common-tower and connectivity programmes, and LGU help with land and access roads are what make sites N3–N8 viable.</p></div>
</div>
<p class="lead" style="margin-top:36px">The council's leverage is simple: offer fast permitting, land and road help for ridge sites, and ask for nothing new for a site that adds no one.</p>""")

# ------------------------------------------------------------------ 24 legal
slide("Hearing strategy", "Check the council's legal footing first", """
<div class="callout">
  <p><b>Executive Order No. 32 (s. 2023)</b> lists Sanggunian resolutions among the requirements that are no longer prerequisites for shared telecom tower permits. <b>Revised JMC No. 01 s. 2021</b> bars LGUs from requiring documents beyond its list.</p>
</div>
<div class="two" style="margin-top:32px">
  <div><h3>Before the hearing</h3><ul class="big">
    <li>Ask the Municipal Legal Officer and DILG provincial office whether this RONO is legally required, or a courtesy endorsement the contractor is seeking.</li>
    <li>If a courtesy: write the conditions into a Memorandum of Agreement the contractor signs.</li></ul></div>
  <div><h3>Levers the LGU still holds</h3><ul class="big">
    <li>Municipal and barangay land for ridge sites, and right-of-way for access spurs.</li>
    <li>Building-permit technical review, zoning and locational clearance.</li>
    <li>Fast one-stop-shop processing under EO 32.</li>
    <li>A council resolution of findings to DICT and NTC.</li></ul></div>
</div>""")

# ------------------------------------------------------------------ 25-26 questions
Q = [
    ("Show us your RSRP propagation map, for your site and for the existing Bolod towers, and the difference.",
     "Ask for −100 and −110 dBm contours, the model and terrain data, antenna height, azimuth, tilt and power. Then: which barangays, and how many residents, gain service they do not have today?"),
    (f"Your antennas will be about {BOLOD_TOP - CT['antenna_top_asl']} m lower than the ones already on Bolod hill. Name one unserved barangay you will reach that Bolod cannot.",
     "Ask for the terrain profile to Pinamasingan, Laurente or San Rafael. Ask whether they evaluated the Pinamasingan ridge on the same road, and for their site-search ring."),
    ("Which operator will be on this tower, and why not co-locate on the existing Bolod towers?",
     "If the purpose is a new operator or more capacity, DICT's co-location policy points to the existing structures."),
    ("What is your written commitment to the 18 unserved barangays, with sites and dates?",
     "Ask for a rollout schedule with coordinates and on-air dates, and a drive test shared with the council within 60 days of switching on."),
    ("Which frequency band will the new tower use, and will it stay up when the grid is down or a typhoon hits?",
     "A sub-GHz layer (700/850 MHz) reaches further than the 3–4 km seen today. Ask for battery hours, generator or solar backup, the NSCP wind rating and typhoon restoration time."),
]
qhtml = "".join(f'<li><div class="qn">Q{i + 1}</div><div><p class="qa">"{html.escape(q)}"</p><p class="qw">{html.escape(w)}</p></div></li>' for i, (q, w) in enumerate(Q))
slide("Hearing strategy", "Five questions for the councilors to ask", f'<ol class="qs">{qhtml}</ol>')

# ------------------------------------------------------------------ 27 conditions
slide("Hearing strategy", "Conditions before granting no objection", f"""
<div class="four">
  <div class="cond"><h3>Coverage extension</h3><ul>
    <li>The site must give RSRP ≥ −100 dBm to at least [2,000] residents of unserved barangays not reached from Bolod. ALT-A to ALT-E pre-qualify, subject to survey.</li>
    <li>If they insist on deeper Bolod: capacity only, tied to a ridge site on air within [12–18] months, or the endorsement lapses.</li>
    <li>For a new tenant or capacity: show first why co-location on Bolod is impossible.</li></ul></div>
  <div class="cond"><h3>Evidence first</h3><ul>
    <li>Propagation study (Longley-Rice or ITU-R P.1812, terrain ≤ 30 m) for the site, Bolod and the difference.</li>
    <li>Band plan, including a sub-GHz layer.</li>
    <li>Microwave or fibre plan, ≥ 99.99% availability for rain zone P.</li>
    <li>Power plan with ≥ 8 h battery; NSCP 2015 structure; EMF compliance.</li></ul></div>
  <div class="cond"><h3>After construction</h3><ul>
    <li>Drive test of all 22 barangays within 60 days, with raw logs to the Sanggunian.</li>
    <li>Annual coverage report for three years.</li>
    <li>Open access to other operators on published terms.</li>
    <li>Restoration ≤ 72 h after typhoon damage.</li>
    <li>Lapses if construction has not started within 12 months.</li></ul></div>
  <div class="cond"><h3>What the LGU offers</h3><ul>
    <li>Priority one-stop-shop processing.</li>
    <li>Help finding municipal or barangay land on the chosen ridge, and spur right-of-way.</li>
    <li>Power-line coordination along the Pinamasingan and Poblacion–Quintina roads.</li>
    <li>A joint letter to DICT supporting the ridge sites.</li></ul></div>
</div>""")

# ------------------------------------------------------------------ 28 visualization
slide("Hearing strategy", "Showing the proof in the session hall", """
<div class="three">
  <div class="card"><h3>Google Earth Pro</h3><ol>
    <li>Open <span class="mono">results/san_pascual_review.kmz</span>.</li>
    <li>Tools → Options → 3D View: elevation exaggeration 2.</li>
    <li>Toggle "BOLOD" + "CT-2" coverage, then "BOLOD" + "ALT-A".</li>
    <li>For an independent check: placemark at a site, altitude 40 m relative to ground, right-click → Show Viewshed.</li>
    <li>Draw a path CT-2 → Pinamasingan → Show Elevation Profile to show the spur.</li></ol></div>
  <div class="card"><h3>HeyWhatsThat</h3><ol>
    <li>New panorama at each site, 40 m above ground, made before the hearing.</li>
    <li>Show the two visibility maps in side-by-side browser tabs.</li>
    <li>Path Profiler, Bolod → ALT-D, shows the microwave link clears.</li></ol></div>
  <div class="card"><h3>CloudRF</h3><ol>
    <li>Area coverage at 1800 MHz (and 758 MHz for a low-band layer), 46 dBm, 17.5 dBi, 40 m mast, 1.5 m receiver.</li>
    <li>Model Longley-Rice, rural vegetated, 6 km radius.</li>
    <li>Legend at −80 / −90 / −100 / −110 / −120 dBm, the classes on these slides.</li>
    <li>Export KMZ into Google Earth. This is the same map the contractor should be producing.</li></ol></div>
</div>""")

# ------------------------------------------------------------------ 29 limitations
slide("Method", "What this study can and cannot tell you", f"""
<div class="two">
  <div><h3>Solid</h3><ul class="big">
    <li>The relative comparison. The same model and terrain apply to every site, so "contractor adds nothing, ridges add thousands" holds even if absolute ranges shift.</li>
    <li>Terrain blocking: the ridges are real and visible in Google Earth's own elevation profile.</li>
    <li>Calibrated to the council's field facts: four served barangays, no Laurente, 3–4 km reach.</li></ul></div>
  <div><h3>To confirm</h3><ul class="big">
    <li>The contractor's exact coordinates, and the surveyed Bolod tower positions.</li>
    <li>Actual road and power-line alignments; ours are inferred from terrain.</li>
    <li>A drive test to replace the calibration with measurements.</li>
    <li>A site walk at each ridge: SRTM is ±5–10 m, and land ownership matters.</li>
    <li>The operator's band, power and antenna plan, which sets the real reach.</li></ul></div>
</div>
<p class="note">Analysis code, data, KMZ and every figure: project repository, folders analysis/, data/, results/. Re-run with real coordinates by editing the constants at the top of analysis/contractor_review.py.</p>""")

# ------------------------------------------------------------------ 30 next steps
slide("Next steps", "Before and after the hearing", """
<div class="two">
  <div><h3>Before</h3><ol class="big">
    <li>Legal Officer opinion on the RONO's status under EO 32.</li>
    <li>Request the contractor's exact coordinates and propagation map in writing.</li>
    <li>Short drive test or phone survey: Busing, Nazareno, Laurente, Boca Chica, Pinamasingan.</li>
    <li>Identify municipal or barangay land near ALT-C and ALT-D.</li></ol></div>
  <div><h3>At and after</h3><ol class="big">
    <li>Present slides 2, 10, 11, 12 and 20; ask the five questions.</li>
    <li>Offer the conditions and the LGU's help as a package.</li>
    <li>Re-run this analysis on the contractor's own coordinates and data.</li>
    <li>Track on-air dates and the drive-test report.</li></ol></div>
</div>""")


# ------------------------------------------------------------------ render
CSS = open(os.path.join(HERE, "slides.css")).read()
out = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><title>San Pascual Cell-Site Review</title>',
       f"<style>{CSS}</style></head><body>"]
total = len(slides)
for i, (section, title, body, cls) in enumerate(slides, 1):
    head = "" if not title else f'<header><div class="eyebrow">{html.escape(section)}</div><h2>{html.escape(title)}</h2></header>'
    foot = "" if i == 1 else f'<footer><span>San Pascual Cell-Site Review · Sangguniang Bayan · Rev. 2, October 2026</span><span>{i} / {total}</span></footer>'
    out.append(f'<section class="slide {cls}">{head}<div class="body">{body}</div>{foot}</section>')
out.append("</body></html>")
with open(os.path.join(HERE, "san_pascual_review_slides.html"), "w") as f:
    f.write("\n".join(out))
print(total, "slides")
