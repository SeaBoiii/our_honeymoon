"""Five original, generic-livery low-poly vehicles. All noses face +Y."""
from pathlib import Path
PROJECT_ROOT = Path(globals().get('PROJECT_ROOT', 'C:/Users/seabo/Documents/GitHub/our_honeymoon'))
exec(compile((PROJECT_ROOT / 'map3d/blender/scripts/common.py').read_text(encoding='utf-8'), 'common.py', 'exec'), globals())


def wheels(k, axles, width, radius, z=None):
    for y in axles:
        for side in (-1,1):
            x=side*width/2
            k.cone((x,y,z or radius),radius,radius,.18,'road',n=12,axis=(1,0,0),label='Tyre')
            k.cone((x+side*.095,y,z or radius),radius*.48,radius*.48,.025,'rock',n=8,axis=(1,0,0),label='Hub')


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
    k.cube((0,0,.63),(1.86,3.65,.64),'red','SUVBody')
    k.cube((0,-.23,1.15),(1.65,2.16,.67),'red','Cabin')
    k.cube((0,.875,1.20),(1.48,.035,.42),'glass','FrontWindscreen')
    k.cube((0,-1.325,1.20),(1.48,.035,.39),'glass','RearWindow')
    for x in (-.837,.837):
        for y in (-.82,.27):
            k.cube((x,y,1.20),(.03,.85,.40),'glass','SideWindow')
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
    k.ball((0,.50,1.05),(.64,1.02,.62),'snow',label='CabinShell')
    k.ball((0,1.11,1.16),(.55,.48,.44),'glass',label='Cockpit')
    k.cube((0,.2,.86),(1.26,1.02,.27),'red','LowerLivery')
    for side in (-1,1):
        k.cube((side*.61,.25,1.20),(.04,.56,.35),'glass','DoorWindow')
        k.bar((side*.40,.78,.65),(side*.63,.64,.23),.045,'rock')
        k.bar((side*.38,-.31,.65),(side*.63,-.40,.23),.045,'rock')
        k.bar((side*.65,-.79,.16),(side*.65,1.18,.16),.055,'road',label='Skid')
        k.bar((side*.65,1.18,.16),(side*.65,1.39,.26),.055,'road')
    k.bar((0,-.29,1.07),(0,-2.55,1.29),.13,'snow',label='TailBoom')
    k.mesh([(-.04,-2.68,1.16),(.04,-2.68,1.16),(-.04,-2.46,2.0),(.04,-2.46,2.0),
            (-.04,-2.04,1.27),(.04,-2.04,1.27)],
           [(0,4,2),(1,3,5),(0,1,5,4),(2,4,5,3),(0,2,3,1)],'red','TailFin')
    k.cube((0,-1.95,1.26),(1.01,.28,.07),'red','Tailplane')
    k.cone((0,.20,1.79),.055,.055,.42,'road',label='Mast')
    rotor=root('Rotor',k.col); rotor.parent=k.obj; rotor.location=(0,.20,2.02)
    # Main rotor lies in local XY, rotating about local Z -> three.js Y.
    for angle in (0,math.pi/2):
        blade=k.cube((0,0,0),(.16,4.2,.035),'road','RotorBlade',parent=rotor)
        blade.rotation_euler.z=angle
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
    outline=[(-.70,-1.90),(.70,-1.90),(.81,.95),(.55,1.62),(0,2.12),(-.55,1.62),(-.81,.95)]
    verts=[(x*.79,y*.93,.06) for x,y in outline]+[(x,y,.59) for x,y in outline]
    n=len(outline)
    k.mesh(verts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+
           [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],'fiord','Hull')
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
    return k.finish('boat',True)


def build_plane():
    k=Kit('Plane',reset_collection('HM_Plane'))
    # Wide-body shape built as elliptical cross sections along +Y.
    stations=[(-2.25,.055),(-1.85,.20),(-1.35,.29),(1.25,.29),(1.85,.21),(2.22,.035)]
    verts=[(r*math.cos(i*math.tau/12),y,.64+r*math.sin(i*math.tau/12)) for y,r in stations for i in range(12)]
    faces=[tuple(reversed(range(12))),tuple(range(60,72))]
    # Outward winding on a tube whose axis is +Y.
    faces += [(j*12+i,(j+1)*12+i,(j+1)*12+(i+1)%12,j*12+(i+1)%12) for j in range(5) for i in range(12)]
    k.mesh(verts,faces,'snow','Fuselage')
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
