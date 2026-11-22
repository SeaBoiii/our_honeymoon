"""Render the three illustrated itinerary chapters in a fresh background Blender process.

blender -b --factory-startup --python-exit-code 1 -P map3d/blender/scripts/render_postcards.py
"""
from pathlib import Path
from math import cos, sin, pi, hypot
from random import Random

import bpy
from mathutils import Vector, noise

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / 'map3d/assets'
ART = ROOT / 'atlas'
W, D = 4.7, 2.85
TAU = 2*pi
PALETTE = {
    'lake': '#64babc', 'fiord': '#376e76', 'foam': '#c7e3dc',
    'grass': '#bfa775', 'meadow': '#ab9e67', 'beach': '#c9b895',
    'forest': '#405f4c', 'green': '#63806a', 'stone': '#757e83',
    'granite': '#98a5a4', 'snow': '#eef2ee', 'ice': '#b9e3e7',
    'earth': '#837968', 'strata': '#9c9077', 'reed': '#b69a57',
}


def material(name, hex_color):
    def linear(channel):
        v = int(channel, 16) / 255
        return v/12.92 if v < .04045 else ((v+.055)/1.055)**2.4
    color = tuple(linear(hex_color[i:i+2]) for i in (1, 3, 5)) + (1,)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = color
    shader.inputs['Roughness'].default_value = .84
    mat.diffuse_color = color
    return mat


def mesh(name, verts, faces, colors, mats):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    for mat in mats.values():
        data.materials.append(mat)
    lookup = {key: i for i, key in enumerate(mats)}
    for face, color in zip(data.polygons, colors):
        face.material_index = lookup[color]
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


PEAKS = {
    'tekapo': [(-3.2,1.45,1.35),(-1.85,2,1.89),(-1.2,2.35,1.45),(.25,2.05,1.34),(1.8,2,1.16),(3.2,1.65,.88)],
    'milford': [(-3.2,.95,1.85),(-2.05,1.25,3.04),(-1.6,1.55,2.25),(-.65,2.43,1.48),(1.1,2.1,1.53),(3.25,1.12,2.18),(4.0,.3,1.47)],
    'franz': [(-3.3,.9,1.4),(-2.3,1.5,2.18),(-1.25,2.05,2.55),(.3,2.15,1.8),(1.65,2.0,2.37),(3.1,1.05,2.06),(3.7,.0,1.03)],
}


def elevation(place, x, y):
    relief = noise.fractal(Vector((x*.93,y*1.22,3.6)),1.05,2.0,3)
    peaks = max(h - hypot((x-a)*.91,(y-b)*1.36)*(1.35 if place=='milford' else 1.18)
                for a,b,h in PEAKS[place])
    mountains = peaks + .25*relief + .095*sin(x*8+y*3)
    if place == 'tekapo':
        shore = -.99+.24*x+.29*cos(x*1.5)
        return max(mountains, min(.28, (shore-y)*1.8)+.035*relief)
    if place == 'milford':
        near = abs(x+.23*sin(y*1.9))-(2.3-.29*y)
        return max(mountains, near*.63-.18+.14*relief)
    return max(mountains, .20+.10*(y+1)+.09*relief+.035*cos(x*7))


def ground(place, mats):
    verts, faces, colors = [], [], []
    def point(radius, angle):
        x,y = W*radius*cos(angle), D*radius*sin(angle)
        z = elevation(place,x,y)
        return (x,y,max(.015,z))
    segments, rings = 168, 52
    verts.append(point(0,0))
    for ring in range(1,rings+1):
        for j in range(segments):
            verts.append(point(ring/rings,TAU*(j+(ring%2)*.36)/segments))
    def ix(r,j): return 1+(r-1)*segments+j%segments
    def surface(tri):
        x,y,z = [sum(verts[i][axis] for i in tri)/3 for axis in range(3)]
        if z < .019: color = 'fiord' if place=='milford' else 'lake'
        elif z < .13 and place=='tekapo': color='beach'
        elif z > (1.62 if place=='milford' else 1.05)+.16*sin(x*4+y*3)+.18*abs(cos(x*3-y)): color='snow'
        elif z > (.65 if place=='tekapo' else 1.1): color='granite' if z>1.25 else 'stone'
        elif place=='tekapo': color='grass' if sin(x*2.6+y*1.7)>.15 else 'meadow'
        elif place=='milford': color='green' if z>.7 else 'forest'
        else: color='stone' if y>-.9 or abs(x)<1.45 else 'forest'
        faces.append(tri); colors.append(color)
    for j in range(segments):
        surface((0,ix(1,j),ix(1,j+1)))
    for i in range(1,rings):
        for j in range(segments):
            a,b,c,d=ix(i,j),ix(i+1,j),ix(i+1,j+1),ix(i,j+1)
            surface((a,b,c)); surface((a,c,d))
    previous=[ix(rings,j) for j in range(segments)]
    for z,scale,color in [(-.14,1.,'strata'),(-.22,.994,'earth'),(-.29,.985,'strata'),(-.45,.96,'earth')]:
        current=[]
        for j,p in enumerate(previous):
            a=TAU*j/segments
            current.append(len(verts));verts.append((W*cos(a)*scale,D*sin(a)*scale,z+.016*sin(7*a)))
        for j,p in enumerate(previous):
            k=(j+1)%segments
            faces.append((p,current[j],current[k],previous[k]));colors.append(color)
        previous=current
    faces.append(tuple(reversed(previous)));colors.append('earth')
    mesh('Sculpted shoreline and ridges',verts,faces,colors,mats)


def model(name, length, xy, bottom, rotation):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ASSETS/(name+'.glb')))
    imported=set(bpy.data.objects)-before
    bpy.context.view_layer.update()
    def bounds():
        # Rotated mesh bounding boxes can extend well below the actual ice or hull.
        points=[o.matrix_world @ v.co for o in imported if o.type=='MESH' for v in o.data.vertices]
        return [Vector(fn(v[i] for v in points) for i in range(3)) for fn in (min,max)]
    lo,hi=bounds()
    scale=length/max(hi-lo)
    group=bpy.data.objects.new(name+' placement',None)
    bpy.context.scene.collection.objects.link(group)
    for o in imported:
        if not o.parent: o.parent=group
    group.scale=(scale,)*3
    group.rotation_euler.z=rotation
    bpy.context.view_layer.update()
    lo,hi=bounds()
    group.location=Vector((*xy,bottom))-Vector(((hi.x+lo.x)/2,(hi.y+lo.y)/2,lo.z))


def planting(place, rng, mats):
    verts, faces, colors=[],[],[]
    def triangle(a,b,c,color):
        start=len(verts);verts.extend((a,b,c));faces.append((start,start+1,start+2));colors.append(color)
    for i in range(2200):
        x,y=rng.uniform(-W,W),rng.uniform(-D,D)
        if (x/W)**2+(y/D)**2>.96: continue
        z=elevation(place,x,y)
        if z<.04:
            if i%9==0 and place!='franz':
                s=rng.uniform(.05,.18)
                triangle((x-s,y,.026),(x+s,y+.01,.026),(x+.018,y+.022,.026),'foam')
            continue
        if place=='tekapo':
            if z>.42 or y>-.38 or hypot(x-.83,y+1.66)<1.06: continue
            for j in range(7):
                ang=rng.random()*TAU; h=rng.uniform(.055,.14)
                triangle((x-.014,y,z-.012),(x+.017,y,z-.012),(x+cos(ang)*h*.55,y+sin(ang)*h*.55,z+h),'reed')
        elif z<1.08 and (place=='milford' or abs(x) > 2.4):
            size=rng.uniform(.055,.14)
            for offset in (-.32,.28):
                cx,cy=x+size*offset,y+size*offset
                top=z+size*rng.uniform(1.15,1.9)
                ring=[(cx+size*.74*cos(j*TAU/7),cy+size*.74*sin(j*TAU/7),top-size*.45) for j in range(7)]
                skirt=[(cx+size*cos(j*TAU/7),cy+size*sin(j*TAU/7),top-size*.98) for j in range(7)]
                for j in range(7):
                    k=(j+1)%7
                    triangle(ring[j],ring[k],(cx,cy,top),'green')
                    triangle(skirt[j],skirt[k],ring[k],'forest')
                    triangle(skirt[j],ring[k],ring[j],'green' if j%3 else 'forest')
                    triangle(skirt[k],skirt[j],(cx,cy,z-.035),'forest')
    mesh('Shore planting and reflections',verts,faces,colors,mats)


def render(place, scene):
    mats={k:material(k,v) for k,v in PALETTE.items()}
    rng=Random(197)
    ground(place,mats)
    planting(place,rng,mats)
    if place=='tekapo':
        model('church_stone',1.65,(.83,-1.66),.27,2.35)
    elif place=='milford':
        model('boat',1.12,(.26,-1.25),.004,-.82)
        falls=[]
        for i in range(50):
            y=.86-i*.032
            x=-1.6+.07*sin(y*5)
            for edge in (-.021,.021):
                falls.append((x+edge,y,max(.025,elevation(place,x+edge,y))+.025))
        faces=[(j,j+1,j+3,j+2) for j in range(0,len(falls)-2,2)]
        mesh('Fiord waterfall',falls,faces,['foam']*len(faces),mats)
    else:
        model('glacier_ice',3.7,(-.38,-.25),-.11,-.29)
        model('helicopter',1.0,(1.45,-.80),1.93,-.82)
    target=Vector((0,0,.77 if place=='tekapo' else .94))
    bpy.ops.object.camera_add(location=(1.25,-14.3,8.7))
    cam=bpy.context.object
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=9.85
    scene.camera=cam
    for pos,energy,size,color in [((-4,-5,8),1950,6,(1,.91,.79)),((4,1,6),840,5,(.79,.9,1))]:
        bpy.ops.object.light_add(type='AREA',location=pos)
        lamp=bpy.context.object;lamp.data.energy=energy;lamp.data.shape='DISK';lamp.data.size=size
        lamp.data.color=color;lamp.rotation_euler=(-lamp.location).to_track_quat('-Z','Y').to_euler()
    world=scene.world or bpy.data.worlds.new('South Island daylight')
    scene.world=world;world.use_nodes=True
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs['Color'].default_value=(.77,.86,.92,1);bg.inputs['Strength'].default_value=.54
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.render.film_transparent=True
    scene.render.resolution_x=900;scene.render.resolution_y=530;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='WEBP';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.quality=91
    scene.render.filepath=str(ART/(place+'-scene.webp'))
    bpy.ops.render.render(write_still=True)


# This script runs in its own factory-startup background process.
if __name__=='__main__':
    if not bpy.app.background:
        raise RuntimeError('Render the postcards with Blender in background mode.')
    for place in PEAKS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        render(place,bpy.context.scene)
