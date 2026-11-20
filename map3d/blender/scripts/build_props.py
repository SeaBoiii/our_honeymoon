"""Thirteen faceted tabletop landmarks and scatter props, no image textures."""
from pathlib import Path
PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon'))
exec(compile((PROJECT_ROOT / 'map3d/blender/scripts/common.py').read_text(encoding='utf-8'), 'common.py', 'exec'), globals())


def annulus(k, center, outer, inner, depth, mat, n=20):
    x,y,z=center
    verts=[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),z+dz)
           for r,dz in ((outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)) for i in range(n)]
    faces=[]
    for band in range(4):
        nxt=(band+1)%4
        faces.extend((band*n+i,band*n+(i+1)%n,nxt*n+(i+1)%n,nxt*n+i) for i in range(n))
    return k.mesh(verts,faces,mat,'HollowRim')


def tree(k, center=(0,0,0), willow=False, pine=False):
    x,y,z=center
    k.cone((x,y,z+.28),.065,.035,.56,'cedar',n=7,label='Trunk')
    if pine:
        for h,r in ((.37,.32),(.55,.26),(.72,.19)):
            k.cone((x,y,z+h),r,0,.42,'beech',n=8,label='ConiferTier')
    else:
        for dx,dy,dz in [(-.20,0,.56),(.18,.02,.59),(0,-.16,.65),(0,.16,.68),(0,0,.79)]:
            k.bar((x,y,z+.36),(x+dx,y+dy,z+dz),.025,'cedar',n=6,label='Branch')
            k.ball((x+dx,y+dy,z+dz),(.24,.23,.23),'pasture' if willow else 'beech',n=9,rings=3,label='Canopy')
            if willow:
                for a in (0,2.1,4.2):
                    px,py=x+dx+.18*math.cos(a),y+dy+.18*math.sin(a)
                    k.cone((px,py,z+dz-.18),.055,.12,.32,'pasture',n=6,label='DroopingWillow')


def church(k):
    k.cube((0,0,.035),(.68,.92,.07),'stone','Foundation')
    k.cube((0,-.07,.29),(.48,.70,.49),'stone','Nave')
    k.roof((0,-.07,.54),.56,.78,.20)
    k.cube((0,.32,.46),(.24,.24,.83),'stone','BellTower')
    k.roof((0,.32,.88),.29,.29,.12)
    for x in (-.248,.248):
        for y in (-.28,-.03,.20):
            k.cube((x,y,.34),(.018,.085,.20),'glass','ChapelWindow')
    k.cube((0,.449,.28),(.12,.015,.30),'cedar','Entrance')
    k.cube((0,.448,.73),(.12,.015,.15),'road','BelfryOpening')
    k.cone((0,.459,.71),.043,.028,.065,'tussock',n=8,label='Bell')
    k.bar((0,-.41,.70),(0,-.41,.84),.012,'road')
    k.bar((-.045,-.41,.79),(.045,-.41,.79),.012,'road')


def observatory(k):
    k.cone((0,0,.035),.45,.45,.07,'rock',n=16,label='Platform')
    k.cone((0,0,.23),.31,.31,.37,'cream',n=16,label='DomeDrum')
    k.ball((0,0,.415),(.34,.34,.33),'snow',n=16,rings=5,dome=True,label='ObservatoryDome')
    # A narrow dark strip follows the dome's meridian, suggesting an open slit.
    for i in range(7):
        a=(i+.5)*math.pi/14
        k.cube((0,-.344*math.cos(a),.415+.334*math.sin(a)),(.055,.055,.052),'road','DomeSlit')
    k.bar((0,-.15,.49),(0,-.39,.66),.039,'rock',label='Telescope')
    k.cube((0,-.315,.20),(.12,.026,.24),'cedar','Door')


def lone_tree(k):
    k.cone((0,0,.025),.42,.44,.05,'water',n=20,label='ShallowWaterBase')
    k.ball((-.045,0,.06),(.16,.13,.055),'stone',n=8,rings=2,label='PebbleShoal')
    tree(k,(0,0,.035),willow=True)


def hot_tub(k):
    k.mesh([(-.52,-.40,0),(.52,-.40,0),(.52,.43,.17),(-.52,.43,.17),
            (-.45,-.33,.25),(.45,-.33,.25),(.45,.36,.25),(-.45,.36,.25)],
           [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7),(3,2,1,0)],'rock','Cliff')
    k.cube((0,0,.275),(1.10,.90,.07),'cedar','Deck')
    for x in [i*.09-.45 for i in range(11)]:
        k.cube((x,0,.314),(.009,.87,.006),'stone','DeckSeam')
    annulus(k,(0,-.03,.48),.34,.282,.32,'cedar')
    k.cone((0,-.03,.52),.28,.28,.018,'water',n=20,label='TubWater')
    for h in (.365,.57):
        annulus(k,(0,-.03,h),.347,.337,.022,'road')
    for x in (-.42,.42):
        k.cube((x,.35,.54),(.045,.045,.44),'cedar','RailingPost')
    k.cube((0,.35,.75),(.90,.045,.045),'cedar','RailingTop')
    for x in (-.12,.12):
        k.cube((x,-.31,.64),(.14,.08,.045),'cream','HeadRest')


def mosque(k):
    k.cube((0,0,.025),(.90,.75,.05),'stone','Courtyard')
    k.cube((-.06,0,.25),(.58,.51,.45),'cream','PrayerHall')
    k.ball((-.06,0,.475),(.27,.25,.25),'snow',n=16,rings=5,dome=True,label='Dome')
    k.bar((-.06,0,.71),(-.06,0,.80),.012,'tussock')
    k.cone((.34,.15,.43),.075,.060,.81,'cream',n=10,label='Minaret')
    k.cone((.34,.15,.72),.095,.095,.045,'stone',n=10,label='Balcony')
    k.cone((.34,.15,.92),.09,0,.18,'water',n=10,label='MinaretCap')
    for x in (-.23,-.06,.11):
        k.cube((x,-.263,.24),(.09,.018,.22),'glass','ArchedDoor')
        k.ball((x,-.267,.35),(.045,.018,.045),'glass',n=8,rings=3,label='ArchTop')


def city(k):
    k.cube((0,0,.025),(1.0,1.0,.05),'road','StreetBlock')
    # Twelve buildings, with a pedestrian gap down the middle of the block.
    for ix,x in enumerate((-.34,-.12,.12,.34)):
        for iy,y in enumerate((-.33,0,.33)):
            height=(.21,.36,.27,.45,.24,.32,.41,.23,.34,.26,.39,.29)[ix*3+iy]
            mat=('stone','cream','snow')[(ix+iy)%3]
            k.cube((x,y,.05+height/2),(.175,.235,height),mat,'Building')
            k.cube((x,y,.055+height),(.182,.242,.025),'rock','Roof')
            for level in range(1,int(height/.09)+1):
                for dx in (-.045,.045):
                    k.cube((x+dx,y-.119,.065+level*.07),(.041,.007,.028),'glass','Window')
    for y in (-.17,.17):
        k.cube((0,y,.055),(.96,.016,.006),'snow','RoadMarking')


def cave(k):
    # Separate rocky arch voussoirs leave a genuine empty cave entrance.
    for i in range(9):
        a=math.pi*i/8
        x,z=.36*math.cos(a),.20+.37*math.sin(a)
        obj=k.cube((x,.04,z),(.23,.35,.23),'rock','ArchRock')
        obj.rotation_euler.y=-a
    k.cube((0,.235,.25),(.74,.035,.45),'road','CaveDarkInterior')
    k.cone((0,-.06,.035),.47,.47,.07,'fiord',n=16,label='CavePool')
    # Little open boat below the arch.
    k.ball((0,-.14,.105),(.10,.22,.055),'cedar',n=8,rings=3,label='TinyBoat')
    k.cube((0,-.14,.143),(.11,.24,.012),'road','BoatInterior')
    for i in range(19):
        x=.29*math.sin(i*2.4); y=.12+.06*math.cos(i*1.3)
        z=.26+.24*((i*7)%19)/19
        k.ball((x,y,z),(.011,.011,.014),material('glow',emission=3),n=5,rings=2,label='Glowworm')


def ski_lift(k):
    k.mesh([(-.60,-.38,0),(.60,-.38,0),(.60,.38,.26),(-.60,.38,.26),
            (-.60,-.38,.06),(.60,-.38,.06),(.60,.38,.32),(-.60,.38,.32)],
           [(4,5,6),(4,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(3,2,1,0)],'snow','SnowSlope')
    stations=[]
    for i in range(3):
        x=-.44+i*.44; y=-.27+i*.27; z=.09+i*.09
        k.bar((x,y,z),(x,y,z+.52),.026,'rock',label='LiftTower')
        k.cube((x,y,z+.52),(.25,.055,.035),'road','CrossArm')
        stations.append((x,y,z+.56))
    for a,b in zip(stations,stations[1:]):
        for offset in (-.10,.10):
            k.bar((a[0]+offset,a[1],a[2]),(b[0]+offset,b[1],b[2]),.009,'road',n=5,label='Cable')
        for t in (.30,.72):
            x=a[0]*(1-t)+b[0]*t-.1; y=a[1]*(1-t)+b[1]*t; z=a[2]*(1-t)+b[2]*t
            k.bar((x,y,z),(x,y,z-.15),.009,'road',n=5,label='ChairHanger')
            k.cube((x,y,z-.16),(.16,.10,.025),'red','ChairSeat')
            k.cube((x,y+.045,z-.105),(.16,.02,.10),'red','ChairBack')


def glacier(k):
    # Gaps between irregular ice columns read as crevasses from the map camera.
    for row in range(5):
        for column in range(4):
            x=(column-1.5)*.20+(.022 if row%2 else 0)
            y=(row-2)*.19
            height=.12+.055*row+.09*(.5+.5*math.sin(column*3.1+row*1.7))
            obj=k.cone((x,y,height/2),.093,.080,height,'ice' if (row+column)%3 else 'snow',n=5,label='IceSerac')
            obj.rotation_euler.z=.21*row+.13*column
            # Thin snow cap leaves the dark blue vertical faces visible.
            k.cone((x,y,height+.006),.094,.078,.018,'snow',n=5,label='SnowCap')


def sheep(k):
    for x in (-.17,.17):
        for y in (-.23,.23):
            k.cone((x,y,.16),.038,.031,.31,'road',n=6,label='Leg')
    k.ball((0,0,.42),(.27,.36,.25),'snow',n=12,rings=4,label='Wool')
    k.ball((0,.34,.48),(.14,.18,.16),'road',n=8,rings=3,label='Head')
    for x in (-.17,.17):
        k.ball((x,.32,.55),(.09,.055,.038),'road',n=6,rings=2,label='Ear')
    k.ball((0,-.35,.44),(.07,.10,.07),'snow',n=6,rings=2,label='Tail')


def pin(k):
    # A red extruded frame with actual empty heart aperture, no painted inset.
    # Radial correspondence builds the ring without booleans or fragile holes.
    n=48; inner=[]; outer=[]
    for i in range(n):
        t=math.tau*i/n
        x=.0135*16*math.sin(t)**3
        z=.65+.0135*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))
        inner.append((x,z))
        dx,dz=x,z-.65
        angle=math.atan2(dz,dx)
        # Teardrop radial boundary: circular shoulders and an elongated tip.
        down=max(0,-math.sin(angle))
        radius=.35+.30*down**5
        outer.append((radius*math.cos(angle),.65+radius*math.sin(angle)))
    vertices=[(x,y,z) for y in (-.065,.065) for contour in (outer,inner) for x,z in contour]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    k.mesh(vertices,faces,'red','HeartApertureFrame')


BUILDERS=[('church_stone','StoneChurch',church),('observatory','Observatory',observatory),
          ('lone_tree','LoneTree',lone_tree),('hot_tub','HotTub',hot_tub),('mosque','Mosque',mosque),
          ('city','City',city),('glowworm_cave','Cave',cave),('ski_lift','SkiLift',ski_lift),
          ('glacier_ice','GlacierIce',glacier),('pine_tree','PineTree',lambda k:tree(k,pine=True)),
          ('beech_tree','BeechTree',tree),('sheep','Sheep',sheep),('pin','Pin',pin)]

import bmesh
for _file,_name,_builder in BUILDERS:
    _kit=Kit(_name,reset_collection('HM_'+_name))
    _builder(_kit)
    for _obj in descendants(_kit.obj):
        if _obj.type=='MESH':
            _bm=bmesh.new(); _bm.from_mesh(_obj.data)
            bmesh.ops.recalc_face_normals(_bm,faces=list(_bm.faces))
            _bm.to_mesh(_obj.data); _bm.free()
    _kit.finish(_file)
print('[props] Finished 13 assets; largest dimension 1 unit, bottom-centre roots.')
