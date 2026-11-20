"""Shared Blender 5.x helpers. Execute with a caller-supplied PROJECT_ROOT."""
from pathlib import Path
import json
import math
import re
import bpy
from mathutils import Vector, Matrix

PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon')).resolve()
ASSET_DIR = PROJECT_ROOT / 'map3d/assets'
BLENDER_DIR = PROJECT_ROOT / 'map3d/blender'
ASSET_DIR.mkdir(parents=True, exist_ok=True)
PALETTE = {
    'snow': '#F4F7F8', 'rock': '#7D8A8F', 'tussock': '#C9A35A',
    'pasture': '#7FA65A', 'beech': '#3F6B3A', 'water': '#3FB8C4',
    'fiord': '#1E5D73', 'road': '#3A3F44', 'red': '#C8432F',
    'glass': '#254B60', 'cedar': '#95633F', 'stone': '#A99D88',
    'ice': '#B4E7EE', 'cream': '#E2D7B7', 'glow': '#55E7CE',
}


def project(lon, lat):
    return ((lon - 170.5) * 8.008, (lat + 44.0) * 11.132)


def elevation_z(metres):
    return metres * 5.0 / 10000.0


def rgba(key):
    value = PALETTE.get(key, key).lstrip('#')
    rgb = [int(value[i:i+2], 16) / 255 for i in (0, 2, 4)]
    # Blender's shader sockets and color attributes use scene-linear values.
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055)**2.4 for v in rgb) + (1.0,)


def material(key, vertex_color=False, emission=0.0):
    name = 'HM_' + key + ('_Vertex' if vertex_color else '')
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = rgba(key)
    bsdf.inputs['Roughness'].default_value = .87
    mat.diffuse_color = rgba(key)
    if vertex_color:
        attr = mat.node_tree.nodes.new('ShaderNodeVertexColor')
        attr.layer_name = 'Color'
        attr.label = 'Color Attribute: Color'
        mat.node_tree.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])
    if emission:
        bsdf.inputs['Emission Color'].default_value = rgba(key)
        bsdf.inputs['Emission Strength'].default_value = emission
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def object_mode():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def reset_collection(name):
    """Only delete objects owned exclusively by this dedicated collection.

    Objects linked into any other collection are unlinked here and preserved.
    Never recurse into child collections, which may belong to the user.
    """
    object_mode()
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    elif col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for obj in list(col.objects):
        if len(obj.users_collection) > 1:
            col.objects.unlink(obj)
        else:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0 and isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
    return col


def new_object(name, data, col, parent=None):
    # Blender silently suffixes collisions. Refuse rather than break loader names.
    if bpy.data.objects.get(name):
        raise RuntimeError('Required asset name already exists outside its collection: ' + name)
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    if parent:
        obj.parent = parent
    return obj


def root(name, col):
    obj = new_object(name, None, col)
    obj.empty_display_type = 'PLAIN_AXES'
    return obj


def mesh_object(name, vertices, faces, col, parent=None, mat=None):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = new_object(name, mesh, col, parent)
    if mat:
        mesh.materials.append(material(mat) if isinstance(mat, str) else mat)
    for p in mesh.polygons:
        p.use_smooth = False
    return obj


def box(name, loc, size, mat, col, parent):
    x, y, z = (s / 2 for s in size)
    vertices = [(-x,-y,-z), (x,-y,-z), (x,y,-z), (-x,y,-z),
                (-x,-y,z), (x,-y,z), (x,y,z), (-x,y,z)]
    faces = [(3,2,1,0), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7), (4,5,6,7)]
    obj = mesh_object(name, vertices, faces, col, parent, mat)
    obj.location = loc
    return obj


def frustum(name, loc, r1, r2, depth, mat, col, parent, n=12, axis=(0,0,1)):
    verts = [(r*math.cos(i*math.tau/n), r*math.sin(i*math.tau/n), z)
             for r,z in ((r1,-depth/2),(r2,depth/2)) for i in range(n)]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj = mesh_object(name, verts, faces, col, parent, mat)
    obj.location = loc
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0,0,1)).rotation_difference(Vector(axis).normalized())
    return obj


def ellipsoid(name, loc, scale, mat, col, parent, n=12, rings=6, dome=False):
    # Latitude rings plus single pole vertices, avoiding degenerate pole faces.
    low = 0 if dome else -math.pi/2
    verts = []
    for j in range(rings):
        a = low + (math.pi/2-low) * (j+1)/(rings+1)
        verts += [(scale[0]*math.cos(a)*math.cos(i*math.tau/n),
                   scale[1]*math.cos(a)*math.sin(i*math.tau/n), scale[2]*math.sin(a)) for i in range(n)]
    faces = []
    if dome:
        verts = [(scale[0]*math.cos(i*math.tau/n),scale[1]*math.sin(i*math.tau/n),0) for i in range(n)] + verts
        rings += 1
        faces.append(tuple(reversed(range(n))))
    else:
        bottom = len(verts)
        verts.append((0,0,-scale[2]))
        faces += [(bottom,(i+1)%n,i) for i in range(n)]
    for j in range(rings-1):
        faces += [(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for i in range(n)]
    top = len(verts)
    verts.append((0,0,scale[2]))
    faces += [((rings-1)*n+i,(rings-1)*n+(i+1)%n,top) for i in range(n)]
    obj = mesh_object(name, verts, faces, col, parent, mat)
    obj.location = loc
    return obj


def beam(name, a, b, radius, mat, col, parent, n=8):
    a, b = Vector(a), Vector(b)
    return frustum(name, (a+b)/2, radius, radius, (b-a).length, mat, col, parent, n, b-a)


def descendants(obj):
    return [obj] + [child for c in obj.children for child in descendants(c)]


def asset_stats(obj):
    bpy.context.view_layer.update()
    vertices, triangles = [], 0
    for child in descendants(obj):
        if child.type != 'MESH':
            continue
        child.data.calc_loop_triangles()
        triangles += len(child.data.loop_triangles)
        vertices.extend(child.matrix_world @ Vector(v) for v in child.bound_box)
    if not vertices:
        raise RuntimeError('Asset contains no meshes: ' + obj.name)
    return triangles, [min(v[i] for v in vertices) for i in range(3)], [max(v[i] for v in vertices) for i in range(3)]


def normalize_asset(obj, largest=1.0, length=None):
    """Bake scale/translation into geometry, retaining rotor pivot transforms."""
    _, lo, hi = asset_stats(obj)
    scale = length / (hi[1]-lo[1]) if length else largest / max(hi[i]-lo[i] for i in range(3))
    offset = Vector((-(lo[0]+hi[0])/2, -(lo[1]+hi[1])/2, -lo[2]))
    # All primitives have unit object scale. Scale mesh coordinates and every
    # local translation once, preserving the rotors' local spin axes.
    for child in descendants(obj)[1:]:
        if child.type == 'MESH':
            child.data.transform(Matrix.Scale(scale,4))
        child.location *= scale
        if child.parent == obj:
            child.location += offset*scale
    bpy.context.view_layer.update()


def export_glb(root_obj, path):
    object_mode()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    selection = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    nodes = descendants(root_obj)
    visibility = [(o, o.hide_get(), o.hide_viewport) for o in nodes]
    try:
        for obj in selection:
            obj.select_set(False)
        for obj, _, _ in visibility:
            obj.hide_viewport = False
            obj.hide_set(False)
            obj.select_set(True)
        bpy.context.view_layer.objects.active = root_obj
        kwargs = dict(filepath=str(path), export_format='GLB', use_selection=True,
                      export_apply=True, export_yup=True, export_vertex_color='ACTIVE',
                      export_texcoords=False, export_animations=False, export_cameras=False,
                      export_lights=False)
        if root_obj.name == 'Terrain':
            # Shared POINT colours + no normal/UV streams keep 120k+ triangles
            # below 6 MB. glTF missing NORMAL specifies flat normals; three's
            # GLTFLoader uses derivative flatShading for this case. No Draco.
            kwargs['export_normals'] = False
        optional = set(kwargs) - {'filepath','export_format','use_selection'}
        while True:
            try:
                result = bpy.ops.export_scene.gltf(**kwargs)
                if 'FINISHED' not in result:
                    raise RuntimeError('glTF exporter did not finish: ' + str(result))
                break
            except (TypeError, ValueError) as exc:
                # Retry only the explicitly rejected optional property.
                message = str(exc)
                rejected = next((k for k in optional if k in message), None)
                if not rejected:
                    raise RuntimeError('glTF export failed for %s: %s' % (root_obj.name, message)) from exc
                print('[export] Retrying without unsupported %s: %s' % (rejected, message))
                kwargs.pop(rejected)
                optional.remove(rejected)
        limit = 6_000_000 if root_obj.name == 'Terrain' else 300_000
        size = path.stat().st_size
        if size >= limit:
            raise RuntimeError('%s is %s bytes; budget is strictly under %s bytes' % (path.name,size,limit))
        print('[export] %s: %s triangles, %.1f KB' % (path.name,asset_stats(root_obj)[0],size/1000))
    finally:
        for obj in nodes:
            obj.select_set(False)
        for obj, hidden, viewport in visibility:
            obj.hide_viewport = viewport
            obj.hide_set(hidden)
        for obj in selection:
            if obj.name in bpy.context.view_layer.objects:
                obj.select_set(True)
        bpy.context.view_layer.objects.active = active


ASSET_DEFINITIONS = [
    ('terrain_south_island','Terrain','LINZ DEM elevation at 5x; lowered real-road corridors; hand-digitised rings; separate water surfaces.'),
    ('car','Car','Compact SUV, ski rack; +Y forward.'),
    ('coach','Coach','Generic white touring coach; +Y forward.'),
    ('helicopter','Helicopter','Rotor local Z; TailRotor local X; +Y forward.'),
    ('boat','Boat','Two-deck fiord cruise boat; +Y forward.'),
    ('plane','Plane','Generic twin-jet wide-body; +Y forward.'),
    ('church_stone','StoneChurch','Stone lakeside chapel and bell tower.'),
    ('observatory','Observatory','Telescope dome and slit.'),
    ('lone_tree','LoneTree','Willow in shallow water.'),
    ('hot_tub','HotTub','Cedar tub for two on a cliff deck.'),
    ('mosque','Mosque','Generic dome and one minaret.'),
    ('city','City','Twelve buildings and street.'),
    ('glowworm_cave','Cave','Cave arch, small boat, emissive glow points.'),
    ('ski_lift','SkiLift','Three towers, cable and hanging chairs.'),
    ('glacier_ice','GlacierIce','Faceted ice tongue and open crevasses.'),
    ('pine_tree','PineTree','Conifer.'),('beech_tree','BeechTree','Rounded native tree.'),
    ('sheep','Sheep','Wool body, dark head and four legs.'),
    ('pin','Pin','Accent-red map pin with an actual heart-shaped aperture.'),
]


class Kit:
    """Unique names, flat data-API primitives, and one asset-owned collection."""
    def __init__(self, root_name, collection):
        self.col = collection
        self.obj = root(root_name, collection)
        self.counter = 0

    def name(self, label):
        self.counter += 1
        return '%s_%s_%03d' % (self.obj.name,label,self.counter)

    def cube(self, loc, size, mat, label='Block', parent=None):
        return box(self.name(label),loc,size,mat,self.col,parent or self.obj)

    def cone(self, loc, r1, r2, depth, mat, n=12, axis=(0,0,1), parent=None, label='Cylinder'):
        return frustum(self.name(label),loc,r1,r2,depth,mat,self.col,parent or self.obj,n,axis)

    def ball(self, loc, scale, mat, n=12, rings=5, dome=False, label='Facets', parent=None):
        return ellipsoid(self.name(label),loc,scale,mat,self.col,parent or self.obj,n,rings,dome)

    def bar(self, a,b,r,mat,n=8,label='Beam',parent=None):
        return beam(self.name(label),a,b,r,mat,self.col,parent or self.obj,n)

    def mesh(self, vertices,faces,mat,label='Shape',parent=None):
        return mesh_object(self.name(label),vertices,faces,self.col,parent or self.obj,mat)

    def roof(self, center, width, length, height, mat='road'):
        x,y,z=center; w=width/2; l=length/2
        return self.mesh([(x-w,y-l,z),(x+w,y-l,z),(x+w,y+l,z),(x-w,y+l,z),
                          (x,y-l,z+height),(x,y+l,z+height)],
                         [(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4),(3,2,1,0)],mat,'GableRoof')

    def finish(self, filename, vehicle=False):
        normalize_asset(self.obj,length=4.5 if vehicle else None)
        _,lo,hi=asset_stats(self.obj)
        if abs(lo[2])>1e-5 or abs(lo[0]+hi[0])>1e-5 or abs(lo[1]+hi[1])>1e-5:
            raise RuntimeError('Bottom-centre origin validation failed: '+self.obj.name)
        export_glb(self.obj,ASSET_DIR/(filename+'.glb'))
        return self.obj
