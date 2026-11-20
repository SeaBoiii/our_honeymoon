"""Run with Python, Shapely 2 and Node. Check the actual player's rounded paths.
An optional browser audit JSON can be supplied to check a particular rendered cut.
"""
from pathlib import Path
import json
import subprocess
import sys
import math
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT=Path(__file__).resolve().parents[2]
def xy(p):
    lon,lat=p
    return ((lon-170.5)*8.008,-(lat+44)*11.132)
def measure(tracks):
    data=json.loads((ROOT/'map3d/blender/data/coastline.json').read_bytes())
    mainland=Polygon([xy(p) for p in data['land'][0]['ring']])
    lakes={l['name']:Polygon([xy(p) for p in l['ring']],[[xy(p) for p in ring] for ring in l.get('islands',[])]) for l in data['lakes']}
    dry=mainland.difference(unary_union(list(lakes.values())))
    edges=[]
    for poly in [mainland,*lakes.values()]:
        for ring in [poly.exterior,*poly.interiors]:
            points=list(ring.coords)
            edges.extend(zip(points,points[1:]))
    tree=STRtree(shapely.linestrings(np.asarray(edges)))
    fleet=json.loads((ROOT/'atlas/vehicle-dimensions.json').read_bytes());metre=fleet['mapUnitsPerMetre']
    assert len(tracks)==21,'expected 17 driving legs and four cruise legs'
    for track in tracks:
        mode,day=track['mode'],track['day']
        p=np.asarray(track['points'])
        path=LineString(p[:,:2])
        if mode=='boat':
            assert (lakes['Te Anau'].covers(path) if day==5 else mainland.disjoint(path)),track['caption']
        else:assert dry.covers(path),track['caption']
        segments=shapely.linestrings(np.stack([p[:-1,:2],p[1:,:2]],axis=1))
        clearance=shapely.distance(segments,tree.geometries.take(tree.nearest(segments)))
        vehicle=fleet['vehicles'][mode]
        length,width=metre*vehicle['length']*.5,metre*vehicle['width']*.5
        radius=math.hypot(length,width)
        if mode!='boat':
            assert np.min(clearance)>2.95*metre*1.09,('road shoulder crosses shoreline',track['caption'])
        for i in np.flatnonzero(clearance<radius):
            # The whole rectangle sweeps between the two poses. A circumscribed disk
            # is unnecessarily wide on a long coach travelling parallel to the shore.
            def corners(t):
                x,z,yaw=p[i]+t*(p[i+1]-p[i])
                sn,cs=math.sin(yaw),math.cos(yaw)
                return [(x+f*sn+w*cs,z+f*cs-w*sn) for f,w in
                        [(-length,-width),(length,-width),(length,width),(-length,width)]]
            angle=abs(p[i+1,2]-p[i,2]);pieces=max(1,math.ceil(angle/.04))
            for j in range(pieces):
                outer=shapely.MultiPoint(corners(j/pieces)+corners((j+1)/pieces)).convex_hull
                sag=radius*(1-math.cos(angle/(2*pieces)))
                if sag>1e-12:outer=outer.buffer(sag,quad_segs=4)
                allowed=dry.covers(outer) if mode!='boat' else (lakes['Te Anau'].covers(outer) if day==5 else mainland.disjoint(outer))
                assert allowed,(day,mode,track['caption'],'vehicle footprint crossed the shoreline',i)
        if 'submerged' in track:
            assert track['submerged']==0 and track['nonfinite']==0,(day,mode,'terrain collision')
            assert track['worstFloor']<.001,(day,mode,'road below terrain')
            assert track['angular']<3.,(day,mode,'excessive angular step')
        print(f'Day {day:2} {mode:5} | {len(p):5} points | full body and shoreline clear')
if __name__=='__main__':
    if len(sys.argv)>1:tracks=json.loads(Path(sys.argv[1]).read_bytes())
    else:
        tracks=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('sample_surface_routes.cjs'))],cwd=ROOT))
    measure(tracks)
