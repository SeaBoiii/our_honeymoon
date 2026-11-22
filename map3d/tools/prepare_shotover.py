"""Cache the Shotover River centreline near the Onsen viewpoint (River Environment Classification)."""
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from shapely.geometry import box, shape
from shapely.ops import unary_union, linemerge

SERVICE = 'https://services3.arcgis.com/fp1tibNcN9mbExhG/arcgis/rest/services/NZ_Rivers_and_Names_WFL1/FeatureServer/0'
BOUNDS = (168.665, -44.999, 168.705, -44.954)


def run():
    params = dict(where="upper(RivName) LIKE '%SHOTOVER%'", geometry=','.join(map(str,BOUNDS)),
                  geometryType='esriGeometryEnvelope', inSR=4326, outSR=4326,
                  spatialRel='esriSpatialRelIntersects', outFields='RivName', f='geojson')
    with urlopen(SERVICE+'/query?'+urlencode(params), timeout=40) as response:
        features = json.load(response)['features']
    segments = unary_union([shape(f['geometry']) for f in features]).intersection(box(*BOUNDS))
    if segments.is_empty:
        raise ValueError('No Shotover River data in the viewpoint bounds')
    if segments.geom_type == 'MultiLineString':
        segments = linemerge(segments)
    lines = getattr(segments,'geoms',[segments])
    result = [[[round(x,6),round(y,6)] for x,y in line.simplify(.000009).coords] for line in lines]
    target = Path(__file__).resolve().parents[2] / 'atlas/shotover.json'
    target.write_text(json.dumps(result,separators=(',',':'))+'\n',encoding='utf8')
    print(sum(map(len,result)), 'river vertices')


if __name__ == '__main__':
    run()
