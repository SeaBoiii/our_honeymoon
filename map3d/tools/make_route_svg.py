"""Build an inline SVG route map (coastline + real road routes + stops) for the summary page.
Uses the same projection as the 3D map. Run: python -I map3d/tools/make_route_svg.py
Writes map3d/tools/route_map.svg (paste into honeymoon.html)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KX, KY = 8.008, 11.132
coast = json.loads((ROOT / 'blender/data/coastline.json').read_text(encoding='utf-8'))
routes = json.loads((ROOT / 'web_assets/routes.json').read_text(encoding='utf-8'))['routes']
lakes = coast['lakes']

X0, X1, Y0, Y1 = 166.3, 174.4, -47.4, -40.4
S = 8.5  # svg px per projected 10-km unit


def pt(lon, lat):
    return (lon - X0) * KX * S, (Y1 - lat) * KY * S


W, H = pt(X1, Y0)


def path(coords, close=False, step=1):
    pts = [pt(lon, lat) for lon, lat in coords[::step]]
    d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts)
    return d + (' Z' if close else '')


out = ['<svg viewBox="0 0 %d %d" role="img" aria-labelledby="mapT" class="routemap">' % (W, H),
       '<title id="mapT">Route map: the honeymoon loop on New Zealand\'s South Island</title>']
for land in coast['land']:
    if land['name'] == 'NorthIslandHint':
        continue
    out.append('<path class="land" d="%s"/>' % path(land['ring'], True, 2))
for lake in lakes:
    out.append('<path class="lake" fill-rule="evenodd" d="%s"/>' % ' '.join(path(ring, True) for ring in [lake['ring'],*lake.get('islands',[])]))
drive = ['air-chc', 'chc-tekapo', 'tekapo-twizel', 'twizel-mtcook', 'mtcook-wanaka', 'wanaka-teanau', 'teanau-qt',
         'qt-coronet', 'coronet-onsen', 'onsen-glenorchy', 'glenorchy-qt', 'qt-franz', 'franz-chc', 'chc-akaroa', 'akaroa-air']
for k in drive:
    out.append('<path class="road" d="%s"/>' % path([(p[1], p[0]) for p in routes[k]['points']]))
out.append('<path class="coach" d="%s"/>' % path([(p[1], p[0]) for p in routes['teanau-milford']['points']]))
stops = [('Christchurch', 172.60, -43.531, 'e'), ('Lake Tekapo', 170.48, -44.005, 'e'), ('Aoraki/Mt Cook', 170.096, -43.735, 'w'),
         ('Wānaka', 169.135, -44.70, 'e'), ('Te Anau', 167.718, -45.414, 'w'), ('Queenstown', 168.662, -45.031, 'e'),
         ('Franz Josef', 170.183, -43.387, 'w'), ('Milford Sound', 167.926, -44.672, 'w'), ('Akaroa', 172.968, -43.804, 'e')]
for name, lon, lat, side in stops:
    x, y = pt(lon, lat)
    dx, anchor = (9, 'start') if side == 'e' else (-9, 'end')
    out.append('<circle class="stop" cx="%.1f" cy="%.1f" r="5"/><text x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (x, y, x + dx, y + 4, anchor, name))
out.append('</svg>')
(ROOT / 'tools/route_map.svg').write_text('\n'.join(out), encoding='utf-8')
print('wrote route_map.svg', int(W), 'x', int(H), sum(len(s) for s in out), 'bytes')
