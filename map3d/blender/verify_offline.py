"""Bpy-free geographic checks and a timed NumPy DEM/corridor dry run.

Run with python map3d/blender/verify_offline.py. This checks the actual math
used by build_terrain, but does not simulate Blender's CDT or GLB exporter.
"""
from pathlib import Path
import ast
import json
import math
import sys
from time import perf_counter
import numpy as np

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE/'scripts'))
from terrain_math import (
    DEMGrid, RoadCorridors, HEIGHT_SCALE, ROAD_OUTER, ROAD_SPACING,
    SAMPLE_LOCATIONS, inside, projected_points, carve_lake_beds,
    print_lake_stats, print_height_samples,
)

# Extract a few pure helpers without importing bpy or executing a build.
scope = {'math': math, 'np': np}
for filename, names in [
    ('common.py', {'project', 'elevation_z'}),
    ('build_terrain.py', {'signed_area', 'clean_ring'}),
]:
    tree = ast.parse((BASE/'scripts'/filename).read_text(encoding='utf-8'))
    pure = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
    exec(compile(pure, filename, 'exec'), scope)


def crossing(a, b, c, d):
    def orient(p, q, r):
        return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    return orient(a, b, c)*orient(a, b, d) < -1e-14 and orient(c, d, a)*orient(c, d, b) < -1e-14


def synthetic_checks():
    data = dict(lat0=-44., lon0=170.5, dlat=1., dlon=1., nlat=2, nlon=2,
                elev=[0., 100., 200., 300.])
    dem = DEMGrid(data)
    np.testing.assert_allclose(dem.sample_lonlat([170.5, 171.5, 171., 171.5], [-44., -44., -43.5, -43.]),
                               [0, 100, 150, 300], atol=1e-8)
    assert float(dem.sample_lonlat(170., -44.)) == 0
    null_dem = DEMGrid(dict(data, elev=[None, -100, 200, 300]))
    assert float(null_dem.sample_lonlat(171., -43.5)) == 125
    assert float(null_dem.sample_lonlat(170.5, -44.)) == 0
    np.testing.assert_allclose(scope['elevation_z'](np.array([0, 710, 3724])),
                               np.array([0, 710, 3724])*HEIGHT_SCALE)
    np.testing.assert_allclose(projected_points(170.142, -43.595), scope['project'](170.142, -43.595))

    def route(xy, elev=None):
        xy = np.asarray(xy, float)
        r = {'points': np.column_stack((xy[:, 1]/11.132-44, xy[:, 0]/8.008+170.5)).tolist()}
        if elev is not None:
            r['elev'] = elev
        return {'test': r}

    road = RoadCorridors(route([[0, 0], [1, 0]], [100, 300]), dem)
    xy = np.array([[.25, 0], [.25, .04], [.25, .08], [.25, .12], [.25, .12001], [.25, 0]])
    base = np.array([500, 500, 500, 500, 500, 100.])
    carved, adjustment = road.carve(xy, base)
    np.testing.assert_allclose(carved, [150, 150, 325, 500, 500, 100], atol=1e-8)
    assert np.all(carved <= base) and np.all(adjustment >= 0)
    assert np.max(np.diff(road.points[:, 0])) <= ROAD_SPACING+1e-7
    fallback = RoadCorridors(route([[0, 0], [1, 0]]), dem)
    expected = dem.sample(np.array([0., 1.]), np.zeros(2))
    distance, height = fallback.nearest([[.5, 0]])
    np.testing.assert_allclose(height, [expected.mean()], atol=1e-8)
    partial = RoadCorridors(route([[0, 0], [1, 0]], [100, None]), dem)
    assert partial.supplied_points == 1 and partial.fallback_points == 1
    empty = RoadCorridors({}, dem)
    np.testing.assert_array_equal(empty.carve(xy, base)[0], base)
    lake = {'xy': [[0, 0], [1, 0], [1, 1], [0, 1]], 'elevation_m': 200}
    bed = carve_lake_beds(np.array([[.5, .5], [0, .5], [2, 2], [.5, .5]]),
                         np.array([300., 300., 300., 100.]), [lake])
    np.testing.assert_allclose(bed, [192, 192, 300, 100])
    print('PASS: bilinear orientation, null/sea, 5x scale, nearest-segment grades, falloff, lower-only, fallback, lake beds')


def check_spatial_index(roads):
    """Compare the bounded index with an independent brute-force projection."""
    rng = np.random.default_rng(1847)
    segment = rng.integers(0, len(roads.a), 1200)
    xy = roads.a[segment]+roads.delta[segment]*rng.random((len(segment), 1))
    xy += rng.uniform(-.2, .2, xy.shape)
    indexed_d, indexed_h = roads.nearest(xy)
    brute_d, brute_h = [], []
    for start in range(0, len(xy), 128):
        offset = xy[start:start+128, None, :]-roads.a[None, :, :]
        t = np.clip(np.sum(offset*roads.delta, axis=2)/roads.length2, 0, 1)
        d2 = np.sum((offset-t[..., None]*roads.delta)**2, axis=2)
        chosen = np.argmin(d2, axis=1)
        row = np.arange(len(chosen))
        distance = np.sqrt(d2[row, chosen])
        active = distance <= ROAD_OUTER
        brute_d.extend(np.where(active, distance, np.inf))
        brute_h.extend(np.where(active, roads.ha[chosen]+roads.dh[chosen]*t[row, chosen], 0))
    np.testing.assert_allclose(indexed_d, brute_d, atol=1e-10)
    np.testing.assert_allclose(indexed_h, brute_h, atol=1e-7)
    print('PASS: spatial index matches brute-force nearest segments at 1200 route-adjacent queries')


def main():
    synthetic_checks()
    data = json.loads((BASE/'data/coastline.json').read_text(encoding='utf-8'))
    coasts = {}
    for record in data['land']+data['lakes']:
        ring = scope['clean_ring'](record['ring'])
        n = len(ring)
        assert len(set(ring)) == n, record['name']+' has duplicated vertices'
        for i in range(n):
            for j in range(i+2, n):
                if i == 0 and j == n-1:
                    continue
                assert not crossing(ring[i], ring[(i+1) % n], ring[j], ring[(j+1) % n]), record['name']+' self-intersects'
        if record in data['land']:
            coasts[record['name']] = ring
        else:
            pts = np.asarray(ring)
            assert inside(pts[:, 0], pts[:, 1], coasts['SouthIsland']).all(), record['name']+' leaves the land ring'
    for lon, lat in [(167.85, -44.60), (167.90, -44.64), (167.934, -44.666)]:
        x, y = scope['project'](lon, lat)
        assert not bool(inside(x, y, coasts['SouthIsland'])), 'Milford inlet blocked'
    print('PASS: all geographic rings simple, lakes inside land, Milford inlet open')

    dem = DEMGrid.load(BASE/'data/dem_grid.json')
    routes = json.loads((BASE.parent/'web_assets/routes.json').read_text(encoding='utf-8'))['routes']
    started = perf_counter()
    roads = RoadCorridors(routes, dem)
    print('[terrain] DEM %dx%d; %d valid nodes, range %.1f..%.1f m' %
          (dem.nlat, dem.nlon, dem.valid.sum(), dem.values.min(), dem.values.max()))
    print('[roads] %d segments, %d CDT controls; supplied elevations %d, DEM fallbacks %d' %
          (len(roads.a), len(roads.points), roads.supplied_points, roads.fallback_points))
    lakes = [dict(lake, xy=scope['clean_ring'](lake['ring'])) for lake in data['lakes']]
    print_lake_stats(dem, lakes)
    samples = projected_points([p[1] for p in SAMPLE_LOCATIONS], [p[2] for p in SAMPLE_LOCATIONS])
    original = dem.sample(samples[:, 0], samples[:, 1])
    h, _ = roads.carve(samples, original)
    h = carve_lake_beds(samples, h, lakes)
    print_height_samples(h, original, lakes)
    check_spatial_index(roads)

    estimated = 0
    max_adjustment = 0.
    point_count = 0
    for name, ring in coasts.items():
        main_island, hint = name == 'SouthIsland', name == 'NorthIslandHint'
        step = .15 if main_island else (.65 if hint else .23)
        lo, hi = np.min(ring, axis=0), np.max(ring, axis=0)
        xx, yy = np.meshgrid(np.arange(lo[0]+step*.47, hi[0], step), np.arange(lo[1]+step*.41, hi[1], step))
        xy = np.column_stack((xx.ravel(), yy.ravel()))
        xy = xy[inside(xy[:, 0], xy[:, 1], ring)]
        grid_count = len(xy)
        if not hint:
            rp = roads.points[inside(roads.points[:, 0], roads.points[:, 1], ring)]
            extra = [np.asarray(ring), rp]
            if main_island:
                extra += [np.asarray(lake['xy']) for lake in lakes]+[samples]
            xy = np.vstack([xy]+extra)
            metres = dem.sample(xy[:, 0], xy[:, 1])
            carved, adjustment = roads.carve(xy, metres)
            assert np.isfinite(carved).all() and np.all(carved >= 0) and np.all(carved <= metres)
            assert np.all(carved[adjustment == 0] == metres[adjustment == 0])
            max_adjustment = max(max_adjustment, float(adjustment.max(initial=0)))
            if main_island:
                beds = carve_lake_beds(xy, carved, lakes)
                assert np.all(beds <= carved) and np.all(beds >= 0)
                # Exercise the complete no-elev path on the same full grid.
                fallback = RoadCorridors({k: {'points': r['points']} for k, r in routes.items()}, dem)
                fallback_h, fallback_adjustment = fallback.carve(xy, metres)
                assert fallback.supplied_points == 0 and fallback.fallback_points == sum(len(r['points']) for r in routes.values())
                assert np.isfinite(fallback_h).all() and np.all(fallback_h <= metres)
                print('[roads] All-elev-absent fallback max lowering: %.1f m' % fallback_adjustment.max(initial=0))
        # Euler estimate, before CDT deduplication, constraint intersections and clipping.
        count = (2*len(xy)-len(ring)-2) if not hint else (2*grid_count+len(ring)-2)
        estimated += count
        point_count += len(xy)
        print('[dry run] %s: %d grid points, ~%d land triangles including road controls' % (name, grid_count, count))
    for lake in lakes:
        ring = lake['xy']
        lo, hi = np.min(ring, axis=0), np.max(ring, axis=0)
        xx, yy = np.meshgrid(np.arange(lo[0]+.15*.47, hi[0], .15), np.arange(lo[1]+.15*.41, hi[1], .15))
        estimated += 2*int(inside(xx.ravel(), yy.ravel(), ring).sum())+len(ring)-2
    assert 120000 <= estimated <= 250000, 'Grid density estimate misses budget'
    print('[terrain] Estimated total triangles: %d (actual CDT count requires Blender)' % estimated)
    print('[roads] Max road-corridor adjustment: %.1f m / Z %.5f (lowering only)' % (max_adjustment, max_adjustment*HEIGHT_SCALE))
    print('[dry run] %d candidate terrain vertices; %.2f s including both road-elevation modes and checks' % (point_count, perf_counter()-started))
    print('PASS: DEM/carving dry run; Blender CDT, GLB bytes, render and total build time still require live execution')


if __name__ == '__main__':
    main()
