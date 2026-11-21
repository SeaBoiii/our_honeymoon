"""Prepare the atlas coast and lakes from LINZ Topo50 GeoJSON (authoring: Shapely 2).
Pass a directory containing mainland.json and one <lake name>.geojson per lake.
Road shoulders reconcile the 1:50k water edge with the OSM road centreline.
"""
from pathlib import Path
import json
import sys
from shapely import affinity, make_valid
from shapely.geometry import LineString, Polygon, shape
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
def metric(g):return affinity.affine_transform(g,[80080,0,0,111320,-170.5*80080,44*111320])
def coords(ring):
    return [[round(x/80080+170.5,6),round(y/111320-44,6)] for x,y in list(ring.coords)[:-1]]
def polygon(g):
    if g.geom_type=='Polygon':return g
    return max((p for p in g.geoms if p.geom_type=='Polygon'),key=lambda p:p.area)
def read(file):return polygon(make_valid(metric(shape(json.loads(file.read_bytes())['features'][0]['geometry']))))
def main():
    source=Path(sys.argv[1])
    coast=ROOT/'blender/data/coastline.json'
    data=json.loads(coast.read_bytes())
    roads=json.loads((ROOT/'web_assets/routes.json').read_bytes())['routes']
    lines=[metric(LineString([(lon,lat) for lat,lon in route['points']])) for route in roads.values()]
    shoulders=unary_union([line.buffer(24,quad_segs=2) for line in lines])
    land=read(source/'mainland.json').simplify(67,preserve_topology=True)
    land=polygon(land.union(shoulders).buffer(0)).simplify(1)
    data['land'][0]['ring']=coords(land.exterior)
    for lake in data['lakes']:
        full=read(source/(lake['name']+'.geojson'))
        if any(line.intersects(full.buffer(-50)) for line in lines):
            raise ValueError('Review deep-water road crossing at '+lake['name'])
        shore=polygon(full.simplify(17,preserve_topology=True).difference(shoulders)).simplify(.8)
        lake['ring']=coords(shore.exterior)
        lake['islands']=[coords(h) for h in shore.interiors if Polygon(h).area>12000]
    data['provenance'].update(source='South Island and eight lakes: LINZ Topo50. Stewart Island and North Island context: Natural Earth.',
        license='LINZ CC BY 4.0; Natural Earth public domain; road alignments © OpenStreetMap contributors (ODbL).',
        accuracy='Cartographic generalisation: 67 m mainland coast, 17 m lake margins.',
        road_fit='24 m road shoulder at shoreline disagreements; source lake incursions deeper than 50 m require review.',
        lake_source='https://data.linz.govt.nz/layer/50293-nz-lake-polygons-topo-150k/',
        coast_source='https://data.linz.govt.nz/layer/50288-nz-island-polygons-topo-150k/')
    coast.write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
if __name__=='__main__':main()
