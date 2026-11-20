"""Render an equirectangular land/ocean texture for the globe intro.

Input: world-atlas land-50m.json (Natural Earth 1:50m land, public domain) as TopoJSON.
Run:   python -I map3d/tools/make_earth.py <path-to-land-50m.json>
Output: map3d/web_assets/earth.png (4096 x 2048)
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

W, H = 4096, 2048
OCEAN = (36, 98, 128)
OCEAN_SHELF = (52, 122, 150)
LAND = (226, 214, 182)
COAST = (174, 158, 120)


def decode(topo):
    sx, sy = topo['transform']['scale']; tx, ty = topo['transform']['translate']
    arcs = []
    for arc in topo['arcs']:
        x = y = 0; pts = []
        for dx, dy in arc:
            x += dx; y += dy
            pts.append((x*sx+tx, y*sy+ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(pts if not out else pts[1:])
        return out

    polys = []
    for g in topo['objects']['land']['geometries']:
        parts = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
        for poly in parts:
            polys.append([ring(r) for r in poly])
    return polys


def px(lon, lat):
    return ((lon+180)/360*W, (90-lat)/180*H)


def main(src):
    polys = decode(json.loads(Path(src).read_text(encoding='utf-8')))
    mask = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(mask)
    def unwrap(ring):
        # rings that cross the antimeridian: make longitudes continuous
        out = [list(ring[0])]
        for lon, lat in ring[1:]:
            prev = out[-1][0]
            while lon - prev > 180: lon -= 360
            while lon - prev < -180: lon += 360
            out.append([lon, lat])
        return out

    for poly in polys:
        rings = [unwrap(r) for r in poly]
        for shift in (-360, 0, 360):  # draw wrapped copies so nothing is cut at the edges
            d.polygon([px(lon+shift, lat) for lon, lat in rings[0]], fill=255)
            for h in rings[1:]:
                d.polygon([px(lon+shift, lat) for lon, lat in h], fill=0)
    # shallow-shelf halo around coasts
    shelf = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))
    img = Image.new('RGB', (W, H), OCEAN)
    img.paste(Image.new('RGB', (W, H), OCEAN_SHELF), (0, 0), shelf.point(lambda v: int(v*.6)))
    edge = mask.filter(ImageFilter.MaxFilter(3))
    img.paste(Image.new('RGB', (W, H), COAST), (0, 0), edge)
    img.paste(Image.new('RGB', (W, H), LAND), (0, 0), mask)
    dest = Path(__file__).resolve().parents[1] / 'web_assets' / 'earth.jpg'
    img.save(dest, quality=88, optimize=True)
    print('wrote', dest, dest.stat().st_size, 'bytes,', len(polys), 'polygons')


if __name__ == '__main__':
    main(sys.argv[1])
