"""Fetch real elevations (LINZ NZ 8 m DEM via the public OpenTopoData API, dataset nzdem8m).

1. A lon/lat grid (~2.8 km) over the South Island + Stewart Island, land cells plus a
   one-cell coastal buffer, written to map3d/blender/data/dem_grid.json.
2. The elevation of every road point in map3d/web_assets/routes.json (adds an "elev" list
   per route, in metres).

Run: python -I map3d/tools/fetch_elevation.py   (about 4 minutes; the API allows 1 call/s,
100 points/call, 1000 calls/day)
"""
import json, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DLAT, DLON = 0.025, 0.035
API = 'https://api.opentopodata.org/v1/nzdem8m?locations='


def inside(x, y, ring):
    c = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            c = not c
    return c


def query(points):
    """points: list of (lat, lon) -> list of metres (None at sea)."""
    out = []
    for i in range(0, len(points), 100):
        chunk = points[i:i+100]
        url = API + '|'.join('%.5f,%.5f' % p for p in chunk)
        for attempt in range(5):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'honeymoon-map/1.0'})
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.load(r)
                if data.get('status') != 'OK':
                    raise RuntimeError(data)
                out += [res['elevation'] for res in data['results']]
                break
            except Exception as exc:  # rate limit or transient error: back off
                print('  retry', attempt, exc)
                time.sleep(3 + attempt * 3)
        else:
            raise RuntimeError('elevation fetch failed')
        time.sleep(1.05)
        if (i // 100) % 20 == 0:
            print('  %d / %d' % (i + len(chunk), len(points)))
    return out


def main():
    coast = json.loads((ROOT / 'blender/data/coastline.json').read_text(encoding='utf-8'))
    rings = [r['ring'] for r in coast['land'] if r['name'] in ('SouthIsland', 'StewartIsland')]
    lat0, lat1, lon0, lon1 = -47.35, -40.4, 166.3, 174.5
    nlat, nlon = int((lat1 - lat0) / DLAT) + 1, int((lon1 - lon0) / DLON) + 1
    land = [[any(inside(lon0 + j * DLON, lat0 + i * DLAT, r) for r in rings) for j in range(nlon)] for i in range(nlat)]
    want = [[land[i][j] or any(land[a][b] for a in range(max(0, i-1), min(nlat, i+2)) for b in range(max(0, j-1), min(nlon, j+2)))
             for j in range(nlon)] for i in range(nlat)]
    cells = [(i, j) for i in range(nlat) for j in range(nlon) if want[i][j]]
    print('grid %dx%d, querying %d cells' % (nlat, nlon, len(cells)))
    elev = query([(lat0 + i * DLAT, lon0 + j * DLON) for i, j in cells])
    grid = [None] * (nlat * nlon)
    for (i, j), e in zip(cells, elev):
        grid[i * nlon + j] = 0.0 if e is None else round(max(e, 0.0), 1)
    (ROOT / 'blender/data/dem_grid.json').write_text(json.dumps({
        'source': 'LINZ NZ 8m DEM (nzdem8m) sampled via api.opentopodata.org. CC BY 4.0 LINZ.',
        'lat0': lat0, 'lon0': lon0, 'dlat': DLAT, 'dlon': DLON, 'nlat': nlat, 'nlon': nlon,
        'note': 'row-major from lat0 (south) upward; null = not sampled (open sea); metres',
        'elev': grid}, separators=(',', ':')), encoding='utf-8')
    print('wrote dem_grid.json')

    rpath = ROOT / 'web_assets/routes.json'
    routes = json.loads(rpath.read_text(encoding='utf-8'))
    for key, r in routes['routes'].items():
        e = query([tuple(p) for p in r['points']])
        r['elev'] = [0.0 if v is None else round(v, 1) for v in e]
        print('route %-16s max %.0f m' % (key, max(r['elev'])))
    routes['elevation_source'] = 'LINZ NZ 8m DEM via api.opentopodata.org (CC BY 4.0 LINZ)'
    rpath.write_text(json.dumps(routes, separators=(',', ':')), encoding='utf-8')
    print('updated routes.json')


if __name__ == '__main__':
    main()
