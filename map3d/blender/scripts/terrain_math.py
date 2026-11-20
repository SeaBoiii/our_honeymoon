"""Offline DEM and road corridor maths. NumPy only; safe outside Blender.

XY units are 10 km; input elevations and returned heights are real metres.
Kept independent of bpy/__file__ so build_terrain can exec this in the console.
"""
import json
import numpy as np

HEIGHT_EXAGGERATION = 5.0
HEIGHT_SCALE = HEIGHT_EXAGGERATION / 10000.0
ROAD_SPACING = .03                 # 300 m maximum CDT point spacing
ROAD_INNER = .04                   # full lowering inside 400 m
ROAD_OUTER = .12                   # smooth falloff ends at 1.2 km
LAKE_BED_DEPTH_M = 8.0
SAMPLE_LOCATIONS = (
    ('Aoraki', 170.142, -43.595),
    ('Christchurch', 172.60, -43.531),
    ('Lindis Pass summit', 169.66, -44.586),
    ('Haast Pass', 169.356, -44.105),
    ("Arthur's Pass village", 171.56, -42.94),
)


def projected_points(lon, lat):
    lon, lat = np.broadcast_arrays(lon, lat)
    return np.stack(((lon-170.5)*8.008, (lat+44.0)*11.132), axis=-1)


def inside(x, y, ring):
    """Vectorised even/odd test; rings may be lists or NumPy arrays."""
    x,y=np.broadcast_arrays(x,y)
    order=np.argsort(y,axis=None)
    sy=y.ravel()[order];sx=x.ravel()[order]
    ring=np.asarray(ring,dtype=float);mask=np.zeros(sy.size,dtype=bool)
    for (ax,ay),(bx,by) in zip(ring,np.roll(ring,-1,axis=0)):
        if ay==by:continue
        lo,hi=np.searchsorted(sy,sorted((ay,by)))
        mask[lo:hi]^=sx[lo:hi]<ax+(sy[lo:hi]-ay)*(bx-ax)/(by-ay)
    result=np.empty_like(mask);result[order]=mask
    return result.reshape(y.shape)


def edge_distance(x, y, ring):
    ring = np.asarray(ring, dtype=float)
    d2 = np.full(np.broadcast_shapes(np.shape(x), np.shape(y)), np.inf)
    for (ax, ay), (bx, by) in zip(ring, np.roll(ring, -1, axis=0)):
        dx, dy = bx-ax, by-ay
        if dx*dx+dy*dy < 1e-20:
            continue
        t = np.clip(((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy), 0, 1)
        d2 = np.minimum(d2, (x-ax-t*dx)**2+(y-ay-t*dy)**2)
    return np.sqrt(d2)


class DEMGrid:
    def __init__(self, data):
        self.lat0, self.lon0 = float(data['lat0']), float(data['lon0'])
        self.dlat, self.dlon = float(data['dlat']), float(data['dlon'])
        self.nlat, self.nlon = int(data['nlat']), int(data['nlon'])
        if min(self.nlat, self.nlon) < 2 or min(self.dlat, self.dlon) <= 0:
            raise ValueError('DEM must be an increasing south-to-north lon/lat grid')
        raw = np.asarray(data['elev'], dtype=float)
        if raw.ndim != 1 or raw.size != self.nlat*self.nlon:
            raise ValueError('DEM elev must have nlat*nlon row-major samples')
        self.valid = np.isfinite(raw).reshape(self.nlat, self.nlon)
        self.values = np.maximum(np.where(self.valid, raw.reshape(self.valid.shape), 0), 0)
        self.source = data.get('source', 'LINZ DEM')

    @classmethod
    def load(cls, path):
        return cls(json.loads(path.read_text(encoding='utf-8')))

    def sample_lonlat(self, lon, lat):
        """Bilinear interpolation; null corners and out-of-coverage points are 0.

        Do not renormalise around null corners: they represent unsampled/sea.
        Clipping indices is only for safe indexing, not extending edge heights.
        """
        lon, lat = np.broadcast_arrays(np.asarray(lon, float), np.asarray(lat, float))
        u, v = (lon-self.lon0)/self.dlon, (lat-self.lat0)/self.dlat
        valid = np.isfinite(u) & np.isfinite(v) & (u >= -1e-10) & (v >= -1e-10)
        valid &= (u <= self.nlon-1+1e-10) & (v <= self.nlat-1+1e-10)
        u = np.clip(np.where(np.isfinite(u), u, 0), 0, self.nlon-1)
        v = np.clip(np.where(np.isfinite(v), v, 0), 0, self.nlat-1)
        j = np.minimum(np.floor(u).astype(int), self.nlon-2)
        i = np.minimum(np.floor(v).astype(int), self.nlat-2)
        tx, ty = u-j, v-i
        a = self.values
        h = ((a[i, j]*(1-tx)+a[i, j+1]*tx)*(1-ty)
             + (a[i+1, j]*(1-tx)+a[i+1, j+1]*tx)*ty)
        return np.where(valid, np.maximum(h, 0), 0)

    def sample(self, x, y):
        return self.sample_lonlat(np.asarray(x)/8.008+170.5, np.asarray(y)/11.132-44.0)

    def lake_stats(self, ring):
        """Native, non-null DEM nodes inside a projected lake outline."""
        lon = self.lon0+np.arange(self.nlon)*self.dlon
        lat = self.lat0+np.arange(self.nlat)*self.dlat
        llon, llat = np.meshgrid(lon, lat)
        xy = projected_points(llon, llat)
        selected = inside(xy[..., 0], xy[..., 1], ring) & self.valid
        values = self.values[selected]
        return (float(np.median(values)) if values.size else None, int(values.size))


class RoadCorridors:
    """Exact nearest-segment projection in a bounded uniform spatial index.

    Segment AABBs expanded by ROAD_OUTER index every cell they can affect.
    Queries compare NumPy chunks only against segments in the same cell.
    Full polylines drive carving; a separate densified set supplies CDT points.
    """
    def __init__(self, routes, dem, cell_size=.5):
        self.cell_size = cell_size
        starts, ends, heights_a, heights_b, controls = [], [], [], [], []
        self.supplied_points = self.fallback_points = 0
        for key, route in routes.items():
            ll = np.asarray(route['points'], dtype=float)
            if ll.size == 0:
                continue
            if ll.ndim != 2 or ll.shape[1] != 2 or not np.isfinite(ll).all():
                raise ValueError('Invalid [lat, lon] road points: '+key)
            xy = projected_points(ll[:, 1], ll[:, 0])
            fallback = dem.sample(xy[:, 0], xy[:, 1])
            supplied = route.get('elev')
            if supplied is not None and len(supplied) == len(ll):
                h = np.asarray(supplied, dtype=float)
                use = np.isfinite(h)
                self.supplied_points += int(use.sum())
                self.fallback_points += int((~use).sum())
                h = np.maximum(np.where(use, h, fallback), 0)
            else:
                h = fallback
                self.fallback_points += len(ll)
            if len(xy) < 2:
                continue
            delta = xy[1:]-xy[:-1]
            lengths = np.linalg.norm(delta, axis=1)
            keep = lengths > 1e-10
            starts.extend(xy[:-1][keep]); ends.extend(xy[1:][keep])
            heights_a.extend(h[:-1][keep]); heights_b.extend(h[1:][keep])
            # Retain original corners and subdivide long spans, never shortcut
            # a hairpin by joining uniform samples across the corner.
            for a, b, length in zip(xy[:-1][keep], xy[1:][keep], lengths[keep]):
                count = max(1, int(np.ceil(length/ROAD_SPACING)))
                controls.extend(a+(b-a)*np.arange(count)[:, None]/count)
            controls.append(xy[-1])
        self.a = np.asarray(starts, dtype=float).reshape(-1, 2)
        self.delta = np.asarray(ends, dtype=float).reshape(-1, 2)-self.a
        self.length2 = np.sum(self.delta**2, axis=1)
        self.ha = np.asarray(heights_a, dtype=float)
        self.dh = np.asarray(heights_b, dtype=float)-self.ha
        # Exact repeats (including reverse journeys) need only one CDT vertex.
        self.points = (np.unique(np.round(controls, 7), axis=0) if controls
                       else np.empty((0, 2)))
        self.buckets = {}
        for index, (a, delta) in enumerate(zip(self.a, self.delta)):
            lo = np.floor((np.minimum(a, a+delta)-ROAD_OUTER)/cell_size).astype(int)
            hi = np.floor((np.maximum(a, a+delta)+ROAD_OUTER)/cell_size).astype(int)
            for ix in range(lo[0], hi[0]+1):
                for iy in range(lo[1], hi[1]+1):
                    self.buckets.setdefault((ix, iy), []).append(index)
        self.buckets = {k: np.asarray(v, dtype=int) for k, v in self.buckets.items()}

    def nearest(self, xy):
        """Distance and interpolated metres, or (inf, 0) outside all corridors."""
        xy = np.asarray(xy, dtype=float).reshape(-1, 2)
        distances = np.full(len(xy), np.inf)
        heights = np.zeros(len(xy))
        if not len(xy) or not len(self.a):
            return distances, heights
        cells = np.floor(xy/self.cell_size).astype(np.int64)
        _, inverse = np.unique(cells, axis=0, return_inverse=True)
        order = np.argsort(inverse, kind='stable')
        groups = np.split(order, np.flatnonzero(np.diff(inverse[order]))+1)
        for group in groups:
            indices = self.buckets.get(tuple(cells[group[0]]))
            if indices is None:
                continue
            a, delta = self.a[indices], self.delta[indices]
            # Bound working matrices even if routes accumulate in one cell.
            chunk_size = max(1, min(1024, 131072//len(indices)))
            for start in range(0, len(group), chunk_size):
                rows = group[start:start+chunk_size]
                offset = xy[rows, None, :]-a[None, :, :]
                t = np.clip(np.sum(offset*delta, axis=2)/self.length2[indices], 0, 1)
                d2 = np.sum((offset-t[..., None]*delta)**2, axis=2)
                nearest = np.argmin(d2, axis=1)
                row_index = np.arange(len(rows))
                distance = np.sqrt(d2[row_index, nearest])
                active = distance <= ROAD_OUTER
                rows = rows[active]
                distances[rows] = distance[active]
                chosen = nearest[active]
                heights[rows] = self.ha[indices[chosen]]+self.dh[indices[chosen]]*t[row_index[active], chosen]
        return distances, heights

    def carve(self, xy, metres):
        metres = np.maximum(np.asarray(metres, dtype=float), 0)
        distance, road = self.nearest(xy)
        t = np.clip((distance-ROAD_INNER)/(ROAD_OUTER-ROAD_INNER), 0, 1)
        weight = 1-t*t*(3-2*t)
        lowered = metres-weight*np.maximum(metres-road, 0)
        return np.maximum(lowered, 0), metres-lowered


def carve_lake_beds(xy, metres, lakes):
    """Lower only, including exact constrained shore vertices; keep water separate."""
    h = np.asarray(metres, dtype=float).copy()
    x, y = xy[:, 0], xy[:, 1]
    for lake in lakes:
        ring = lake['xy']
        lo, hi = np.min(ring, axis=0)-1e-6, np.max(ring, axis=0)+1e-6
        ix = np.where((x >= lo[0]) & (x <= hi[0]) & (y >= lo[1]) & (y <= hi[1]))[0]
        submerged = inside(x[ix], y[ix], ring) | (edge_distance(x[ix], y[ix], ring) < 2e-6)
        for island in lake.get('holes',[]):
            submerged &= ~inside(x[ix],y[ix],island)
        ix = ix[submerged]
        h[ix] = np.minimum(h[ix], max(0, lake['elevation_m']-LAKE_BED_DEPTH_M))
    return h


def print_lake_stats(dem, lakes):
    for lake in lakes:
        median, count = dem.lake_stats(lake['xy'])
        comparison = ('%.1f m, delta %+.1f m' % (median, median-lake['elevation_m'])
                      if median is not None else 'unavailable')
        print('[lake] %s: surface %.1f m / Z %.5f; DEM median %s (%d native nodes)' %
              (lake['name'], lake['elevation_m'], lake['elevation_m']*HEIGHT_SCALE, comparison, count))


def print_height_samples(metres, original, lakes):
    for (name, _, _), h, base in zip(SAMPLE_LOCATIONS, metres, original):
        print('[terrain] %s: Z=%.5f (%.1f m); DEM %.1f m' % (name, h*HEIGHT_SCALE, h, base))
    tekapo = next(lake for lake in lakes if lake['name'] == 'Tekapo')
    h = tekapo['elevation_m']
    print('[terrain] Lake Tekapo surface: Z=%.5f (%.1f m)' % (h*HEIGHT_SCALE, h))
