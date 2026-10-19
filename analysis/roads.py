"""Terrain-inferred road corridor proxy for San Pascual.

No OpenStreetMap extract was reachable from the analysis environment, so the
road network is approximated by least-slope paths between barangay centres
along the known DPWH corridors (Poblacion-Quintina Road via Pinamasingan, the
west-coast road via San Rafael/Santa Cruz, the north-coast road to Laurente,
and the inland Pinamasingan-San Pedro-Mapanique link).  Swap in the real
centreline (KML/GeoJSON from Google Earth or OSM) when available.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

GRID = 3.0 / 3600.0          # 3 arcsec (~92 m) routing grid
LAT_N, LAT_S = 13.17, 12.95
LON_W, LON_E = 122.93, 123.15

# barangay chains that roads are known (or very likely) to connect
CORRIDORS = {
    "Poblacion-Pinamasingan-Quintina Rd": ["Bolod (Poblacion)", "Pinamasingan", "Cueva", "Dangcalan", "Halabangbaybay", "Quintina"],
    "North coast to Laurente": ["Bolod (Poblacion)", "Nazareno", "Laurente", "Cueva"],
    "West coast road": ["Bolod (Poblacion)", "Boca Chica", "San Rafael", "Santa Cruz", "Mabuhay", "Mabini", "Ki-Romero", "Malaking Ilog", "San Jose", "Ki-Buaya", "Quintina"],
    "Inland Pinamasingan-San Pedro-Mapanique": ["Pinamasingan", "San Pedro", "Mapanique", "Malaking Ilog"],
}


class RoadProxy:
    def __init__(self, dem, brgys):
        self.lats = np.arange(LAT_N, LAT_S, -GRID)
        self.lons = np.arange(LON_W, LON_E, GRID)
        LA, LO = np.meshgrid(self.lats, self.lons, indexing="ij")
        self.z = dem.elev(LA, LO)
        self.shape = self.z.shape
        self._graph()
        self.by_name = {b["barangay"]: b for b in brgys}
        self.paths = {name: self._chain(ch) for name, ch in CORRIDORS.items()}

    def _graph(self):
        ny, nx = self.shape
        dy = 111_320.0 * GRID
        dx = dy * np.cos(np.radians((LAT_N + LAT_S) / 2))
        idx = np.arange(ny * nx).reshape(ny, nx)
        rows, cols, w = [], [], []
        sea = self.z <= 1.0
        for di, dj in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            a = idx[max(0, -di):ny - max(0, di), max(0, -dj):nx - max(0, dj)]
            b = idx[max(0, di):ny - max(0, -di) or None, max(0, dj):nx - max(0, -dj) or None]
            za, zb = self.z.flat[a], self.z.flat[b]
            run = np.hypot(di * dy, dj * dx)
            slope = np.abs(zb - za) / run
            cost = run * (1 + 400 * slope ** 2) * (1 + 0.004 * np.maximum(za, zb))  # prefer flat, low ground
            cost = np.where(sea.flat[a] | sea.flat[b], run * 50, cost)              # keep off the sea
            rows += [a.ravel(), b.ravel()]
            cols += [b.ravel(), a.ravel()]
            w += [cost.ravel(), cost.ravel()]
        n = ny * nx
        self.G = coo_matrix((np.concatenate(w), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()

    def node(self, lat, lon):
        i = int(round((LAT_N - lat) / GRID))
        j = int(round((lon - LON_W) / GRID))
        return int(np.clip(i, 0, self.shape[0] - 1) * self.shape[1] + np.clip(j, 0, self.shape[1] - 1))

    def latlon(self, n):
        i, j = divmod(int(n), self.shape[1])
        return float(self.lats[i]), float(self.lons[j])

    def route(self, a, b):
        s, t = self.node(*a), self.node(*b)
        _, pred = dijkstra(self.G, indices=s, return_predecessors=True)
        out, n = [], t
        while n != s and n >= 0:
            out.append(self.latlon(n))
            n = pred[n]
        out.append(self.latlon(s))
        return out[::-1]

    def _chain(self, names):
        pts = []
        for a, b in zip(names, names[1:]):
            A, B = self.by_name[a], self.by_name[b]
            seg = self.route((A["lat"], A["lon"]), (B["lat"], B["lon"]))
            pts += seg if not pts else seg[1:]
        return pts

    def all_points(self):
        return np.array([p for path in self.paths.values() for p in path])

    def dist_to_road_m(self, lat, lon):
        P = self.all_points()
        kx = 111_320.0 * np.cos(np.radians(lat))
        return float(np.min(np.hypot((P[:, 1] - lon) * kx, (P[:, 0] - lat) * 111_320.0)))
