"""Cache OSM streets and building footprints around itinerary towns. Requires shapely and mapbox-vector-tile."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
import math
import subprocess
import mapbox_vector_tile
from shapely.geometry import LineString, MultiLineString, Point, box, shape
from shapely.prepared import prep
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
ZOOM=14
# West, south, east, north. Keep the airport-to-Riccarton corridor and the visited town centres.
AREAS=[(172.518,-43.542,172.61,-43.478),(170.455,-44.014,170.505,-43.992),
 (169.114,-44.708,169.153,-44.684),(167.698,-45.429,167.73,-45.401),
 (168.641,-45.042,168.683,-45.019),(168.378,-44.861,168.398,-44.84),
 (170.176,-43.399,170.192,-43.381),(172.955,-43.815,172.978,-43.797)]
def tile(lon,lat):
    return int((lon+180)/360*2**ZOOM),int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**ZOOM)
def fetch(url):
    return subprocess.check_output(['curl','--fail','--silent','--show-error','--retry','2','--max-time','35',url])
def run():
    areas=unary_union([box(*b) for b in AREAS])
    tiles=set()
    for west,south,east,north in AREAS:
        left,top=tile(west,north);right,bottom=tile(east,south)
        tiles.update((x,y) for x in range(left,right+1) for y in range(top,bottom+1))
    template=json.loads(fetch('https://tiles.openfreemap.org/planet'))['tiles'][0]
    roads=[];buildings=[];seen=set()
    def download(t):
        x,y=t
        data=fetch(template.format(z=ZOOM,x=x,y=y))
        if data[:2]==bytes([31,139]):data=gzip.decompress(data)
        return t,mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})
    def quant(lon,lat):return [round((lon-170.5)*80080),round(-(lat+44)*111320)]
    with ThreadPoolExecutor(max_workers=5) as pool:
        for (tx,ty),doc in pool.map(download,sorted(tiles)):
            def lonlat(p):
                return (tx+p[0]/4096)/2**ZOOM*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*(ty+p[1]/4096)/2**ZOOM))))
            tilebox=box(0,0,4096,4096)
            for feature in doc.get('transportation',{}).get('features',[]):
                props=feature['properties']
                if props.get('class') not in ('minor','service','tertiary','secondary','primary','trunk','motorway','residential'):continue
                geom=shape(feature['geometry']).intersection(tilebox)
                for line in getattr(geom,'geoms',[geom]):
                    if line.geom_type!='LineString' or line.is_empty:continue
                    trimmed=LineString([lonlat(p) for p in line.coords]).intersection(areas)
                    for piece in getattr(trimmed,'geoms',[trimmed]):
                        if piece.geom_type=='LineString' and piece.length>.000065:
                            coords=[quant(*pt) for pt in piece.simplify(.000016).coords]
                            if len(coords)>=2:roads.append(coords)
            for feature in doc.get('building',{}).get('features',[]):
                geom=shape(feature['geometry'])
                for footprint in getattr(geom,'geoms',[geom]):
                    if footprint.geom_type!='Polygon' or footprint.is_empty:continue
                    center=footprint.centroid
                    if not tilebox.covers(center):continue
                    lon,lat=lonlat((center.x,center.y))
                    if not any(l<lon<e and b<lat<t for l,b,e,t in AREAS):continue
                    rect=list(footprint.minimum_rotated_rectangle.exterior.coords)
                    sides=[]
                    for i in (0,1):
                        a,b=quant(*lonlat(rect[i])),quant(*lonlat(rect[i+1]))
                        sides.append((math.dist(a,b),math.atan2(a[1]-b[1],a[0]-b[0])))
                    length,angle=max(sides);width=min(sides)[0]
                    xy=quant(lon,lat);k=tuple(xy)
                    if k in seen or length<5 or length>130 or width<4:continue
                    seen.add(k);buildings.append(xy+[round(length),round(width),round(math.degrees(angle))])
    routes=json.loads((ROOT/'map3d/web_assets/routes.json').read_bytes())['routes']
    network=MultiLineString([[quant(lon,lat) for lat,lon in leg['points']] for leg in routes.values()])
    corridor=prep(network.buffer(1500,quad_segs=2))
    roads=[line for line in roads if corridor.intersects(LineString(line))]
    buildings=[b for b in buildings if corridor.contains(Point(b[:2]))]
    out={'source':'OpenFreeMap / OpenMapTiles, data © OpenStreetMap contributors (ODbL)',
         'areas':[quant(w,n)+quant(e,s) for w,s,e,n in AREAS],'streets':roads,'buildings':buildings}
    (ROOT/'atlas/settlements.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf8')
    print(len(tiles),'tiles,',len(roads),'street sections,',len(buildings),'buildings')
if __name__=='__main__':run()
