"""Replace the hand-drawn coastline with real Natural Earth 1:10m data.

Inputs: world-atlas land-10m.json (TopoJSON) and Natural Earth ne_10m_lakes.geojson.
Run:    python -I map3d/tools/make_coastline.py <land-10m.json> <ne_10m_lakes.geojson>
Output: map3d/blender/data/coastline.json (same schema the Blender scripts read);
        the old hand-drawn file is kept as coastline_handdrawn.json.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'blender/data'
# real lake surface levels (m above sea level)
LAKE_LEVELS = {'Tekapo': 710, 'Pukaki': 518, 'Ohau': 520, 'Wanaka': 278, 'Hawea': 348,
               'Wakatipu': 310, 'Te Anau': 204, 'Manapouri': 178}


def decode_topo(topo):
    sx, sy = topo['transform']['scale']; tx, ty = topo['transform']['translate']
    arcs = []
    for arc in topo['arcs']:
        x = y = 0; pts = []
        for dx, dy in arc:
            x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            p = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(p if not out else p[1:])
        return out
    polys = []
    for g in topo['objects']['land']['geometries']:
        for poly in (g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]):
            polys.append(ring(poly[0]))
    return polys


def area(r):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:] + r[:1])) / 2)


def simplify(pts, tol):
    keep = [False] * len(pts); keep[0] = keep[-1] = True; stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy or 1e-18
        best, bi = 0, -1
        for i in range(a + 1, b):
            x, y = pts[i]; t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L)); d = (x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2
            if d > best: best, bi = d, i
        if best > tol * tol and bi > 0: keep[bi] = True; stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def clip_south_of(ring, lat_max):
    """Sutherland-Hodgman clip keeping lat <= lat_max."""
    out = []
    for i in range(len(ring)):
        cur, prev = ring[i], ring[i - 1]
        cin, pin = cur[1] <= lat_max, prev[1] <= lat_max
        if cin != pin:
            t = (lat_max - prev[1]) / (cur[1] - prev[1]); out.append((prev[0] + t * (cur[0] - prev[0]), lat_max))
        if cin: out.append(cur)
    return out


def main(land_path, lakes_path):
    polys = decode_topo(json.loads(Path(land_path).read_text(encoding='utf-8')))
    nz = [p for p in polys if all(165 < x < 179.9 and -48 < y < -34 for x, y in p)]
    nz.sort(key=area, reverse=True)
    def pick(lon, lat):
        for p in nz:
            if min(x for x, _ in p) < lon < max(x for x, _ in p) and min(y for _, y in p) < lat < max(y for _, y in p):
                return p
    south, north, stewart = pick(170.5, -43.5), pick(175.5, -39.0), pick(167.9, -47.0)
    rnd = lambda r: [[round(x, 4), round(y, 4)] for x, y in r]
    land = [{'name': 'SouthIsland', 'ring': rnd(simplify(south, 0.0012))},
            {'name': 'StewartIsland', 'ring': rnd(simplify(stewart, 0.002))},
            {'name': 'NorthIslandHint', 'ring': rnd(simplify(clip_south_of(north, -40.55), 0.01))}]
    for l in land:
        if l['ring'][0] == l['ring'][-1]: l['ring'].pop()
        print('%-16s %5d points' % (l['name'], len(l['ring'])))

    gj = json.loads(Path(lakes_path).read_text(encoding='utf-8'))
    lakes = []
    for f in gj['features']:
        name = (f['properties'].get('name') or '').replace('Lake ', '').strip()
        key = next((k for k in LAKE_LEVELS if k.lower() == name.lower() or k.replace(' ', '').lower() == name.replace(' ', '').lower()), None)
        if not key: continue
        g = f['geometry']; polys2 = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        outer = max((p[0] for p in polys2), key=area)
        if not all(166 < x < 175 and -47 < y < -41 for x, y in outer): continue
        r = rnd(simplify([tuple(p) for p in outer], 0.001))
        if r[0] == r[-1]: r.pop()
        if len(r) < 4: continue
        if any(l['name'] == key and len(l['ring']) >= len(r) for l in lakes): continue
        lakes = [l for l in lakes if l['name'] != key]
        lakes.append({'name': key, 'elevation_m': LAKE_LEVELS[key], 'ring': r})
        print('lake %-10s %4d points' % (key, len(r)))
    missing = set(LAKE_LEVELS) - {l['name'] for l in lakes}
    if missing: print('MISSING lakes (not in Natural Earth 10m):', sorted(missing))

    old = DATA / 'coastline.json'; backup = DATA / 'coastline_handdrawn.json'
    prev = json.loads(old.read_text(encoding='utf-8'))
    if not backup.exists(): backup.write_text(old.read_text(encoding='utf-8'), encoding='utf-8')
    # keep hand-drawn rings only for lakes Natural Earth lacks
    for l in prev['lakes']:
        if l['name'] in missing: lakes.append(l)
    prev.update({'land': land, 'lakes': lakes, 'provenance': {
        'source': 'Natural Earth 1:10m land (via world-atlas@2.0.2) and ne_10m_lakes; public domain.',
        'license': 'Public domain (Natural Earth).', 'accuracy': '1:10,000,000 scale, about 1 km; simplified with 0.004 degree tolerance.',
        'lake_levels': 'Surface elevations in metres from published lake levels.'}})
    old.write_text(json.dumps(prev, separators=(',', ':')), encoding='utf-8')
    print('wrote', old)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
