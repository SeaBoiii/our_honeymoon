"""Claude's terrain for the honeymoon map ("topographic diorama" style).

Run inside Blender (via the Blender MCP or the Text Editor). Builds into its own collection
CL_Terrain and exports map3d-claude/assets/terrain.glb.

Data: corrected Natural Earth coast (+road buffer), LINZ 8 m DEM grid, OSRM road polylines
with DEM elevations, real lake levels. Same projection as the rest of the project:
X = (lon-170.5)*8.008, Y = (lat+44)*11.132, Z = elev_m/10000*5  (1 unit = 10 km, 5x vertical).
"""
import bpy, json, math, time
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

ROOT = 'C:/Users/seabo/Documents/GitHub/our_honeymoon'
DATA = ROOT + '/map3d/blender/data'
OUT = ROOT + '/map3d-claude/assets'
EX = 5 / 10000
STEP = 0.14

def P(lon, lat): return ((lon - 170.5) * 8.008, (lat + 44.0) * 11.132)

def srgb_lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]

# ---------- helpers ----------
def collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
    elif col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        if len(o.users_collection) == 1:
            d = o.data; bpy.data.objects.remove(o, do_unlink=True)
            if d is not None and getattr(d, 'users', 1) == 0 and isinstance(d, bpy.types.Mesh): bpy.data.meshes.remove(d)
        else: col.objects.unlink(o)
    lc = bpy.context.view_layer.layer_collection.children.get(name)
    if lc: lc.exclude = False
    return col

def vc_material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    a = nt.nodes.new('ShaderNodeVertexColor'); a.layer_name = 'Color'
    b.inputs['Roughness'].default_value = .92
    nt.links.new(a.outputs['Color'], b.inputs['Base Color']); nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m

def flat_material(name, hexcol, rough=.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes.get('Principled BSDF') or next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = srgb_lin(hexcol) + [1]; b.inputs['Roughness'].default_value = rough
    return m

def inside_mask(x, y, ring):
    ring = np.asarray(ring); ax, ay = ring[:, 0], ring[:, 1]; bx, by = np.roll(ax, -1), np.roll(ay, -1)
    m = np.zeros(x.shape, bool)
    for s in range(0, len(ax), 64):  # chunk edges to bound memory
        A, B, C, D = ax[s:s+64, None], ay[s:s+64, None], bx[s:s+64, None], by[s:s+64, None]
        hit = ((B > y[None]) != (D > y[None])) & (x[None] < A + (y[None] - B) * (C - A) / np.where(D - B == 0, 1e-12, D - B))
        m ^= np.logical_xor.reduce(hit, axis=0)
    return m

def cdt(points, rings):
    pts = [Vector((float(a), float(b))) for a, b in points]; edges = []; off = 0
    faces = []
    for k, r in enumerate(rings):
        n = len(r); edges += [(off + i, off + (i + 1) % n) for i in range(n)]
        if k == 0: faces = [list(range(off, off + n))]
        off += n
    res = delaunay_2d_cdt(pts, edges, faces, 1, 1e-7)
    return np.array([(v.x, v.y) for v in res[0]]), [f for f in res[2] if len(f) == 3]

# ---------- data ----------
coast = json.load(open(DATA + '/coastline.json', encoding='utf-8'))
dem = json.load(open(DATA + '/dem_grid.json', encoding='utf-8'))
routes = json.load(open(ROOT + '/map3d/web_assets/routes.json', encoding='utf-8'))['routes']
G = np.array([np.nan if v is None else v for v in dem['elev']], float).reshape(dem['nlat'], dem['nlon'])
G = np.nan_to_num(G, nan=0.0)

def dem_at(lon, lat):
    fi = (lat - dem['lat0']) / dem['dlat']; fj = (lon - dem['lon0']) / dem['dlon']
    i = np.clip(np.floor(fi).astype(int), 0, dem['nlat'] - 2); j = np.clip(np.floor(fj).astype(int), 0, dem['nlon'] - 2)
    ti, tj = np.clip(fi - i, 0, 1), np.clip(fj - j, 0, 1)
    return (G[i, j] * (1 - ti) * (1 - tj) + G[i + 1, j] * ti * (1 - tj) + G[i, j + 1] * (1 - ti) * tj + G[i + 1, j + 1] * ti * tj)

def to_ll(x, y): return x / 8.008 + 170.5, y / 11.132 - 44.0

# road samples (~300 m) with real elevations
road_xy, road_e = [], []
for r in routes.values():
    pts, el = r['points'], r.get('elev') or [None] * len(r['points'])
    for (la1, lo1), (la2, lo2), e1, e2 in zip(pts, pts[1:], el, el[1:]):
        a, b = np.array(P(lo1, la1)), np.array(P(lo2, la2)); n = max(1, int(np.linalg.norm(b - a) / .03))
        for k in range(n):
            t = k / n; road_xy.append(a + (b - a) * t)
            road_e.append((e1 if e1 is not None else 0) * (1 - t) + (e2 if e2 is not None else 0) * t)
road_xy = np.array(road_xy); road_e = np.array(road_e)

# divide line (for wet-west vs dry-east colouring)
DIV = np.array([P(lo, la) for lo, la in [(172.72,-41.05),(172.25,-41.85),(171.85,-42.45),(171.55,-42.95),(170.72,-43.30),(170.142,-43.595),(169.63,-43.98),(169.05,-44.30),(168.53,-44.70),(168.05,-45.15),(167.55,-45.65),(167.15,-46.0)]])
def west(x, y):
    o = np.argsort(DIV[:, 1]); return x < np.interp(y, DIV[o, 1], DIV[o, 0])

def colours(x, y, h_m, slope):
    W = west(x, y); c = np.zeros((len(x), 3))
    pal = {k: np.array(srgb_lin(v)) for k, v in dict(low='#86A95F', mid='#A9B96A', tus='#D2B878', forest='#3E6A3C', forest2='#557552',
                                                        brown='#A08F76', rock='#8C9398', snow='#F3F6F8', bush='#6F8D4F').items()}
    c[:] = pal['low']
    c[(h_m >= 150)] = pal['mid']
    c[(h_m >= 400) & ~W] = pal['tus']; c[(h_m >= 150) & W] = pal['forest']
    c[(h_m >= 800) & ~W] = pal['brown']; c[(h_m >= 800) & W] = pal['forest2']
    c[(h_m >= 1150) | ((slope > .9) & (h_m > 600))] = pal['rock']
    c[(h_m >= 1450) & (slope < 1.4)] = pal['snow']; c[h_m >= 2100] = pal['snow']
    return c

def build_island(name, ring_ll, step, lakes, col, flat_m=None):
    ring = np.array([P(lo, la) for lo, la in ring_ll])
    x0, y0 = ring.min(0); x1, y1 = ring.max(0)
    gx, gy = np.meshgrid(np.arange(x0 + step * .5, x1, step), np.arange(y0 + step * .5, y1, step))
    gx, gy = gx.ravel(), gy.ravel(); m = inside_mask(gx, gy, ring); gx, gy = gx[m], gy[m]
    lake_rings = [np.array([P(lo, la) for lo, la in L['ring']]) for L in lakes]
    extra = []
    if flat_m is None and len(road_xy):
        rm = inside_mask(road_xy[:, 0], road_xy[:, 1], ring); extra = road_xy[rm]
    pts = np.vstack([ring] + lake_rings + [np.column_stack([gx, gy])] + ([extra] if len(extra) else []))
    xy, faces = cdt(pts, [ring] + lake_rings)
    F = np.array(faces); cen = xy[F].mean(1); keep = inside_mask(cen[:, 0], cen[:, 1], ring); F = F[keep]
    lon, lat = to_ll(xy[:, 0], xy[:, 1])
    if flat_m is not None:
        h = np.full(len(xy), float(flat_m))
    else:
        h = np.maximum(dem_at(lon, lat), 0.0)
        # road corridors: only ever lower terrain toward the real road grade
        if len(road_xy):
            cell = .15; key = lambda a: (np.floor(a[:, 0] / cell).astype(int), np.floor(a[:, 1] / cell).astype(int))
            rk = key(road_xy); buckets = {}
            for idx, (i, j) in enumerate(zip(*rk)): buckets.setdefault((i, j), []).append(idx)
            vk = key(xy)
            for v, (i, j) in enumerate(zip(*vk)):
                cand = []
                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1): cand += buckets.get((i + di, j + dj), [])
                if not cand: continue
                c = np.array(cand); d = np.hypot(road_xy[c, 0] - xy[v, 0], road_xy[c, 1] - xy[v, 1]); k = d.argmin()
                if d[k] < .12:
                    w = 1.0 if d[k] < .04 else 1 - (d[k] - .04) / .08; w = w * w * (3 - 2 * w)
                    h[v] = min(h[v], h[v] * (1 - w) + road_e[c[k]] * w)
        for L, lr in zip(lakes, lake_rings):  # carve lake beds just under the surface
            mm = inside_mask(xy[:, 0], xy[:, 1], lr); h[mm] = np.minimum(h[mm], L['elevation_m'] - 25)
    z = np.maximum(h * EX, .012)
    # slope per vertex (real-world rise/run, from adjacent faces)
    xyz = np.column_stack([xy, z]); nrm = np.cross(xyz[F[:, 1]] - xyz[F[:, 0]], xyz[F[:, 2]] - xyz[F[:, 0]])
    fs = np.hypot(nrm[:, 0], nrm[:, 1]) / np.maximum(np.abs(nrm[:, 2]), 1e-9) / (EX * 10000 / 10000 * 1)  # remove exaggeration
    fs = fs / 5.0
    slope = np.zeros(len(xy))
    for k in range(3): np.maximum.at(slope, F[:, k], fs)
    me = bpy.data.meshes.new(name + '_Mesh'); me.from_pydata(xyz.tolist(), [], F.tolist()); me.update()
    for p in me.polygons: p.use_smooth = False
    col_attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    rgb = colours(xy[:, 0], xy[:, 1], h, slope); rgba = np.column_stack([rgb, np.ones(len(rgb))]).astype(np.float32)
    col_attr.data.foreach_set('color', rgba.ravel())
    me.color_attributes.active_color = col_attr
    me.materials.append(vc_material('CL_TerrainColour'))
    ob = bpy.data.objects.new(name, me); col.objects.link(ob)
    return ob, len(F)

def build_lake(L, col, parent):
    lr = np.array([P(lo, la) for lo, la in L['ring']])
    x0, y0 = lr.min(0); x1, y1 = lr.max(0)
    gx, gy = np.meshgrid(np.arange(x0 + .05, x1, .1), np.arange(y0 + .05, y1, .1)); gx, gy = gx.ravel(), gy.ravel()
    m = inside_mask(gx, gy, lr)
    xy, faces = cdt(np.vstack([lr, np.column_stack([gx[m], gy[m]])]), [lr])
    F = np.array(faces); cen = xy[F].mean(1); F = F[inside_mask(cen[:, 0], cen[:, 1], lr)]
    z = L['elevation_m'] * EX
    me = bpy.data.meshes.new('Lake_' + L['name'] + '_Mesh'); me.from_pydata([(a, b, z) for a, b in xy], [], F.tolist()); me.update()
    me.materials.append(flat_material('CL_LakeWater', '#3FB8C4', .25))
    ob = bpy.data.objects.new('Lake_' + L['name'].replace(' ', ''), me); col.objects.link(ob); ob.parent = parent
    return len(F)

def export(root, path, normals=True):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.selected_objects: o.select_set(False)
    stack = [root]; nodes = []
    while stack: o = stack.pop(); nodes.append(o); stack += list(o.children)
    for o in nodes: o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = root
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_vertex_color='ACTIVE', export_texcoords=False, export_animations=False, export_cameras=False, export_lights=False)
    if not normals: kw['export_normals'] = False
    r = bpy.ops.export_scene.gltf(**kw)
    for o in nodes: o.select_set(False)
    return r

# ---------- build ----------
t0 = time.time()
col = collection('CL_Terrain')
lakes = coast['lakes']
land = {l['name']: l['ring'] for l in coast['land']}
terrain, ntri = build_island('Terrain', land['SouthIsland'], STEP, lakes, col)
stew, n2 = build_island('StewartIsland', land['StewartIsland'], .22, [], col); stew.parent = terrain
north, n3 = build_island('NorthIslandHint', land['NorthIslandHint'], .5, [], col, flat_m=80); north.parent = terrain
lroot = bpy.data.objects.new('Lakes', None); col.objects.link(lroot); lroot.parent = terrain
nl = sum(build_lake(L, col, lroot) for L in lakes)
import os; os.makedirs(OUT, exist_ok=True)
export(terrain, OUT + '/terrain.glb', normals=False)
print('terrain tris %d (+stewart %d, north %d, lakes %d) in %.1fs; glb %.0f KB' % (ntri, n2, n3, nl, time.time() - t0, os.path.getsize(OUT + '/terrain.glb') / 1000))
for nm, lo, la in [('Aoraki', 170.142, -43.595), ('Lindis', 169.66, -44.586), ('Haast', 169.356, -44.105), ("Arthur's", 171.56, -42.94)]:
    print(nm, 'DEM %.0f m' % float(dem_at(np.array([lo]), np.array([la]))[0]))
