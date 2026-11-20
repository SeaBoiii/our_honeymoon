"""Fetch real road geometry (OpenStreetMap via the public OSRM router) for every
drive/coach leg of the honeymoon and write map3d/web_assets/routes.json.

Run:  python -I map3d/tools/fetch_routes.py
Waypoints are (lat, lon). Via-points force the intended roads
(e.g. Cromwell instead of the Crown Range, Lindis Pass, Haast Pass, Arthur's Pass).
"""
import json, time, urllib.request, sys
from pathlib import Path

AIR=(-43.489,172.532); CHC=(-43.531,172.600); TEK=(-44.005,170.480); TWZ=(-44.258,170.098)
MTC=(-43.735,170.096); WAN=(-44.700,169.135); TEA=(-45.414,167.718); QT=(-45.031,168.662)
FJ=(-43.387,170.183); MIL=(-44.6715,167.9265); AKA=(-43.804,172.968)
GERALDINE=(-44.09,171.24); FAIRLIE=(-44.10,170.83); OMARAMA=(-44.487,169.968); TARRAS=(-44.835,169.41)
CROMWELL=(-45.04,169.20); FRANKTON=(-45.02,168.73); CORONET=(-44.926,168.736); ONSEN=(-44.991,168.677)
GLEN=(-44.851,168.388); MAKARORA=(-44.23,169.23); HAAST=(-43.88,169.04); FOX=(-43.465,170.017)
HOKITIKA=(-42.717,170.967); ARTHURS=(-42.94,171.56); LITTLE_RIVER=(-43.77,172.79)

ROUTES = {
    'air-chc':        [AIR, CHC],
    'chc-tekapo':     [CHC, GERALDINE, FAIRLIE, TEK],
    'tekapo-twizel':  [TEK, TWZ],
    'twizel-mtcook':  [TWZ, MTC],
    'mtcook-wanaka':  [MTC, OMARAMA, TARRAS, WAN],
    'wanaka-teanau':  [WAN, CROMWELL, FRANKTON, TEA],
    'teanau-milford': [TEA, MIL],
    'milford-teanau': [MIL, TEA],
    'teanau-qt':      [TEA, QT],
    'qt-coronet':     [QT, CORONET],
    'coronet-onsen':  [CORONET, ONSEN],
    'onsen-glenorchy':[ONSEN, QT, GLEN],
    'glenorchy-qt':   [GLEN, QT],
    'qt-franz':       [QT, FRANKTON, CROMWELL, WAN, MAKARORA, HAAST, FOX, FJ],
    'franz-chc':      [FJ, HOKITIKA, ARTHURS, CHC],
    'chc-akaroa':     [CHC, LITTLE_RIVER, AKA],
    'akaroa-air':     [AKA, LITTLE_RIVER, AIR],
}


def simplify(pts, tol):
    """Douglas-Peucker on (lat, lon) in degrees."""
    if len(pts) < 3:
        return pts
    keep = [False]*len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts)-1)]
    while stack:
        a, b = stack.pop()
        (y1, x1), (y2, x2) = pts[a], pts[b]
        dx, dy = x2-x1, y2-y1; L = (dx*dx+dy*dy) or 1e-18
        best, bi = 0, -1
        for i in range(a+1, b):
            y, x = pts[i]
            t = max(0, min(1, ((x-x1)*dx+(y-y1)*dy)/L))
            d = (x-x1-t*dx)**2+(y-y1-t*dy)**2
            if d > best: best, bi = d, i
        if best > tol*tol and bi > 0:
            keep[bi] = True; stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def fetch(waypoints):
    coords = ';'.join('%.5f,%.5f' % (lon, lat) for lat, lon in waypoints)
    url = 'https://router.project-osrm.org/route/v1/driving/%s?overview=full&geometries=geojson' % coords
    req = urllib.request.Request(url, headers={'User-Agent': 'honeymoon-map/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if data.get('code') != 'Ok':
        raise RuntimeError('OSRM error: %s' % data.get('message'))
    route = data['routes'][0]
    pts = [(round(lat, 5), round(lon, 5)) for lon, lat in route['geometry']['coordinates']]
    return pts, route['distance'], route['duration']


def main():
    out = {'source': 'OpenStreetMap road network via the public OSRM demo router (router.project-osrm.org). Data (c) OpenStreetMap contributors, ODbL.',
           'routes': {}}
    for key, wps in ROUTES.items():
        pts, dist, dur = fetch(wps)
        simple = simplify(pts, 0.0008)
        out['routes'][key] = {'km': round(dist/1000, 1), 'hours': round(dur/3600, 2), 'points': simple}
        print('%-16s %6.1f km %5.2f h  %5d -> %4d pts' % (key, dist/1000, dur/3600, len(pts), len(simple)))
        time.sleep(1.1)  # be polite to the demo server
    dest = Path(__file__).resolve().parents[1] / 'web_assets' / 'routes.json'
    dest.write_text(json.dumps(out, separators=(',', ':')), encoding='utf-8')
    print('wrote', dest, dest.stat().st_size, 'bytes')


if __name__ == '__main__':
    sys.exit(main())
