"""Five original, generic-livery low-poly vehicles. All noses face +Y."""
from pathlib import Path
PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon'))
exec(compile((PROJECT_ROOT / 'map3d/blender/scripts/common.py').read_text(encoding='utf-8'), 'common.py', 'exec'), globals())


def wheels(k, axles, width, radius, z=None):
    for y in axles:
        for side in (-1,1):
            x=side*width/2
            k.cone((x,y,z or radius),radius,radius,.18,'road',n=28,axis=(1,0,0),label='Tyre')
            k.cone((x+side*.095,y,z or radius),radius*.65,radius*.65,.025,'rock',n=20,axis=(1,0,0),label='Hub')
            for i in range(5):
                a = i * math.tau / 5
                k.bar((x+side*.112,y,z or radius),
                      (x+side*.112,y+radius*.51*math.cos(a),(z or radius)+radius*.51*math.sin(a)),
                      radius*.057,'cream',n=6,label='HubSpoke')


def road_proportions(k, width_factor, height_factor):
    """Set realistic body ratios while retaining round wheels and unit scales."""
    stretch=Matrix.Diagonal((width_factor,1.0,height_factor,1.0))
    for obj in k.obj.children:
        if obj.type!='MESH':
            raise RuntimeError('Road proportions expects direct mesh children')
        rotation=(obj.rotation_quaternion if obj.rotation_mode=='QUATERNION' else obj.rotation_euler.to_quaternion()).to_matrix().to_4x4()
        if '_Tyre_' in obj.name or '_Hub_' in obj.name:
            obj.data.transform(Matrix.Scale(height_factor,4))
        else:
            obj.data.transform(rotation.inverted() @ stretch @ rotation)
        obj.location=stretch.to_3x3() @ obj.location


def build_car():
    k=Kit('Car',reset_collection('HM_Car'))
    # Cross sections define the rising bonnet, raked windscreen and rear hatch.
    def shell(stations, paint, name):
        vertices=[]
        for y,w,bottom,top in stations:
            shoulder=top-(top-bottom)*.18
            vertices.extend([(u*w,y,h) for u,h in ((-.89,bottom),(-1,bottom+.07),
                (-1,shoulder),(-.84,top),(.84,top),(1,shoulder),(1,bottom+.07),(.89,bottom))])
        faces=[tuple(range(7,-1,-1)),tuple(range(len(vertices)-8,len(vertices)))]
        for start in range(0,len(vertices)-8,8):
            faces.extend((start+i,start+(i+1)%8,start+(i+1)%8+8,start+i+8) for i in range(8))
        body=k.mesh(vertices,faces,paint,name)
        bm=bmesh.new(); bm.from_mesh(body.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(body.data); bm.free()
    shell([(-1.84,.82,.41,.79),(-1.6,.96,.34,.93),(-.8,.97,.33,1.01),
           (.62,.96,.33,.99),(1.55,.92,.36,.87),(1.84,.82,.42,.78)],'red','BodyShell')
    shell([(-1.45,.78,.90,1.02),(-1.14,.79,.91,1.46),(-.83,.80,.91,1.52),
           (.29,.78,.92,1.51),(.93,.78,.90,1.00)],'glass','PanoramicGlazing')
    k.cube((0,-.33,1.51),(1.39,1.40,.075),'red','Roof')
    for x in (-.837,.837):
        k.bar((x*.96,-.38,.97),(x*.94,-.38,1.47),.032,'road',label='Pillar')
        k.cube((x*1.16,0,.42),(.045,2.1,.095),'road','Sill')
        for y in (-.7,.55):
            k.cube((x*1.025,y,.88),(.045,.25,.035),'road','Handle')
        k.cube((x*1.17,.72,1.12),(.22,.20,.13),'red','Mirror')
    for x in (-.65,.65):
        k.cube((x,1.838,.72),(.38,.035,.18),'snow','Headlamp')
        k.cube((x,-1.838,.75),(.30,.035,.17),'red','TailLamp')
    k.cube((0,1.846,.54),(.82,.035,.16),'road','Grille')
    k.cube((0,-1.84,.40),(1.65,.08,.14),'road','Bumper')
    wheels(k,[-1.14,1.15],1.87,.37)
    for y in (-.85,.45):
        k.cube((0,y,1.56),(1.55,.11,.10),'road','RoofRack')
    for x in (-.35,.35):
        k.cube((x,-.06,1.67),(.13,2.75,.055),'snow','Ski')
        k.cube((x,.07,1.73),(.14,.25,.10),'road','Binding')
    road_proportions(k,.83,.95)
    return k.finish('car',True)


def build_coach():
    k=Kit('Coach',reset_collection('HM_Coach'))
    k.cube((0,0,.73),(1.30,4.25,.82),'snow','CoachLower')
    k.cube((0,0,1.45),(1.28,4.18,.68),'snow','CoachUpper')
    k.cube((0,2.103,1.47),(1.13,.026,.53),'glass','Windscreen')
    k.cube((0,-2.103,1.49),(1.10,.026,.45),'glass','RearWindow')
    for side in (-1,1):
        for y in (-1.65,-.96,-.27,.42,1.11,1.75):
            k.cube((side*.649,y,1.47),(.025,.55,.49),'glass','PassengerWindow')
        k.cube((side*.665,0,.91),(.025,4.08,.16),'water','TealStripe')
        for y in (-1.30,-.43,.45):
            k.cube((side*.657,y,.58),(.024,.76,.35),'cream','LuggageDoor')
        k.bar((side*.62,1.90,1.55),(side*.80,2.00,1.59),.035,'road')
        k.cube((side*.82,2.0,1.51),(.09,.11,.23),'road','Mirror')
    k.cube((.652,1.62,.84),(.028,.56,.82),'glass','EntryDoor')
    k.cube((0,-.2,1.84),(.75,1.25,.13),'rock','RoofAC')
    wheels(k,[-1.35,-.87,1.40],1.30,.30)
    for x in (-.44,.44):
        k.cube((x,2.14,.58),(.21,.03,.12),'snow','Headlamp')
        k.cube((x,-2.14,.61),(.18,.03,.12),'red','TailLamp')
    road_proportions(k,.70,.70)
    return k.finish('coach',True)


def build_helicopter():
    k=Kit('Helicopter',reset_collection('HM_Helicopter'))
    # Continuous airframe from the tail cone to the canopy. Use the actual
    # curved skin for glazing so the windscreen sits flush with the fuselage.
    stations=[(-2.65,.045,1.23,1.34),(-2.39,.068,1.19,1.37),(-1.82,.10,1.12,1.38),
              (-1.23,.16,.97,1.43),(-.88,.28,.73,1.48),(-.56,.45,.53,1.58),
              (-.36,.55,.44,1.63),(-.30,.57,.43,1.65),(.18,.64,.40,1.67),
              (.23,.65,.40,1.67),(.64,.63,.41,1.63),(.97,.55,.45,1.53),
              (1.22,.42,.51,1.40),(1.40,.25,.62,1.25),(1.47,.08,.78,1.09),(1.49,.008,.89,.98)]
    sides=32; vertices=[]; faces=[]; coatings=[]
    for y,w,lo,hi in stations:
        for i in range(sides):
            a=i*math.tau/sides
            vertices.append((w*math.cos(a),y,(hi+lo)/2+(hi-lo)*.5*math.sin(a)))
    for j in range(len(stations)-1):
        for i in range(sides):
            b=(i+1)%sides; a=(i+.5)*math.tau/sides; height=math.sin(a)
            faces.append((j*sides+i,(j+1)*sides+i,(j+1)*sides+b,j*sides+b))
            if j<5: coat=1 if height<-.10 or j==1 else 0
            elif height<-.62: coat=2
            elif height<-.22: coat=1
            elif j>=7 and j!=8 and (height<.86 or j>=10):
                coat=3 if abs(math.cos(a))>.10 or j<10 else 0
            else: coat=0
            coatings.append(coat)
    faces.extend([tuple(range(sides)),tuple(reversed(range(len(vertices)-sides,len(vertices))))]);coatings.extend([0,1])
    shell=k.mesh(vertices,faces,'snow','StreamlinedAirframe')
    for col in ('red','road','glass'):
        shell.data.materials.append(material(col))
    for face,coat in zip(shell.data.polygons,coatings):
        face.material_index=coat;face.use_smooth=True
    k.ball((0,-.40,1.56),(.32,.57,.19),'snow',n=18,rings=6,label='TurbineCowling')
    for side in (-1,1):
        k.cone((side*.20,-.78,1.65),.094,.087,.24,'rock',n=16,axis=(0,1,.15),label='Exhaust')
        k.cone((side*.20,-.907,1.63),.071,.071,.014,'road',n=14,axis=(0,1,.15),label='ExhaustBore')
        for slot in range(5):
            k.bar((side*.271,-.55+slot*.074,1.57),(side*.254,-.52+slot*.074,1.66),
                  .013,'road',6,label='CowlingLouvre')
    for side in (-1,1):
        k.cube((side*.615,.10,.90),(.038,.12,.03),'cream','DoorLatch')
        k.bar((side*.40,.78,.65),(side*.63,.64,.23),.045,'rock')
        k.bar((side*.38,-.31,.65),(side*.63,-.40,.23),.045,'rock')
        k.bar((side*.65,-.79,.16),(side*.65,1.18,.16),.055,'road',label='Skid')
        k.bar((side*.65,1.18,.16),(side*.65,1.39,.26),.055,'road')
    k.mesh([(-.04,-2.68,1.16),(.04,-2.68,1.16),(-.04,-2.46,2.0),(.04,-2.46,2.0),
            (-.04,-2.04,1.27),(.04,-2.04,1.27)],
           [(0,4,2),(1,3,5),(0,1,5,4),(2,4,5,3),(0,2,3,1)],'red','TailFin')
    k.cube((0,-1.95,1.26),(1.01,.28,.07),'red','Tailplane')
    k.cone((0,.20,1.79),.055,.055,.42,'road',label='Mast')
    rotor=root('Rotor',k.col); rotor.parent=k.obj; rotor.location=(0,.20,2.02)
    # Main rotor lies in local XY, rotating about local Z -> three.js Y.
    for i in range(3):
        a=i*math.tau/3+.2
        def blade_section(start,end,mat):
            v=[(-.06,start,0),(.10,start,.022),(.045,end,.04),(-.085,end,.02)]
            blade=k.mesh(v+[(x,y,z-.023) for x,y,z in v],
                         [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,'RotorBlade',parent=rotor)
            blade.rotation_euler.z=a
        blade_section(.10,1.94,'road')
        blade_section(1.94,2.08,'#e1a741')
    k.cone((0,0,.025),.14,.11,.10,'rock',parent=rotor)
    tail=root('TailRotor',k.col); tail.parent=k.obj; tail.location=(.17,-2.47,1.53)
    # Tail rotor lies in local YZ, rotating about local X -> three.js X.
    for angle in (0,math.pi/2):
        blade=k.cube((0,0,0),(.035,.74,.065),'road','TailBlade',parent=tail)
        blade.rotation_euler.x=angle
    k.cone((0,0,0),.07,.07,.10,'rock',axis=(1,0,0),parent=tail)
    result=k.finish('helicopter',True)
    if rotor.parent!=result or tail.parent!=result or any(abs(v)>1e-6 for v in rotor.rotation_euler):
        raise RuntimeError('Rotor pivots must remain direct, unrotated children')
    return result


def build_boat():
    k=Kit('Boat',reset_collection('HM_Boat'))
    # Hull rings taper to a pointed +Y bow; closed bottom, deck and sides.
    outline=[(-.62,-1.90),(.62,-1.90),(.73,-1.80),(.80,-1.28),(.82,-.5),(.82,.40),
             (.79,.92),(.69,1.28),(.55,1.57),(.34,1.82),(.13,2.03),(0,2.12),
             (-.13,2.03),(-.34,1.82),(-.55,1.57),(-.69,1.28),(-.79,.92),(-.82,.4),(-.82,-.5),(-.80,-1.28),(-.73,-1.80)]
    rings=[(.30,.80,.035),(.68,.92,.15),(.90,.97,.30),(.99,1,.47),(1,1,.55),(.995,1,.595)]
    verts=[(x*w,y*l,h+.07*max(y-1,0)**2) for w,l,h in rings for x,y in outline]
    n=len(outline)
    faces=[tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
    for band in range(len(rings)-1):
        faces.extend((band*n+i,band*n+(i+1)%n,(band+1)*n+(i+1)%n,(band+1)*n+i) for i in range(n))
    hull=k.mesh(verts,faces,'fiord','FlaredHull')
    for col in ('cedar','snow','road'):
        hull.data.materials.append(material(col))
    hull.data.polygons[1].material_index=1
    for face in list(hull.data.polygons)[2:]:
        band=(face.index-2)//n
        face.material_index=2 if band==3 else 3 if band==4 else 0
        face.use_smooth=band<3
    k.cube((0,-.10,.89),(1.34,2.80,.61),'snow','MainCabin')
    k.cube((0,-.18,1.23),(1.48,3.00,.09),'snow','UpperDeck')
    k.cube((0,.47,1.48),(1.04,1.25,.49),'snow','Wheelhouse')
    for side in (-1,1):
        for y in (-1.13,-.48,.17,.82):
            k.cube((side*.681,y,.93),(.025,.50,.32),'glass','SaloonWindow')
        k.cube((side*.533,.47,1.50),(.025,.99,.29),'glass','BridgeWindow')
        for y in (-1.53,-.8,0,.8,1.30):
            k.bar((side*.71,y,1.26),(side*.71,y,1.64),.022,'road')
        k.bar((side*.71,-1.53,1.64),(side*.71,1.30,1.64),.022,'road')
    k.cube((0,1.108,1.50),(.88,.026,.29),'glass','BridgeFront')
    k.cube((0,-1.52,1.51),(1.41,.035,.025),'road','SternRail')
    k.cone((0,.31,1.93),.035,.025,.52,'road',label='Antenna')
    for x in (-.43,.43):
        k.ball((x,-.70,1.36),(.17,.42,.09),'red',n=8,rings=3,label='LifeRaft')
    for y in (-.98,-.65,-.32):
        for side in (-1,1):
            k.cube((side*.36,y,1.37),(.44,.14,.08),'cedar','ObservationBench')
            k.cube((side*.36,y-.065,1.47),(.44,.035,.18),'cedar','SeatBack')
    for side in (-1,1):
        for y,x in ((-1.40,.79),(-.68,.82),(.05,.83),(.78,.81),(1.36,.67)):
            k.ball((side*x,y,.48),(.054,.082,.15),'road',n=8,rings=3,label='Fender')
        # Orange-and-white lifebuoy on each side of the saloon.
        for i in range(20):
            a=i*math.tau/20; b=(i+1)*math.tau/20
            k.bar((side*.71,-1.09+.125*math.cos(a),.93+.125*math.sin(a)),
                  (side*.71,-1.09+.125*math.cos(b),.93+.125*math.sin(b)),.033,
                  'snow' if i%5<2 else 'red',8,label='LifeRing')
    return k.finish('boat',True)


def build_plane():
    k=Kit('Plane',reset_collection('HM_Plane'))
    # Wide-body shape built as elliptical cross sections along +Y.
    stations=[(-2.25,.035),(-2.10,.12),(-1.85,.20),(-1.55,.27),(-1.30,.29),
              (1.24,.29),(1.54,.266),(1.80,.215),(2.02,.14),(2.16,.075),(2.22,.018)]
    sides=28
    verts=[(r*math.cos(i*math.tau/sides),y,.64+r*math.sin(i*math.tau/sides)) for y,r in stations for i in range(sides)]
    faces=[tuple(reversed(range(sides))),tuple(range(len(verts)-sides,len(verts)))]
    # Outward winding on a tube whose axis is +Y.
    faces += [(j*sides+i,(j+1)*sides+i,(j+1)*sides+(i+1)%sides,j*sides+(i+1)%sides)
              for j in range(len(stations)-1) for i in range(sides)]
    fuselage=k.mesh(verts,faces,'snow','Fuselage')
    for face in fuselage.data.polygons:
        face.use_smooth=True
    for side in (-1,1):
        # Swept, tapered wing with a genuine thin thickness.
        top=[(side*.20,.25,.59),(side*2.01,-.76,.53),(side*2.04,-1.01,.53),(side*.24,-.53,.59)]
        bottom=[(x,y,z-.045) for x,y,z in top]
        # Let mesh validation recalculate normals consistently below.
        k.mesh(top+bottom,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'snow','SweptWing')
        k.cube((side*.78,-.14,.44),(.09,.36,.30),'rock','Pylon')
        k.cone((side*.78,-.10,.32),.19,.175,.72,'snow',n=12,axis=(0,1,0),label='Engine')
        k.cone((side*.78,.269,.32),.149,.149,.012,'road',n=12,axis=(0,1,0),label='EngineIntake')
        k.cone((side*.78,.280,.32),.052,.027,.035,'rock',n=8,axis=(0,1,0),label='FanSpinner')
        for y in [i*.16-1.28 for i in range(17)]:
            r=.292 if -1.3<y<1.26 else .25
            k.cube((side*r,y,.72),(.017,.065,.066),'glass','CabinWindow')
        k.mesh([(side*.14,-1.67,.76),(side*.81,-2.04,.77),(side*.83,-2.19,.77),(side*.15,-1.98,.73)],[(0,1,2,3)],'water','HorizontalTail')
    k.mesh([(-.025,-1.36,.82),(-.025,-1.92,1.53),(-.025,-2.15,1.52),(-.025,-2.09,.78),
            (.025,-1.36,.82),(.025,-1.92,1.53),(.025,-2.15,1.52),(.025,-2.09,.78)],
           [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'water','VerticalTail')
    k.ball((0,1.84,.75),(.17,.21,.10),'glass',n=8,rings=3,label='Cockpit')
    # Correct all closed component normals using bmesh, independent of side.
    import bmesh
    for obj in descendants(k.obj):
        if obj.type=='MESH':
            bm=bmesh.new(); bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(obj.data); bm.free()
    return k.finish('plane',True)


for _builder in (build_car,build_coach,build_helicopter,build_boat,build_plane):
    _builder()
print('[vehicles] Finished 5 assets; +Y forward, bottom-centre roots, 4.5-unit length.')
