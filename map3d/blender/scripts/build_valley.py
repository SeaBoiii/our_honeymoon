"""A winter cutaway of Hooker Valley, modelled for close orbit and the atlas cover."""
from pathlib import Path
import math
import random

PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon'))
exec(compile((PROJECT_ROOT/'map3d/blender/scripts/common.py').read_text(encoding='utf-8'), 'common.py', 'exec'), globals())


def build_valley():
    rng = random.Random(270827)
    k = Kit('HookerValley', reset_collection('HM_HookerValley'))
    tau = math.tau
    snow, firn, shadow = '#fff9e8', '#dbeded', '#b6d2d5'
    slate, schist, scree = '#516970', '#758582', '#a2a696'
    moss, tussock, straw = '#77875c', '#aaa267', '#c1b579'
    water, riffle = '#3caead', '#a1e4d5'
    river_z = .24

    def channel(y):
        return -.24 + .46*math.sin(1.35*y+.15) + .17*y

    def ground(x,y):
        # Overlapping sharp ridges at the head of the valley, a glacial trough below.
        peaks = [(-2.05,1.03,2.14),(-1.30,1.66,2.84),(-.62,1.56,2.38),
                 (.25,1.83,3.42),(1.09,1.62,2.47),(1.91,1.18,1.91),(2.60,.83,1.36)]
        ridge = max(h-1.12*abs(x-px)-1.42*abs(y-py)
                    -.37*abs((x-px)*.74+(y-py)) for px,py,h in peaks)
        ridge += .115*math.sin(5.4*x+2*y)+.09*math.sin(8*y-3*x)+.044*math.cos(12*x+7*y)
        bank = .47+.07*math.sin(1.8*x+y)+.085*math.cos(2*y-.8*x)
        channel_depth = .42*math.exp(-((x-channel(y))/.51)**4)
        return max(.07, max(bank, ridge)-channel_depth)

    def radius(a):
        return 1+.043*math.sin(3*a+.6)+.026*math.sin(7*a+1.3)+.013*math.cos(11*a)

    sectors, rings = 144, 32
    verts = [(0,0,ground(0,0))]
    for j in range(1,rings+1):
        for i in range(sectors):
            a = tau*(i+.28*(j%2))/sectors
            d = j/rings*radius(a)
            x,y = 3.55*d*math.cos(a), 2.42*d*math.sin(a)
            verts.append((x,y,ground(x,y)))
    faces=[(0,1+i,1+(i+1)%sectors) for i in range(sectors)]
    for j in range(1,rings):
        for i in range(sectors):
            a=1+(j-1)*sectors+i; b=1+(j-1)*sectors+(i+1)%sectors
            if j%2:
                faces.extend([(a,a+sectors,b),(b,a+sectors,b+sectors)])
            else:
                faces.extend([(a,a+sectors,b+sectors),(a,b+sectors,b)])
    surface=k.mesh(verts,faces,slate,'AlpineRelief')
    colors=[slate,schist,scree,moss,tussock,straw,shadow,firn,snow]
    for c in colors[1:]:
        surface.data.materials.append(material(c))
    for face in surface.data.polygons:
        x,y,z=face.center
        # Snow collects on high shelves. Exposed ribs break up the snowline.
        exposure=.21*math.sin(5*x-2*y)+.16*math.cos(6*(x+y))+.33*(1-face.normal.z)
        score=z-exposure
        if score>1.53:
            idx=8 if face.normal.x<.25 else 7 if face.normal.y<.55 else 6
        elif score>1.14:
            idx=7 if face.normal.z>.72 else 1 if face.normal.x<.3 else 0
        elif z>.67:
            idx=2 if face.normal.z>.65 else 1
        else:
            idx=3 if math.sin(x*2+y*3)+.32*math.cos(x*7)<.08 else 4
            if abs(x-channel(y))<.48 or z<.3: idx=2
            if rng.random()<.05: idx=5
        face.material_index=idx

    edge=verts[-sectors:]
    # A geological cut edge makes the relief readable from underneath and at a distance.
    walls=[]; wall_faces=[]
    for i,(x,y,z) in enumerate(edge):
        seam=.038*math.sin(i*.34)
        walls.extend([(x,y,max(z,river_z)),(x*.998,y*.998,.05+seam),(x*.985,y*.985,-.09+seam),
                      (x*.97,y*.97,-.22+seam*.5),(x*.946,y*.946,-.32)])
    for i in range(sectors):
        a=5*i; b=5*((i+1)%sectors)
        wall_faces.extend((a+j,a+j+1,b+j+1,b+j) for j in range(4))
    wall_faces.append(tuple(5*i+4 for i in reversed(range(sectors))))
    walls_obj=k.mesh(walls,wall_faces,'#8d866e','StratifiedEdge')
    for c in ('#a99574','#635e56','#534e48'):
        walls_obj.data.materials.append(material(c))
    for f in walls_obj.data.polygons:
        f.material_index=min(f.index%4,3) if f.index<sectors*4 else 3
    k.mesh([(x,y,river_z) for x,y,_ in edge],[tuple(range(sectors))],water,'River')
    # The bridge follows two catenary-like cables, with a shallow sag in the walkway.
    by=-.93; cx=channel(by); half=1.02
    def deck(t): return .65+.096*t*t
    for i in range(34):
        t=-1+(i+.5)*2/34
        k.cube((cx+t*half,by,deck(t)),(.056,.26,.036),'#b77c48','TimberPlank')
    for side in (-1,1):
        y=by+side*.145
        cable=[]
        for i in range(19):
            t=-1+i/9
            cable.append((cx+t*half,y,.94+.42*t*t))
            if i%2==0:
                k.bar((cx+t*half,y,deck(t)),cable[-1],.008,'#394b49',6,'Hanger')
        for a,b in zip(cable,cable[1:]):
            k.bar(a,b,.018,'#d0b590',8,'Cable')
        for t in (-1,1):
            x=cx+t*half
            k.bar((x,y,ground(x,y)-.05),(x,y,1.40),.055,'#72543a',8,'Portal')
            k.bar((x,y,1.37),(x+t*.46,y,ground(x+t*.46,y)),.014,'#574e40',6,'Backstay')
    # Diamond wire infill and deck fasteners beneath the sculpted suspension cables.
    for side in (-1,1):
        y=by+side*.141
        for i in range(28):
            t=-1+2*i/28;u=t+2/28;x=cx+t*half;xx=cx+u*half
            z=deck(t)+.037;zz=deck(u)+.037
            k.bar((x,y,z),(xx,y,zz+.12),.004,'#58625a',5,'MeshWire')
            k.bar((x,y,z+.12),(xx,y,zz),.004,'#58625a',5,'MeshWire')
            k.cone((x,y-side*.025,z-.010),.008,.007,.009,'#66645c',n=8,label='DeckBolt')
    for t in (-1,1):
        k.cube((cx+t*half,by,1.395),(.11,.42,.11),'#ac8054','Lintel')

    # Sparse riverbank conifers, stones, tussock and glints at physical scales.
    for i in range(105):
        x,y=rng.uniform(-3.15,3.15),rng.uniform(-2.05,1.00)
        z=ground(x,y)
        if (x/3.35)**2+(y/2.20)**2>.95 or z<.31 or z>.86: continue
        if abs(y-by)<.30 and abs(x-cx)<1.42: continue
        if (x>1.1 or x<-.92) and rng.random()<.66:
            h=rng.uniform(.19,.49)
            k.cone((x,y,z+h*.25),h*.065,h*.044,h*.54,'cedar',n=5,label='Trunk')
            for tier,col in enumerate(('#385a50','#4b6c5b','#678568')):
                radius=h*(.24-tier*.047)
                base=z+h*(.21+tier*.19)
                rim=[(x+math.cos(j*tau/12+tier)*radius*(1 if j%2 else .66),
                      y+math.sin(j*tau/12+tier)*radius*(1 if j%2 else .66),
                      base+(.035*h if j%2 else .11*h)) for j in range(12)]
                k.mesh(rim+[(x,y,base+h*(.56-tier*.045))],
                       [(j,(j+1)%12,12) for j in range(12)]+[tuple(reversed(range(12)))],col,'FirBough')
        else:
            for j in range(3):
                dx,dy=rng.uniform(-.06,.06),rng.uniform(-.04,.04)
                k.mesh([(x-.02+dx,y+dy,z),(x+.018+dx,y+dy,z),(x+2*dx,y+2*dy,z+rng.uniform(.07,.14))],
                       [(0,1,2)],straw,'Tussock')
    for i in range(55):
        y=rng.uniform(-2.12,.52); x=channel(y)+rng.choice((-1,1))*rng.uniform(.26,.58)
        z=ground(x,y)
        if z<.34:
            s=rng.uniform(.024,.088)
            k.ball((x,y,max(river_z-.015,z)),(1.5*s,s,.68*s),scree,n=5,rings=2,label='Shingle')
    for i in range(40):
        y=rng.uniform(-2.15,.35); x=channel(y)+rng.uniform(-.29,.29)
        if ground(x,y)<river_z-.014:
            k.mesh([(x-.025,y,river_z+.004),(x,y-.073,river_z+.004),(x+.014,y+.064,river_z+.004)],
                   [(0,1,2)],riffle,'Current')
    return k.finish('hooker_valley')


build_valley()
