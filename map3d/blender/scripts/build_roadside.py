"""Build the shared roadside miniatures in an isolated Blender scene."""
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


def build(output):
    previous = bpy.context.window.scene
    scene = bpy.data.scenes.new("South Island roadsides")
    bpy.context.window.scene = scene
    mat = bpy.data.materials.new("Painted landscape")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    color = mat.node_tree.nodes.new('ShaderNodeVertexColor')
    color.layer_name = 'Pigment'
    mat.node_tree.links.new(color.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .92
    rng = random.Random(47)
    meshes = []

    def add(verts, faces, colors, smooth=False):
        start = len(vertices)
        vertices.extend(verts)
        polygons.extend(tuple(start + i for i in face) for face in faces)
        pigments.extend(colors)
        shading.extend([smooth] * len(faces))

    def tint(hexcolor, factor=1):
        c = [int(hexcolor[i:i+2], 16)/255 for i in (0, 2, 4)]
        return tuple(min(1, ((v+.055)/1.055)**2.4 * factor) for v in c) + (1,)

    def solid(verts, faces, color, smooth=False):
        add(verts, faces, [tint(color, rng.uniform(.93, 1.07)) for v in verts], smooth)

    def branch(a, b, ra, rb, color):
        a, b = Vector(a), Vector(b)
        axis = (b-a).normalized()
        u = axis.cross(Vector((0,1,0))).normalized()
        v = axis.cross(u)
        ring = [u*math.cos(i*math.tau/7)+v*math.sin(i*math.tau/7) for i in range(7)]
        solid([p+d*r for p,r in ((a,ra),(b,rb)) for d in ring],
              [(i,(i+1)%7,(i+1)%7+7,i+7) for i in range(7)], color, True)

    def crown(center, radii, color, lod, stone=False):
        n, rings = (6,3) if lod else (10,5)
        x,y,z = center
        verts = [(x,y,z-radii[2])]
        cols = [tint(color,.63)]
        for j in range(1,rings):
            lat = math.pi*j/rings-math.pi/2
            for i in range(n):
                angle = math.tau*(i+.36*(j%2))/n
                radius = rng.uniform(.82,1.13)*math.cos(lat)
                verts.append((x+math.cos(angle)*radius*radii[0],y+math.sin(angle)*radius*radii[1],
                              z+(math.sin(lat)+rng.uniform(-.08,.08))*radii[2]))
                cols.append(tint(color,rng.uniform(.78,1.13)*(.9+.18*math.sin(lat))))
        verts.append((x,y,z+radii[2])); cols.append(tint(color,1.12))
        faces = [(0,1+(i+1)%n,1+i) for i in range(n)]
        for j in range(rings-2):
            for i in range(n):
                a,b=1+j*n+i,1+j*n+(i+1)%n
                faces.append((a,b,b+n,a+n))
        faces.extend((1+(rings-2)*n+i,1+(rings-2)*n+(i+1)%n,len(verts)-1) for i in range(n))
        add(verts,faces,cols,not stone)

    def box(c, ext, color):
        verts=[tuple(c[i]+v[i]*ext[i]/2 for i in range(3)) for v in
               [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        solid(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],color)

    def make(name,lod):
        if name in ('Beech','Poplar'):
            pop = name=='Poplar'
            trunk = '797367' if pop else '615746'
            if lod:
                branch((0,0,0),(0,0,.66),.032,.014,trunk)
                if pop:
                    crown((0,0,.56),(.13,.12,.47),'8c9854',True)
                else:
                    for a,h in ((0,.58),(2.16,.64),(4.33,.70)):
                        crown((.13*math.cos(a),.13*math.sin(a),h),(.21,.20,.24),'527558',True)
                    crown((0,0,.79),(.195,.18,.18),'688463',True)
                return
            branch((0,0,0),(.014,0,.87 if pop else .70),.023 if pop else .045,.012,trunk)
            count = (7 if lod else 17) if pop else (6 if lod else 14)
            for j in range(count):
                a=j*2.39996
                h=(.27 if pop else .40)+j/count*(.65 if pop else .46)
                spread=(.068 if pop else .26)*(1-.55*j/count)
                x,y=math.cos(a)*spread, math.sin(a)*spread
                branch((.008,0,h-.18),(x,y,h),.014,.006,trunk)
                radius=(.085 if pop else .17)*rng.uniform(.88,1.12)
                palette=('84934d','a5a158','7b904f') if pop else ('45694f','577655','63805a','385e4c')
                crown((x,y,h),(radius,radius*(.84 if pop else 1),radius*(1.95 if pop else .79)),palette[j%len(palette)],lod)
            crown((0,0,.86),(.08,.075,.14) if pop else (.15,.16,.125),'9c9d57' if pop else '648260',lod)
        elif name=='Tussock':
            for j in range(14 if lod else 58):
                a=j*2.39996; reach=rng.uniform(.23,.65); height=rng.uniform(.42,.88)
                w=rng.uniform(.025,.054); dx,dy=math.cos(a),math.sin(a)
                verts=[]
                for d,h,s in ((.08,0,.7),(.20,.63,1),(.60,1,.6),(1,.79,.02)):
                    for side in (-1,1):
                        verts.append((dx*d*reach-side*dy*w*s,dy*d*reach+side*dx*w*s,h*height))
                solid(verts,[(0,1,3,2),(2,3,5,4),(4,5,7,6)],rng.choice(('c8aa60','ab934f','bda16b','d5c089','8c874b')))
        elif name=='Schist':
            for j in range(3 if lod else 7):
                x,y=rng.uniform(-.35,.35),rng.uniform(-.34,.34);s=rng.uniform(.20,.49)
                crown((x,y,s*.29),(s,s*.66,s*.49),rng.choice(('92918a','777d78','aaa594')),lod,True)
        else:
            shed=name=='Woolshed'; width,depth=(1,.64) if shed else (.85,.58)
            roof={'Villa':'906f61','VillaZinc':'a0a59f','VillaSlate':'526565','Woolshed':'746c62'}[name]
            box((0,0,.17),(width,depth,.34),'b2a99a' if shed else 'e6debd')
            hw,hd=width*.56,depth*.56
            solid([(-hw,-hd,.32),(hw,-hd,.32),(hw,hd,.32),(-hw,hd,.32),(-hw,0,.54),(hw,0,.54)],
                  [(0,1,5,4),(4,5,2,3),(0,4,3),(1,2,5)],roof)
            if not lod:
                if shed:
                    box((-.17,-depth/2,.14),(.40,.015,.27),'545b53')
                    for j in range(18):
                        box((-.48+j*.055,-depth/2-.008,.19),(.008,.012,.29),'9c978c')
                else:
                    for x in (-.28,.24):
                        box((x,-.30,.19),(.17,.018,.16),'f2e6cb')
                        box((x,-.312,.19),(.135,.015,.125),'556b70')
                    box((0,-.305,.13),(.12,.02,.26),'6b7b73')
                    box((.26,.08,.52),(.07,.085,.19),'9a685a')

    try:
        for name in ('Beech','Poplar','Tussock','Schist','Villa','VillaZinc','VillaSlate','Woolshed'):
            for lod in (0,1):
                vertices,polygons,pigments,shading=[],[],[],[]
                make(name,lod)
                label=name+('Far' if lod else 'Near')
                mesh=bpy.data.meshes.new(label);mesh.from_pydata(vertices,[],polygons);mesh.update()
                attr=mesh.color_attributes.new(name='Pigment',type='BYTE_COLOR',domain='POINT')
                for i,c in enumerate(pigments):attr.data[i].color=c
                for i,s in enumerate(shading):mesh.polygons[i].use_smooth=s
                mesh.materials.append(mat);obj=bpy.data.objects.new(label,mesh);scene.collection.objects.link(obj)
                meshes.append(mesh)
        output=Path(output);output.parent.mkdir(exist_ok=True,parents=True)
        bpy.ops.export_scene.gltf(filepath=str(output),use_active_scene=True,export_yup=True,export_materials='EXPORT')
        print(f'Exported {len(meshes)} roadside meshes to {output.name}')
    finally:
        bpy.context.window.scene=previous
        for obj in list(scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.scenes.remove(scene)
        for mesh in meshes:bpy.data.meshes.remove(mesh)
        bpy.data.materials.remove(mat)


if __name__ == '__main__':
    build(Path(__file__).resolve().parents[3]/'atlas'/'roadside.glb')
