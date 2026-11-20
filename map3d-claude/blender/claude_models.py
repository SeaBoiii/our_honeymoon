"""Claude's vehicles and landmarks for the honeymoon map.

Run inside Blender. Each asset is built in its own CL_* collection from bmesh primitives,
then exported to map3d-claude/assets/<name>.glb.
Conventions: Z up, vehicles face +Y, origin at bottom centre (the web app re-fits sizes).
Wheels are children named Wheel_* (spin about local X); the helicopter has Rotor (spins
about local Z) and TailRotor (about local X).
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

OUT = 'C:/Users/seabo/Documents/GitHub/our_honeymoon/map3d-claude/assets'
os.makedirs(OUT, exist_ok=True)

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]

MATS = {}
def M(name, hexcol, rough=.7, metal=0.0, emit=0.0):
    key = 'CL_' + name
    if key in MATS: return MATS[key]
    m = bpy.data.materials.get(key) or bpy.data.materials.new(key); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = lin(hexcol) + [1]; b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = lin(hexcol) + [1]; b.inputs['Emission Strength'].default_value = emit
    MATS[key] = m; return m

PAL = dict(red=M('Red', '#B8322A', .45), cream=M('Cream', '#EFE6D2'), white=M('White', '#F4F5F2', .5), glass=M('Glass', '#1F3442', .15, .3),
           tyre=M('Tyre', '#22262A', .9), rim=M('Rim', '#B9BEC3', .35, .6), teal=M('Teal', '#1C8C93', .5), dark=M('Dark', '#2B3036'),
           wood=M('Wood', '#8A5A36', .8), cedar=M('Cedar', '#A0683F', .75), stone=M('Stone', '#A79C88', .95), slate=M('Slate', '#4A525A', .8),
           leaf=M('Leaf', '#4E7D3E', .9), leaf2=M('Leaf2', '#6E9A48', .9), pine=M('Pine', '#2F5A3B', .9), bark=M('Bark', '#5B4030', .9),
           water=M('Water', '#3FB8C4', .2), snow=M('Snow', '#F2F6F8', .8), ice=M('Ice', '#BDE8F0', .2), rock=M('Rock', '#6F767C', .95),
           glow=M('Glow', '#7FFFE0', .5, 0, 6.0), light=M('Lamp', '#FFE7A8', .4, 0, 3.0), gold=M('Gold', '#C9A24A', .35, .5),
           wool=M('Wool', '#EDEBE4', 1.0), mosque=M('MosqueWall', '#F1E9D8', .8), dome=M('Dome', '#2E8B7A', .4), coral=M('Coral', '#E2563F', .5))

COL = None
def begin(name):
    global COL
    cname = 'CL_' + name; col = bpy.data.collections.get(cname)
    if col is None:
        col = bpy.data.collections.new(cname); bpy.context.scene.collection.children.link(col)
    elif col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        if len(o.users_collection) == 1:
            d = o.data; bpy.data.objects.remove(o, do_unlink=True)
            if isinstance(d, bpy.types.Mesh) and d.users == 0: bpy.data.meshes.remove(d)
    lc = bpy.context.view_layer.layer_collection.children.get(cname)
    if lc: lc.exclude = False
    COL = col
    root = bpy.data.objects.new('CL' + name, None); col.objects.link(root)
    return root

_n = [0]
def part(root, kind, mat, loc=(0, 0, 0), size=(1, 1, 1), rot=(0, 0, 0), name=None, parent=None, **kw):
    """kind: box | cyl | cone | sphere | ico | hemi | prism (gable roof) | poly (extruded outline)"""
    bm = bmesh.new()
    if kind == 'box': bmesh.ops.create_cube(bm, size=1)
    elif kind in ('cyl', 'cone'):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=kw.get('seg', 12), radius1=.5, radius2=.5 if kind == 'cyl' else kw.get('top', 0.0), depth=1)
    elif kind == 'sphere': bmesh.ops.create_uvsphere(bm, u_segments=kw.get('seg', 12), v_segments=kw.get('rings', 8), radius=.5)
    elif kind == 'ico': bmesh.ops.create_icosphere(bm, subdivisions=kw.get('sub', 1), radius=.5)
    elif kind == 'hemi':
        bmesh.ops.create_uvsphere(bm, u_segments=kw.get('seg', 16), v_segments=kw.get('rings', 10), radius=.5)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context='VERTS')
        bmesh.ops.contextual_create(bm, geom=[e for e in bm.edges if e.is_boundary])
    elif kind == 'prism':  # gable roof: ridge along Y
        v = [bm.verts.new(p) for p in [(-.5, -.5, 0), (.5, -.5, 0), (0, -.5, .5), (-.5, .5, 0), (.5, .5, 0), (0, .5, .5)]]
        for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]: bm.faces.new([v[i] for i in f])
    elif kind == 'poly':  # outline (list of xy) extruded 0..1 in z
        pts = kw['pts']; lo = [bm.verts.new((x, y, 0)) for x, y in pts]; hi = [bm.verts.new((x, y, 1)) for x, y in pts]
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        for i in range(len(pts)): j = (i + 1) % len(pts); bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _n[0] += 1; nm = name or '%s_%s_%03d' % (root.name, kind, _n[0])
    me = bpy.data.meshes.new(nm + '_M'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    me.materials.append(mat)
    o = bpy.data.objects.new(nm, me); COL.objects.link(o); o.parent = parent or root
    o.location = loc; o.scale = size; o.rotation_euler = [math.radians(a) for a in rot]
    return o

def pivot(root, name, loc, parent=None):
    e = bpy.data.objects.new(name, None); COL.objects.link(e); e.parent = parent or root; e.location = loc; return e

def wheel(root, name, x, y, r=.42, w=.32):
    p = pivot(root, name, (x, y, r))
    part(root, 'cyl', PAL['tyre'], (0, 0, 0), (r * 2, r * 2, w), (0, 90, 0), parent=p, seg=14)
    part(root, 'cyl', PAL['rim'], (math.copysign(w * .52, x), 0, 0), (r * 1.1, r * 1.1, .04), (0, 90, 0), parent=p, seg=10)
    part(root, 'box', PAL['dark'], (math.copysign(w * .56, x), 0, 0), (.03, r * 1.15, .1), parent=p)  # spoke shows rotation
    return p

def export(root, fname):
    for o in bpy.context.selected_objects: o.select_set(False)
    stack = [root]; nodes = []
    while stack: o = stack.pop(); nodes.append(o); stack += list(o.children)
    for o in nodes: o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(filepath=OUT + '/' + fname + '.glb', export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_texcoords=False, export_animations=False, export_cameras=False, export_lights=False)
    for o in nodes: o.select_set(False)
    print('%-14s %6.1f KB' % (fname, os.path.getsize(OUT + '/' + fname + '.glb') / 1000))

# ================= vehicles =================
def car():
    r = begin('Car')
    part(r, 'box', PAL['red'], (0, 0, .78), (1.86, 4.3, .62))                           # lower body
    part(r, 'box', PAL['red'], (0, 1.55, 1.12), (1.8, 1.2, .2), (-8, 0, 0))             # bonnet slope
    part(r, 'box', PAL['glass'], (0, -.35, 1.42), (1.7, 2.55, .62))                     # glasshouse
    part(r, 'box', PAL['red'], (0, -.45, 1.75), (1.74, 2.45, .1))                       # roof
    for x in (-.86, .86): part(r, 'box', PAL['red'], (x, -.35, 1.42), (.05, .14, .64))  # B-pillars
    for x in (-.55, .55): part(r, 'box', PAL['dark'], (x, -.45, 1.84), (.06, 2.2, .06)) # roof rails
    for x in (-.3, .3): part(r, 'box', PAL['coral'], (x, -.5, 1.9), (.12, 2.0, .04))    # skis
    part(r, 'box', PAL['dark'], (0, 2.16, .62), (1.8, .1, .3))                          # bumper
    for x in (-.65, .65): part(r, 'box', PAL['light'], (x, 2.17, .9), (.36, .05, .14))  # headlights
    for x in (-.7, .7): part(r, 'box', M('Tail', '#FF3B30', .4, 0, 2), (x, -2.16, .95), (.3, .05, .14))
    for nm, x, y in (('Wheel_FL', -.9, 1.35), ('Wheel_FR', .9, 1.35), ('Wheel_RL', -.9, -1.35), ('Wheel_RR', .9, -1.35)): wheel(r, nm, x, y)
    export(r, 'car')

def coach():
    r = begin('Coach')
    part(r, 'box', PAL['white'], (0, 0, 1.85), (2.5, 12, 2.9))
    part(r, 'box', PAL['glass'], (0, -.4, 2.45), (2.53, 10.4, 1.0))
    part(r, 'box', PAL['glass'], (0, 6.0, 2.2), (2.3, .06, 1.6))                     # windscreen
    part(r, 'box', PAL['teal'], (0, 0, 1.15), (2.54, 12.02, .28))
    part(r, 'box', PAL['teal'], (0, 0, 3.32), (2.0, 9, .1))
    for x in (-.85, .85): part(r, 'box', PAL['light'], (x, 6.02, .8), (.4, .05, .18))
    for nm, x, y in (('Wheel_FL', -1.15, 3.9), ('Wheel_FR', 1.15, 3.9), ('Wheel_ML', -1.15, -2.6), ('Wheel_MR', 1.15, -2.6), ('Wheel_RL', -1.15, -3.8), ('Wheel_RR', 1.15, -3.8)):
        wheel(r, nm, x, y, .5, .36)
    export(r, 'coach')

def helicopter():
    r = begin('Helicopter')
    part(r, 'sphere', PAL['red'], (0, .3, 1.35), (1.5, 2.6, 1.45), seg=14, rings=9)
    part(r, 'sphere', PAL['glass'], (0, 1.15, 1.45), (1.25, 1.3, 1.0), seg=14, rings=9)
    part(r, 'cone', PAL['red'], (0, -2.4, 1.55), (.55, .55, 3.6), (90, 0, 0), top=.35, seg=10)
    part(r, 'box', PAL['red'], (0, -4.05, 2.05), (.08, .7, 1.0), (-15, 0, 0))
    part(r, 'box', PAL['red'], (0, -3.9, 1.6), (1.1, .4, .06))
    for x in (-.65, .65):
        part(r, 'cyl', PAL['dark'], (x, .2, .15), (.12, .12, 3.0), (90, 0, 0), seg=8)
        for y in (-.5, .9): part(r, 'box', PAL['dark'], (x * .85, y, .45), (.06, .06, .65), (0, x * 18, 0))
    part(r, 'cyl', PAL['dark'], (0, .2, 2.2), (.18, .18, .35), seg=8)                        # mast
    rot = pivot(r, 'Rotor', (0, .2, 2.4))
    part(r, 'cyl', PAL['dark'], (0, 0, 0), (.3, .3, .12), parent=rot, seg=8)
    for a in (0, 90): part(r, 'box', PAL['dark'], (0, 0, 0), (.22, 8.6, .04), (0, 0, a), parent=rot)
    tail = pivot(r, 'TailRotor', (.18, -4.15, 2.15))
    for a in (0, 90): part(r, 'box', PAL['dark'], (0, 0, 0), (.03, .16, 1.3), (a, 0, 0), parent=tail)
    export(r, 'helicopter')

def boat():
    r = begin('Boat')
    hull = [(-1.5, -4.2), (1.5, -4.2), (1.55, 1.6), (.9, 3.6), (0, 4.6), (-.9, 3.6), (-1.55, 1.6)]
    part(r, 'poly', PAL['dark'], (0, 0, 0), (1, 1, .9), pts=hull)
    part(r, 'poly', PAL['white'], (0, 0, .9), (1, 1, .32), pts=hull)
    part(r, 'box', PAL['white'], (0, -.9, 1.75), (2.5, 5.2, 1.05))
    part(r, 'box', PAL['glass'], (0, -.9, 1.85), (2.53, 4.9, .5))
    part(r, 'box', PAL['white'], (0, -1.5, 2.65), (2.0, 3.0, .75))
    part(r, 'box', PAL['glass'], (0, -1.5, 2.72), (2.03, 2.7, .38))
    part(r, 'box', PAL['teal'], (0, -.9, 2.3), (2.6, 5.4, .08))
    part(r, 'cyl', PAL['dark'], (0, -2.3, 3.4), (.1, .1, 1.0), seg=6)
    export(r, 'boat')

def plane():
    r = begin('Plane')
    part(r, 'cyl', PAL['white'], (0, 0, 1.6), (1.15, 1.15, 10.5), (90, 0, 0), seg=14)
    part(r, 'sphere', PAL['white'], (0, 5.25, 1.6), (1.15, 1.6, 1.15), seg=14)
    part(r, 'cone', PAL['white'], (0, -6.6, 1.85), (1.15, 1.15, 2.8), (90, 0, 0), top=.25, seg=14)
    part(r, 'box', PAL['glass'], (0, 5.6, 1.95), (.8, .5, .22), (-20, 0, 0))
    for s in (-1, 1):
        part(r, 'poly', PAL['white'], (0, 0, 1.15), (1, 1, .14), pts=[(0, 1.2), (s * 6.8, -2.0), (s * 6.8, -2.8), (0, -1.0)][::(1 if s > 0 else -1)])
        part(r, 'cyl', PAL['slate'], (s * 2.4, .9, .95), (.55, .55, 1.8), (90, 0, 0), seg=12)
        part(r, 'poly', PAL['white'], (0, -6.6, 2.05), (1, 1, .08), pts=[(0, .4), (s * 2.6, -1.2), (s * 2.6, -1.6), (0, -.8)][::(1 if s > 0 else -1)])
    part(r, 'prism', PAL['teal'], (0, -6.9, 2.3), (.12, 2.2, 3.0))   # tail fin
    part(r, 'box', PAL['teal'], (0, 0, 1.25), (1.17, 10.4, .12))  # belly stripe
    export(r, 'plane')

# ================= landmarks (≈1 unit) =================
def church():
    r = begin('Church')
    part(r, 'box', PAL['stone'], (0, 0, .25), (.5, .8, .5))
    part(r, 'prism', PAL['slate'], (0, 0, .5), (.58, .86, .38))
    part(r, 'box', PAL['stone'], (0, .48, .38), (.26, .26, .76))
    part(r, 'cone', PAL['slate'], (0, .48, .88), (.36, .36, .26), seg=4, top=0)
    part(r, 'box', PAL['glass'], (0, -.401, .3), (.2, .01, .26))   # the famous window toward the lake
    export(r, 'church_stone')

def observatory():
    r = begin('Observatory')
    part(r, 'cyl', PAL['cream'], (0, 0, .2), (.8, .8, .4), seg=20)
    part(r, 'hemi', PAL['white'], (0, 0, .4), (.82, .82, .82), seg=20)
    part(r, 'box', PAL['dark'], (0, .2, .62), (.12, .45, .44), (-30, 0, 0))
    part(r, 'cyl', PAL['slate'], (0, 0, .02), (1.0, 1.0, .04), seg=20)
    export(r, 'observatory')

def lone_tree():
    r = begin('LoneTree')
    part(r, 'cyl', PAL['water'], (0, 0, .02), (1.0, 1.0, .04), seg=20)
    part(r, 'cone', PAL['bark'], (0, 0, .3), (.08, .08, .6), top=.5, seg=6)
    part(r, 'cone', PAL['bark'], (.08, 0, .52), (.04, .04, .3), (0, 35, 0), top=.4, seg=5)
    for (x, y, z, s) in [(0, 0, .72, .42), (.15, .08, .62, .3), (-.14, -.05, .6, .3), (.05, -.16, .58, .26), (-.04, .16, .64, .28)]:
        part(r, 'ico', PAL['leaf2'], (x, y, z), (s, s, s * 1.3))
    export(r, 'lone_tree')

def hot_tub():
    r = begin('HotTub')
    part(r, 'box', PAL['wood'], (0, 0, .05), (1.0, .8, .1))
    part(r, 'cyl', PAL['cedar'], (0, 0, .24), (.56, .56, .3), seg=18)
    part(r, 'cyl', PAL['water'], (0, 0, .385), (.48, .48, .02), seg=18)
    for x in (-.48, .48): part(r, 'box', PAL['wood'], (x, -.38, .3), (.04, .04, .4))
    part(r, 'box', PAL['wood'], (0, -.38, .5), (1.0, .04, .04))
    part(r, 'ico', PAL['white'], (0, 0, .5), (.18, .18, .1))  # a wisp of steam
    export(r, 'hot_tub')

def mosque():
    r = begin('Mosque')
    part(r, 'box', PAL['mosque'], (0, 0, .2), (.7, .7, .4))
    part(r, 'cyl', PAL['mosque'], (0, 0, .43), (.42, .42, .06), seg=16)
    part(r, 'hemi', PAL['dome'], (0, 0, .46), (.4, .4, .44), seg=16)
    part(r, 'cone', PAL['gold'], (0, 0, .7), (.03, .03, .12), seg=6)
    part(r, 'cyl', PAL['mosque'], (.42, .42, .45), (.1, .1, .9), seg=8)
    part(r, 'cone', PAL['dome'], (.42, .42, .97), (.12, .12, .14), seg=8)
    for x in (-.18, 0, .18): part(r, 'box', PAL['dark'], (x, -.351, .18), (.08, .01, .16))
    export(r, 'mosque')

def city():
    r = begin('City')
    part(r, 'box', PAL['slate'], (0, 0, .02), (1.0, 1.0, .04))
    import random; rnd = random.Random(7)
    for i in range(4):
        for j in range(4):
            if (i, j) in ((1, 2), (2, 1)): continue
            h = rnd.uniform(.12, .55); x, y = -.36 + i * .24, -.36 + j * .24
            part(r, 'box', rnd.choice([PAL['cream'], PAL['stone'], PAL['white']]), (x, y, .04 + h / 2), (.16, .16, h))
            part(r, 'box', PAL['glass'], (x, y - .081, .04 + h * .55), (.12, .005, h * .6))
    part(r, 'cyl', PAL['leaf'], (.12, .12, .05), (.3, .3, .02), seg=10)   # a little park
    export(r, 'city')

def cave():
    r = begin('Cave')
    part(r, 'cyl', PAL['water'], (0, 0, .02), (1.0, .8, .04), seg=16)
    part(r, 'ico', PAL['rock'], (0, .15, .2), (1.0, .7, .65), sub=1)
    part(r, 'hemi', PAL['dark'], (0, -.31, .04), (.36, .36, .05), (90, 0, 0), seg=12)   # arched mouth in the rock face
    part(r, 'box', PAL['wood'], (0, -.5, .06), (.1, .26, .04))                           # little boat
    for (x, z) in [(-.12, .2), (.05, .26), (.14, .17), (-.02, .13), (.09, .3)]: part(r, 'ico', PAL['glow'], (x, -.34, z), (.025, .025, .025), sub=0)
    export(r, 'glowworm_cave')

def ski_lift():
    r = begin('SkiLift')
    part(r, 'box', PAL['snow'], (0, 0, .1), (.8, 1.05, .06), (-6, 0, 0))   # gently sloping snowfield
    for k, y in enumerate((-.4, 0, .4)):
        part(r, 'cyl', PAL['slate'], (0, y, .4 + k * .05), (.04, .04, .8), seg=6)
        part(r, 'box', PAL['slate'], (0, y, .8 + k * .05), (.3, .04, .04))
    for x in (-.13, .13):
        part(r, 'cyl', PAL['dark'], (x, 0, .84), (.012, .012, .9), (90 - 3.6, 0, 0), seg=4)
        for y in (-.25, .1): part(r, 'box', PAL['coral'], (x, y, .72), (.08, .06, .06))
    export(r, 'ski_lift')

def glacier():
    r = begin('Glacier')
    import random; rnd = random.Random(3)
    for k in range(9):
        y = -.4 + k * .1; w = .5 - abs(k - 4) * .03
        part(r, 'ico', rnd.choice([PAL['ice'], PAL['snow']]), (rnd.uniform(-.05, .05), y, .12 + k * .03), (w, .18, .22 + k * .02), sub=1)
    for y in (-.2, .05, .25): part(r, 'box', M('Crevasse', '#3C7F9A', .3), (0, y, .3 + y * .2), (.35, .015, .1))
    export(r, 'glacier_ice')

def pine():
    r = begin('Pine')
    part(r, 'cyl', PAL['bark'], (0, 0, .1), (.08, .08, .2), seg=6)
    for k, (z, s) in enumerate([(.3, .5), (.52, .4), (.72, .28)]): part(r, 'cone', PAL['pine'], (0, 0, z), (s, s, .34), seg=8)
    export(r, 'pine_tree')

def beech():
    r = begin('Beech')
    part(r, 'cyl', PAL['bark'], (0, 0, .15), (.09, .09, .3), seg=6)
    for (x, y, z, s) in [(0, 0, .5, .46), (.14, .05, .42, .32), (-.13, -.06, .44, .32), (.02, .13, .62, .28)]: part(r, 'ico', PAL['leaf'], (x, y, z), (s, s, s), sub=1)
    export(r, 'beech_tree')

def sheep():
    r = begin('Sheep')
    part(r, 'ico', PAL['wool'], (0, 0, .5), (.55, .8, .5), sub=1)
    part(r, 'sphere', PAL['dark'], (0, .45, .6), (.22, .28, .24), seg=8, rings=6)
    for x in (-.15, .15):
        for y in (-.22, .22): part(r, 'cyl', PAL['dark'], (x, y, .14), (.07, .07, .28), seg=5)
    export(r, 'sheep')

def pin():
    r = begin('Pin')
    part(r, 'cone', PAL['coral'], (0, 0, .3), (.42, .42, .6), (180, 0, 0), seg=16)
    part(r, 'sphere', PAL['coral'], (0, 0, .72), (.6, .6, .6), seg=16, rings=10)
    for x in (-.07, .07): part(r, 'sphere', PAL['white'], (x, -.28, .76), (.14, .1, .14), seg=8, rings=6)
    part(r, 'cone', PAL['white'], (0, -.28, .68), (.2, .1, .14), (180, 0, 0), seg=8)
    export(r, 'pin')

for f in (car, coach, helicopter, boat, plane, church, observatory, lone_tree, hot_tub, mosque, city, cave, ski_lift, glacier, pine, beech, sheep, pin):
    f()
print('done')
