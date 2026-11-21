"""Validate exports, write measured metadata, render two looks, save the blend.

Preview scenes contain linked-data duplicates. User scenes, objects, cameras,
worlds, render settings and selection are left alone. Set RENDER_PREVIEWS=False
only for a quick diagnostic run; the default produces the spec's two PNGs.
"""
from pathlib import Path
PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon'))
exec(compile((PROJECT_ROOT / 'map3d/blender/scripts/common.py').read_text(encoding='utf-8'), 'common.py', 'exec'), globals())


def validate_glb(path, terrain=False):
    """Inspect the actual glTF JSON chunk as well as the Blender scene."""
    import struct
    blob=path.read_bytes()
    if blob[:4]!=b'glTF' or len(blob)<20:
        raise RuntimeError('Invalid or missing GLB: '+str(path))
    version,length=struct.unpack_from('<II',blob,4)
    count,kind=struct.unpack_from('<I4s',blob,12)
    if version!=2 or length!=len(blob) or kind!=b'JSON':
        raise RuntimeError('Invalid GLB header: '+str(path))
    doc=json.loads(blob[20:20+count].decode('utf-8'))
    if doc.get('images') or doc.get('textures'):
        raise RuntimeError('Image textures violate the self-contained palette contract: '+path.name)
    if doc.get('extensionsRequired'):
        # The loader has no Draco or Meshopt decoder configured.
        unsupported=set(doc['extensionsRequired'])-{'KHR_materials_emissive_strength'}
        if unsupported:
            raise RuntimeError('Unexpected required glTF extension: '+str(unsupported))
    if terrain:
        nodes=doc.get('nodes',[])
        names={n.get('name') for n in nodes}
        if not {'Terrain','Lakes','NorthIslandHint','StewartIsland'}<=names:
            raise RuntimeError('Terrain GLB lost required node names: '+str(names))
        for mesh in doc.get('meshes',[]):
            for primitive in mesh['primitives']:
                if 'NORMAL' in primitive['attributes']:
                    raise RuntimeError('Terrain normals unexpectedly exported; flat shading/size strategy requires omitted normals')
    else:
        if path.stem=='helicopter':
            nodes=doc.get('nodes',[])
            indices={n.get('name'):i for i,n in enumerate(nodes)}
            if not {'Helicopter','Rotor','TailRotor'}<=indices.keys():
                raise RuntimeError('Helicopter GLB lost rotor node names')
            children=nodes[indices['Helicopter']].get('children',[])
            if any(indices[n] not in children for n in ('Rotor','TailRotor')):
                raise RuntimeError('Export must preserve direct Rotor/TailRotor children')
    limit=export_budget(path.stem)
    if len(blob)>=limit:
        raise RuntimeError('Export size budget exceeded: '+path.name)


def preview_scene(kind):
    """Reuse only explicitly owned preview scenes/collections, never user ones."""
    name='HM_Preview_'+kind
    collection=reset_collection(name)
    # reset_collection links to the active scene for export visibility. Preview
    # collections instead live solely in their dedicated scene.
    for scene in bpy.data.scenes:
        if collection.name in scene.collection.children:
            scene.collection.children.unlink(collection)
    scene=bpy.data.scenes.get(name)
    if scene and not scene.get('honeymoon_preview'):
        raise RuntimeError('Refusing to reuse a user scene named '+name)
    if scene is None:
        scene=bpy.data.scenes.new(name)
    scene['honeymoon_preview']=True
    scene.collection.children.link(collection)
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=24
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1600
    scene.render.resolution_y=1200 if kind=='Terrain' else 1400
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard'
    world=bpy.data.worlds.get(name+'_World') or bpy.data.worlds.new(name+'_World')
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.60,.74,.79,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
    scene.world=world
    return scene,collection


def copy_hierarchy(original,col,prefix):
    clones={}
    for obj in descendants(original):
        clone=obj.copy()
        clone.name=prefix+obj.name
        col.objects.link(clone)
        clones[obj]=clone
        clone.hide_viewport=False
        clone.hide_render=False
    for obj,clone in clones.items():
        clone.parent=clones.get(obj.parent)
        clone.matrix_basis=obj.matrix_basis.copy()
    return clones[original]


def studio_camera(scene,col,target,position,ortho):
    camera_data=bpy.data.cameras.new(scene.name+'_CameraData')
    camera=new_object(scene.name+'_Camera',camera_data,col)
    camera.location=position
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.type='ORTHO'; camera_data.ortho_scale=ortho
    camera_data.clip_start=.01; camera_data.clip_end=1000
    scene.camera=camera
    light_data=bpy.data.lights.new(scene.name+'_SunData','SUN')
    light=new_object(scene.name+'_Sun',light_data,col)
    light.rotation_euler=(math.radians(28),math.radians(-24),math.radians(-30))
    light_data.energy=2.0
    light_data.angle=.12


def text_label(text,col,loc):
    data=bpy.data.curves.new('HM_LabelData','FONT')
    data.body=text; data.size=.135; data.align_x='CENTER'
    data.extrude=0
    obj=new_object('HM_Label_'+text,data,col)
    obj.location=loc
    data.materials.append(material('road'))
    return obj


def render_previews():
    directory=BLENDER_DIR/'previews'; directory.mkdir(parents=True,exist_ok=True)
    scene,col=preview_scene('Terrain')
    terrain=bpy.data.objects['Terrain']
    copy_hierarchy(terrain,col,'HM_TerrainLook_')
    _,lo,hi=asset_stats(terrain)
    cx,cy=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
    span=max(hi[0]-lo[0],hi[1]-lo[1])
    box('HM_TerrainLook_Sea',(cx,cy,-.08),(span*1.6,span*1.6,.12),'fiord',col,None)
    studio_camera(scene,col,(cx,cy,0),(cx-34,cy-58,94),span*1.16)
    scene.render.filepath=str(directory/'terrain.png')
    bpy.ops.render.render(write_still=True,scene=scene.name)
    print('[preview] Wrote terrain.png')
    scene,col=preview_scene('Lineup')
    entries=ASSET_DEFINITIONS[1:]
    for i,(_,name,_) in enumerate(entries):
        obj=bpy.data.objects[name]
        _,lo,hi=asset_stats(obj)
        size=max(hi[j]-lo[j] for j in range(3))
        clone=copy_hierarchy(obj,col,'HM_LineupLook_')
        clone.scale=obj.scale/size
        x=(i%5-2)*1.70
        y=(len(entries)//5/2-i//5)*1.90
        clone.location=(x,y,.06)
        # Local XY ground text is readable in an elevated camera.
        text_label(name,col,(x,y-.73,.065))
    box('HM_LineupLook_Ground',(0,0,-.015),(9.2,9.0,.08),'cream',col,None)
    studio_camera(scene,col,(0,0,.2),(-4,-9,14),12.0)
    scene.render.filepath=str(directory/'props_lineup.png')
    bpy.ops.render.render(write_still=True,scene=scene.name)
    print('[preview] Wrote props_lineup.png (%d miniatures)' % len(entries))


def write_manifest():
    entries=[]
    for filename,name,notes in ASSET_DEFINITIONS:
        obj=bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError('Missing asset %s; run its build script first' % name)
        path=ASSET_DIR/(filename+'.glb')
        if not path.is_file():
            raise RuntimeError('Missing export: '+str(path))
        validate_glb(path,name=='Terrain')
        triangles,lo,hi=asset_stats(obj)
        entries.append({'file':path.name,'root':name,'triangles':triangles,
                        'bbox_min':[round(x,6) for x in lo],
                        'bbox_max':[round(x,6) for x in hi],'notes':notes})
    manifest=ASSET_DIR/'manifest.json'
    manifest.write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
    if globals().get('RENDER_PREVIEWS',True):
        render_previews()
    if not globals().get('SAVE_BLEND',True):
        return
    object_mode()
    # Keep a previous .blend outside these directories from being backed up
    # implicitly by Blender. Existing user scenes remain part of this snapshot.
    old_versions=bpy.context.preferences.filepaths.save_version
    try:
        bpy.context.preferences.filepaths.save_version=0
        result=bpy.ops.wm.save_as_mainfile(filepath=str(BLENDER_DIR/'honeymoon_map.blend'))
        if 'FINISHED' not in result:
            raise RuntimeError('Blender failed to save honeymoon_map.blend')
    finally:
        bpy.context.preferences.filepaths.save_version=old_versions
    print('[manifest] Wrote %d measured assets and honeymoon_map.blend' % len(entries))


write_manifest()
