"""Render transparent atlas plates from the same models the browser loads."""
from pathlib import Path
import bpy
from mathutils import Vector

PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon'))
out = PROJECT_ROOT / 'map3d/preview/plates'
out.mkdir(parents=True, exist_ok=True)


def render_plate(name, slug, width, height, angle):
    scene = bpy.data.scenes.new('Atlas plate '+slug)
    created = []
    try:
        scene.collection.children.link(bpy.data.collections['HM_'+name])
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 24
        scene.cycles.use_denoising = True
        scene.render.film_transparent = True
        scene.render.resolution_x,scene.render.resolution_y = width,height
        scene.render.resolution_percentage = 100
        scene.world = bpy.data.worlds.new('Atlas softbox')
        scene.world.use_nodes = True
        bg = next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
        bg.inputs['Color'].default_value = (.76,.88,1,1)
        bg.inputs['Strength'].default_value = .38
        def add(data):
            obj = bpy.data.objects.new('Plate '+data.name,data)
            scene.collection.objects.link(obj)
            created.append(obj)
            return obj
        cam = add(bpy.data.cameras.new('Atlas lens'))
        cam.data.type = 'ORTHO'
        scene.camera = cam
        cam.rotation_euler = (-Vector(angle)).to_track_quat('-Z','Y').to_euler()
        basis = cam.rotation_euler.to_matrix()
        bpy.context.view_layer.update()
        points = [basis.transposed() @ (o.matrix_world @ v.co)
                  for o in scene.objects if o.type=='MESH' for v in o.data.vertices]
        lo=Vector([min(v[i] for v in points) for i in range(3)])
        hi=Vector([max(v[i] for v in points) for i in range(3)])
        center=basis @ ((lo+hi)/2)
        span = max(hi.x-lo.x,(hi.y-lo.y)*width/height)
        cam.data.ortho_scale = span*1.075
        cam.location = center + Vector(angle).normalized()*4*span
        for pos,power,size,tint in [((-2.5,-3,4),450,1.6,(1,.91,.78)),((2,2,3),150,2.2,(.78,.89,1))]:
            light=add(bpy.data.lights.new('Atlas soft light','AREA'))
            light.data.energy=power*span*span
            light.data.color=tint; light.data.shape='DISK'; light.data.size=size*span
            light.location=center+Vector(pos)*span
            light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
        scene.render.image_settings.file_format='PNG'
        scene.render.image_settings.color_mode='RGBA'
        scene.render.filepath=str(out/(slug+'.png'))
        bpy.ops.render.render(write_still=True, scene=scene.name)
    finally:
        world=scene.world
        bpy.data.scenes.remove(scene)
        for obj in created:
            data=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if data.users==0:
                (bpy.data.cameras if isinstance(data,bpy.types.Camera) else bpy.data.lights).remove(data)
        if world and world.users==0:
            bpy.data.worlds.remove(world)


plates=[('HookerValley','valley',1320,900,(2.5,-7.5,4.1)),
        ('StoneChurch','chapel',520,400,(-3.7,4,2.0)),
        ('Boat','cruise',520,400,(3.7,4.4,2.5)),
        ('Helicopter','helicopter',520,400,(4.5,3,2))]
for plate in plates:
    render_plate(*plate)
