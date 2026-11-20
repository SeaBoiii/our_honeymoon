"""Make sure every real road sits on land.

The 1:10m Natural Earth coast is 1-3 km off on coast-hugging roads (SH6 on the West Coast,
Akaroa harbour). This rasterises land = (inside the coast) OR (within ~750 m of any road),
keeps the South Island component, traces its outline and writes it back as the SouthIsland
ring in coastline.json.

Run after make_coastline.py:  python -I map3d/tools/fit_coast_to_roads.py
"""
import json, math
from collections import deque
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CPATH = ROOT / 'blender/data/coastline.json'
LON0, LON1, LAT0, LAT1 = 166.2, 174.6, -47.0, -40.3
DLON, DLAT = 0.005, 0.0035          # ~400 m cells
BUF_KM = 0.75


def main():
    coast = json.loads(CPATH.read_text(encoding='utf-8'))
    si = next(l for l in coast['land'] if l['name'] == 'SouthIsland')
    ring = np.array(si['ring'], dtype=float)
    nx, ny = int((LON1 - LON0) / DLON) + 1, int((LAT1 - LAT0) / DLAT) + 1
    xs = LON0 + np.arange(nx) * DLON
    mask = np.zeros((ny, nx), dtype=bool)
    ax, ay = ring[:, 0], ring[:, 1]; bx, by = np.roll(ax, -1), np.roll(ay, -1)
    for j in range(ny):  # scanline polygon fill
        y = LAT0 + j * DLAT
        hit = (ay > y) != (by > y)
        if not hit.any(): continue
        cx = np.sort(ax[hit] + (y - ay[hit]) * (bx[hit] - ax[hit]) / (by[hit] - ay[hit]))
        for a, b in zip(cx[0::2], cx[1::2]):
            mask[j, (xs >= a) & (xs <= b)] = True
    land_cells = mask.sum()
    routes = json.loads((ROOT / 'web_assets/routes.json').read_text(encoding='utf-8'))['routes']
    for r in routes.values():  # road buffer
        pts = r['points']
        for (la1, lo1), (la2, lo2) in zip(pts, pts[1:]):
            k = math.cos(math.radians(la1)); rlat = BUF_KM / 111.0; rlon = rlat / k
            i0 = max(0, int((min(lo1, lo2) - rlon - LON0) / DLON)); i1 = min(nx - 1, int((max(lo1, lo2) + rlon - LON0) / DLON) + 1)
            j0 = max(0, int((min(la1, la2) - rlat - LAT0) / DLAT)); j1 = min(ny - 1, int((max(la1, la2) + rlat - LAT0) / DLAT) + 1)
            gx, gy = np.meshgrid(LON0 + np.arange(i0, i1 + 1) * DLON, LAT0 + np.arange(j0, j1 + 1) * DLAT)
            dx, dy = (lo2 - lo1) * k, la2 - la1; px, py = (gx - lo1) * k, gy - la1
            t = np.clip((px * dx + py * dy) / ((dx * dx + dy * dy) or 1e-18), 0, 1)
            d = np.hypot(px - t * dx, py - t * dy) * 111.0
            mask[j0:j1 + 1, i0:i1 + 1] |= d <= BUF_KM
    print('land cells %d -> %d with road buffer' % (land_cells, mask.sum()))
    # keep the component containing inland Canterbury (BFS, 4-neighbour)
    sj, si_ = int((-43.6 - LAT0) / DLAT), int((171.8 - LON0) / DLON)
    keep = np.zeros_like(mask); keep[sj, si_] = True; q = deque([(sj, si_)])
    while q:
        j, i = q.popleft()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = j + dj, i + di
            if 0 <= a < ny and 0 <= b < nx and mask[a, b] and not keep[a, b]:
                keep[a, b] = True; q.append((a, b))
    # fill interior holes (lakes etc. are handled separately): flood the outside instead
    outside = np.zeros_like(keep); q = deque()
    for j in range(ny):
        for i in (0, nx - 1):
            if not keep[j, i]: outside[j, i] = True; q.append((j, i))
    for i in range(nx):
        for j in (0, ny - 1):
            if not keep[j, i] and not outside[j, i]: outside[j, i] = True; q.append((j, i))
    while q:
        j, i = q.popleft()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = j + dj, i + di
            if 0 <= a < ny and 0 <= b < nx and not keep[a, b] and not outside[a, b]:
                outside[a, b] = True; q.append((a, b))
    solid = ~outside
    # Moore-neighbour boundary trace, starting from the bottom-most then left-most cell
    js, is_ = np.nonzero(solid); start = (js.min(), is_[js == js.min()].min())
    nbr = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
    boundary = [start]; cur = start; back = 0  # we entered from the west
    while True:
        for k in range(8):
            d = (back + 1 + k) % 8
            a, b = cur[0] + nbr[d][0], cur[1] + nbr[d][1]
            if 0 <= a < ny and 0 <= b < nx and solid[a, b]:
                back = (d + 4) % 8; cur = (a, b); break
        if cur == start: break
        boundary.append(cur)
        if len(boundary) > 2_000_000: raise RuntimeError('trace did not close')
    pts = [(LON0 + i * DLON, LAT0 + j * DLAT) for j, i in boundary]

    def simplify(p, tol):
        keepf = [False] * len(p); keepf[0] = keepf[-1] = True; st = [(0, len(p) - 1)]
        while st:
            a, b = st.pop(); (x1, y1), (x2, y2) = p[a], p[b]; dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy or 1e-18; best, bi = 0, -1
            for i in range(a + 1, b):
                x, y = p[i]; t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L)); d = (x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2
                if d > best: best, bi = d, i
            if best > tol * tol and bi > 0: keepf[bi] = True; st += [(a, bi), (bi, b)]
        return [q2 for q2, f in zip(p, keepf) if f]
    ring2 = simplify(pts, 0.0025)

    def inside(x, y, rr):
        c = False
        for (ax_, ay_), (bx_, by_) in zip(rr, rr[1:] + rr[:1]):
            if (ay_ > y) != (by_ > y) and x < ax_ + (y - ay_) * (bx_ - ax_) / (by_ - ay_): c = not c
        return c
    off = sum(not inside(p[1], p[0], ring2) for r in routes.values() for p in r['points'])
    print('traced %d boundary cells -> %d ring points; road points offshore: %d' % (len(pts), len(ring2), off))
    si['ring'] = [[round(x, 5), round(y, 5)] for x, y in ring2]
    coast['provenance']['road_fit'] = 'Natural Earth 1:10m coast unioned with a 750 m buffer around every road (OpenStreetMap via OSRM), traced at ~400 m.'
    CPATH.write_text(json.dumps(coast, separators=(',', ':')), encoding='utf-8')
    print('wrote', CPATH)


if __name__ == '__main__':
    main()
