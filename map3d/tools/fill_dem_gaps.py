"""Fetch DEM samples for grid cells that the corrected coastline now covers but the first
pass (around the hand-drawn coast) never sampled. Run: python -I map3d/tools/fill_dem_gaps.py"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_elevation import query, inside  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
gpath = ROOT / 'blender/data/dem_grid.json'
g = json.loads(gpath.read_text(encoding='utf-8'))
coast = json.loads((ROOT / 'blender/data/coastline.json').read_text(encoding='utf-8'))
rings = [r['ring'] for r in coast['land'] if r['name'] in ('SouthIsland', 'StewartIsland')]
nlat, nlon, lat0, lon0, dlat, dlon = g['nlat'], g['nlon'], g['lat0'], g['lon0'], g['dlat'], g['dlon']
land = [[any(inside(lon0 + j * dlon, lat0 + i * dlat, r) for r in rings) for j in range(nlon)] for i in range(nlat)]
want = [(i, j) for i in range(nlat) for j in range(nlon)
        if g['elev'][i * nlon + j] is None and any(land[a][b] for a in range(max(0, i - 1), min(nlat, i + 2)) for b in range(max(0, j - 1), min(nlon, j + 2)))]
print('cells to fill:', len(want))
if want:
    vals = query([(lat0 + i * dlat, lon0 + j * dlon) for i, j in want])
    for (i, j), e in zip(want, vals):
        g['elev'][i * nlon + j] = 0.0 if e is None else round(max(e, 0.0), 1)
    gpath.write_text(json.dumps(g, separators=(',', ':')), encoding='utf-8')
print('done')
