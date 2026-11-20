"""Offline LINZ DEM terrain with road corridors; execute in Blender's console."""
from pathlib import Path
PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon'))
exec(compile((PROJECT_ROOT / 'map3d/blender/scripts/common.py').read_text(encoding='utf-8'), 'common.py', 'exec'), globals())
exec(compile((PROJECT_ROOT / 'map3d/blender/scripts/terrain_math.py').read_text(encoding='utf-8'), 'terrain_math.py', 'exec'), globals())
import numpy as np
from mathutils.geometry import delaunay_2d_cdt


def signed_area(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1])) / 2


def clean_ring(coords):
    result = []
    for lon,lat in coords:
        p = project(lon,lat)
        if not result or math.dist(result[-1],p) > 1e-7:
            result.append(p)
    if math.dist(result[0],result[-1]) < 1e-7:
        result.pop()
    if len(result) < 3:
        raise RuntimeError('Coast/lake ring has fewer than three unique points')
    return result if signed_area(result) > 0 else list(reversed(result))


DIVIDE_LL = [(172.72,-41.05),(172.25,-41.85),(171.85,-42.45),
             (171.55,-42.95),(170.72,-43.30),(170.142,-43.595),
             (169.63,-43.98),(169.05,-44.30),(168.53,-44.70),
             (168.05,-45.15),(167.55,-45.65),(167.15,-46.00)]
DIVIDE_XY = [project(*p) for p in DIVIDE_LL]


def divide_x_at_y(y):
    pts = sorted(DIVIDE_XY,key=lambda p:p[1])
    return np.interp(y,[p[1] for p in pts],[p[0] for p in pts])


def height_metres(x, y, dem):
    return dem.sample(x, y)


def constrained_grid(ring, step, lake_rings=(), landmarks=()):
    points = list(ring)
    edges = [(i,(i+1)%len(ring)) for i in range(len(ring))]
    for lr in lake_rings:
        offset = len(points)
        points.extend(lr)
        edges.extend((offset+i,offset+(i+1)%len(lr)) for i in range(len(lr)))
    x0,y0 = np.min(ring,axis=0)
    x1,y1 = np.max(ring,axis=0)
    xx,yy = np.meshgrid(np.arange(x0+step*.47,x1,step),np.arange(y0+step*.41,y1,step))
    x,y=xx.ravel(),yy.ravel()
    mask=inside(x,y,ring)
    points.extend(zip(x[mask].tolist(),y[mask].tolist()))
    points.extend(landmarks)
    # Output type 1 is the interior of input face(s), including lake beds.
    # Only the outer coast is a face: lake loops constrain edges, not holes.
    try:
        result=delaunay_2d_cdt([Vector(p) for p in points],edges,[list(range(len(ring)))],1,1e-7,False)
    except TypeError:
        result=delaunay_2d_cdt([Vector(p) for p in points],edges,[list(range(len(ring)))],1,1e-7)
    vertices,_,faces=result[:3]
    xy=np.array([(v.x,v.y) for v in vertices],dtype=float)
    # Defensive centroid clipping as well; enforce upwards winding.
    triangles=[]
    for face in faces:
        if len(face) != 3:
            raise RuntimeError('CDT returned non-triangle; expected interior triangulation')
        a,b,c=face
        pa,pb,pc=xy[a],xy[b],xy[c]
        cross=(pb[0]-pa[0])*(pc[1]-pa[1])-(pb[1]-pa[1])*(pc[0]-pa[0])
        if abs(cross)>1e-12:
            triangles.append((a,b,c) if cross>0 else (a,c,b))
    centers=xy[np.array(triangles)].mean(axis=1)
    keep=inside(centers[:,0],centers[:,1],ring)
    return xy,[face for face,k in zip(triangles,keep) if k]


def terrain_colors(obj, xy, z, west):
    mesh=obj.data
    xyz=np.column_stack((xy,z))
    tri=np.array([tuple(p.vertices) for p in mesh.polygons],dtype=int)
    normal=np.cross(xyz[tri[:,1]]-xyz[tri[:,0]],xyz[tri[:,2]]-xyz[tri[:,0]])
    steep=np.hypot(normal[:,0],normal[:,1])/np.maximum(np.abs(normal[:,2]),1e-9)
    # Vertical exaggeration removed when deriving real-world slope.
    slope=np.zeros(len(xy))
    for i in range(3):
        np.maximum.at(slope,tri[:,i],steep/HEIGHT_EXAGGERATION)
    h=z/HEIGHT_SCALE
    colors=np.tile(rgba('pasture'),(len(xy),1))
    colors[(~west)&(h>400)]=rgba('tussock')
    colors[west&(h<900)]=rgba('beech')
    colors[(h>=900)&(slope>.7)]=rgba('rock')
    colors[(h>=1300)&(slope<1.3)]=rgba('snow')
    colors[(h>=1100)&(slope>=.15)&(slope<.7)]=rgba('snow')
    attr=mesh.color_attributes.new(name='Color',type='BYTE_COLOR',domain='POINT')
    attr.data.foreach_set('color',colors.astype(np.float32).ravel())
    mesh.color_attributes.active_color_index=len(mesh.color_attributes)-1
    mesh.color_attributes.render_color_index=0
    mesh.materials.append(material('snow',vertex_color=True))


def build_terrain():
    from time import perf_counter
    started=perf_counter()
    path=BLENDER_DIR/'data/coastline.json'
    if not path.is_file():
        raise RuntimeError('Offline coastline is required: '+str(path))
    data=json.loads(path.read_text(encoding='utf-8'))
    lake_defs=[dict(lake,xy=clean_ring(lake['ring'])) for lake in data['lakes']]
    if len(lake_defs)!=8:
        raise RuntimeError('Expected all eight lake polygons in coastline.json')
    dem=DEMGrid.load(BLENDER_DIR/'data/dem_grid.json')
    routes=json.loads((PROJECT_ROOT/'map3d/web_assets/routes.json').read_text(encoding='utf-8'))
    roads=RoadCorridors(routes['routes'],dem)
    print('[terrain] DEM %dx%d, %d sampled nodes; %s' %
          (dem.nlat,dem.nlon,int(dem.valid.sum()),dem.source))
    print('[roads] %d segments, %d CDT points; supplied elevations %d, DEM fallbacks %d' %
          (len(roads.a),len(roads.points),roads.supplied_points,roads.fallback_points))
    print_lake_stats(dem,lake_defs)
    col=reset_collection('HM_Terrain')
    terrain=None
    max_road_adjustment=0.
    for definition in data['land']:
        name=definition['name']
        coast=clean_ring(definition['ring'])
        main=name=='SouthIsland'
        hint=name=='NorthIslandHint'
        # Base land contributes about 133k triangles, plus road controls.
        step=.15 if main else (.23 if not hint else .65)
        controls=[project(lon,lat) for _,lon,lat in SAMPLE_LOCATIONS] if main else []
        if not hint:
            rp=roads.points
            controls.extend(map(tuple,rp[inside(rp[:,0],rp[:,1],coast)]))
        xy,faces=constrained_grid(coast,step,[l['xy'] for l in lake_defs] if main else [],controls)
        x,y=xy[:,0],xy[:,1]
        if hint:
            h=np.full(len(x),65.)
        else:
            h=height_metres(x,y,dem)
            h,adjustment=roads.carve(xy,h)
            max_road_adjustment=max(max_road_adjustment,float(adjustment.max(initial=0)))
        if main:
            h=carve_lake_beds(xy,h,lake_defs)
        z=elevation_z(h)
        obj=mesh_object('Terrain' if main else name,np.column_stack((xy,z)).tolist(),faces,col,terrain)
        if main:
            terrain=obj
        terrain_colors(obj,xy,z,x<divide_x_at_y(y))
        print('[terrain] %s: %d triangles; grid %.3f' % (obj.name,len(faces),step))
        if main:
            indices=[int(np.argmin(np.sum((xy-np.array(p))**2,axis=1))) for p in controls[:len(SAMPLE_LOCATIONS)]]
            if np.max(np.linalg.norm(xy[indices]-np.array(controls[:len(SAMPLE_LOCATIONS)]),axis=1))>2e-6:
                raise RuntimeError('CDT lost an elevation diagnostic vertex')
            print_height_samples(h[indices],dem.sample(x[indices],y[indices]),lake_defs)
    if terrain is None:
        raise RuntimeError('SouthIsland ring must precede other islands')
    lakes_root=root('Lakes',col)
    lakes_root.parent=terrain
    for lake in lake_defs:
        lr=lake['xy']
        # A fine flat lake grid improves route water-height rasterisation too.
        xy,faces=constrained_grid(lr,.15)
        z=elevation_z(lake['elevation_m'])
        obj=mesh_object('Water_'+lake['name'],[(x,y,z) for x,y in xy],faces,col,lakes_root,'water')
        obj['surface_elevation_m']=lake['elevation_m']
    triangles,_,_=asset_stats(terrain)
    if not 120_000<=triangles<=250_000:
        raise RuntimeError('Terrain triangle budget missed: %d; adjust grid step in build_terrain.py' % triangles)
    terrain['coastline_source']=data['provenance']['source']
    terrain['height_exaggeration']=HEIGHT_EXAGGERATION
    terrain['elevation_source']=dem.source
    terrain['max_road_corridor_lowering_m']=max_road_adjustment
    print('[roads] Max road-corridor adjustment: %.1f m / Z %.5f (lowering only)' %
          (max_road_adjustment,elevation_z(max_road_adjustment)))
    export_glb(terrain,ASSET_DIR/'terrain_south_island.glb')
    print('[terrain] Finished: %d triangles including lake surfaces and context islands' % triangles)
    print('[terrain] Build and export took %.2f s' % (perf_counter()-started))


build_terrain()
