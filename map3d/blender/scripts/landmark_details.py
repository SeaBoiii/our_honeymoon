"""Architectural and geological details for the itinerary miniatures (Blender units)."""
import math
import random


def arch_trim(k, center, width, spring, rise, outward, stone):
    """Wedge-shaped voussoirs with a real interval between individual stones."""
    x,y,z=center
    tangent=Vector((-outward[1],outward[0],0)); normal=Vector((*outward,0))
    origin=Vector((x,y,z+spring))
    for i in range(11):
        a=math.pi*i/11+.018;b=math.pi*(i+1)/11-.018
        points=[]
        for depth in (0,.012):
            for angle,extra in [(a,0),(b,0),(b,.013),(a,.013)]:
                point=origin+tangent*math.cos(angle)*(width+extra)+normal*depth
                point.z+=math.sin(angle)*(rise+extra)
                points.append(tuple(point))
        k.mesh(points,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],stone,'ArchStone')


def chapel_details(k):
    rng=random.Random(422)
    for side in (-1,1):
        for y in (-.28,-.03,.20):
            arch_trim(k,(side*.258,y,0),.047,.427,.047,(side,0),'#d0baa0')
            k.cube((side*.262,y,.24),(.034,.123,.021),'#bcb3a3','StoneSill')
        for i in range(8):
            z=.526+i*.045;length=.232 if i%2 else .212
            for y in (.208,.427):
                k.cube((side*.085,y,z),(.056,length*.16,.036),'#ad9c87','TowerQuoin')
            k.cube((side*.122,.32,z),(.014,length,.011),'#9a9081','TowerCourse')
        for a,b in [((side*.276,-.459,.535),(side*.276,.321,.535)),
                    ((side*.269,-.40,.527),(side*.269,-.40,.108))]:
            k.bar(a,b,.011,'#676c68',10,'RainwaterPipe')
    for row in range(10):
        for i in range(6):
            x=(i-2.5)*.075+(.012 if row%2 else -.003);z=.088+row*.044
            if abs(x)>.223:continue
            k.cube((x,-.423,z),(.067,.017,rng.uniform(.027,.039)),rng.choice(('#a29988','#afa591','#9d9383')),'GableSchist')
    for y in (.453,-.423):
        arch_trim(k,(0,y,0),.068,.392,.048,(0,1 if y>0 else -1),'#b4a590')
    for x in (-.049,-.025,0,.025,.049):
        k.cube((x,.462,.278),(.017,.010,.246),'#826146','OakDoorPlank')
    for z in (.216,.333):k.cube((0,.469,z),(.118,.009,.012),'#484f49','StrapHinge')
    k.ball((.037,.476,.263),(.009,.008,.009),'#a89461',n=10,rings=4,label='Latch')


def dome_details(k):
    for i in range(48):
        a=i*math.tau/48;x,y=math.cos(a),math.sin(a)
        if i%2==0:k.bar((.312*x,.312*y,.078),(.312*x,.312*y,.402),.005,'#a8a79a',6,'DrumJoint')
        k.cone((.332*x,.332*y,.419),.005,.005,.012,'#a6a395',n=6,label='RingBolt')
    for x in (-.051,.051):
        last=None
        for j in range(19):
            a=j*math.pi/36;v=(x,-.339*math.cos(a),.419+.329*math.sin(a))
            if last:k.bar(last,v,.009,'#babbb1',8,'ShutterGuide')
            last=v
    for i in range(15):
        a=math.pi*.13+i*math.pi*.083
        if math.sin(a)<-.60:continue
        x,y=.418*math.cos(a),.418*math.sin(a)
        k.bar((x,y,.07),(x,y,.16),.006,'#787f7a',7,'WalkwayPost')
        b=a+math.pi*.083
        k.bar((x,y,.154),(.418*math.cos(b),.418*math.sin(b),.154),.007,'#a6aaa0',7,'WalkwayRail')
    for j in range(3):k.cube((0,-.366-j*.033,.064-j*.015),(.168,.045,.027),'#a5a49a','AccessStep')
    for x in (-.10,.10):
        k.bar((x,-.46,.036),(x,-.46,.126),.006,'#777d7a',8,'RailPost')
        k.bar((x,-.46,.126),(x,-.312,.202),.006,'#777d7a',8,'Handrail')


def sculpt_willow(k):
    rng=random.Random(724)
    k.cone((0,0,.021),.49,.49,.042,'#588e8e',n=72,label='LakePlinth')
    for j in range(22):
        a=rng.random()*math.tau;r=rng.uniform(.09,.34)
        k.ball((r*math.cos(a),r*math.sin(a),.041),(.044,.031,.024),'#8d9281',n=10,rings=3,label='Shingle')
    trunk=[(-.07,0,.035),(-.055,.004,.12),(-.09,.008,.23),(-.065,.018,.32),(.002,.025,.405),(.074,.05,.496)]
    for j,(a,b) in enumerate(zip(trunk,trunk[1:])):k.bar(a,b,.071-j*.008,'#65594b',11,'WeatheredTrunk')
    verts=[];faces=[];colors=[]
    for j in range(9):
        a=j*2.40;origin=Vector(trunk[3+j%3]);tip=origin+Vector((math.cos(a)*.25,math.sin(a)*.17,.21+rng.random()*.12))
        joint=origin.lerp(tip,.52);joint.z+=.039
        k.bar(origin,joint,.027,'#65594b',9,'WillowBough');k.bar(joint,tip,.019,'#70614e',8,'WillowBough')
        for q in range(7):
            az=a+rng.uniform(-1.24,1.24)
            start=joint.lerp(tip,rng.uniform(.35,1))
            high=start+Vector((math.cos(az)*.10,math.sin(az)*.085,.06))
            end=high+Vector((math.cos(az)*.075,math.sin(az)*.06,-rng.uniform(.09,.20)))
            k.bar(start,high,.009,'#756a51',6,'WillowTwig');k.bar(high,end,.004,'#857e58',5,'HangingTwig')
            for p in range(15):
                t=rng.random();c=high.lerp(end,t)+Vector((rng.uniform(-.028,.028),rng.uniform(-.022,.022),rng.uniform(-.015,.015)))
                length=rng.uniform(.025,.060);d=Vector((rng.uniform(-.009,.009),rng.uniform(-.009,.009),-length));w=Vector((-.010*math.sin(az),.010*math.cos(az),0))
                idx=len(verts);verts.extend([c,c+d*.45+w,c+d,c+d*.45-w,c+d*.48+Vector((.003,.003,.003))])
                faces.extend((idx+i,idx+(i+1)%4,idx+4) for i in range(4));colors.extend([rng.randrange(4)]*4)
    leaves=k.mesh(verts,faces,'#7d8e59','LanceolateWillowLeaves')
    for col in ('#91a574','#a9b181','#718257'):leaves.data.materials.append(material(col))
    for f,c in zip(leaves.data.polygons,colors):f.material_index=c
    for j in range(3):
        last=None
        for i in range(18):
            a=-.6+i*.11;r=.17+j*.074
            v=(r*math.cos(a)-.056,r*math.sin(a),.044)
            if last:k.bar(last,v,.0025,'#9bb8aa',5,'WaterRipple')
            last=v


def onsen_details(k):
    for i in range(40):
        a=i*math.tau/40;x,y=math.cos(a),math.sin(a)
        stave=k.cube((.331*x,-.03+.331*y,.473),(.049,.024,.293),('#aa764c','#b58458','#9f6e47')[i%3],'CedarStave')
        stave.rotation_euler.z=a-math.pi*.5
        rim=k.cube((.313*x,-.03+.313*y,.645),(.047,.061,.021),'#ba956a','TubRim');rim.rotation_euler.z=a-math.pi*.5
    for x in (-.27,-.14,0,.14,.27):k.bar((x,.35,.34),(x,.35,.726),.011,'#a9855e',8,'Baluster')
    for j in range(6):
        a=.7+j*.35
        k.ball((.211*math.cos(a),-.03+.211*math.sin(a),.534),(.010,.010,.003),'#c1ddd3',n=10,rings=3,label='SpringBubble')
    for j in range(3):
        y=-.371-j*.027;k.cube((.24,y,.386-j*.026),(.19,.055,.031),'#ae855c','BathStep')


def mosque_details(k):
    for side in (-1,1):
        for y in (-.151,0,.151):
            x=-.06+side*.292
            k.cube((x,y,.278),(.013,.072,.133),'glass','Clerestory')
            k.ball((x,y,.342),(.007,.038,.043),'glass',n=16,rings=5,label='ArchedGlazing')
            arch_trim(k,(x,y,0),.04,.34,.045,(side,0),'#d7c7a5')
    for x in (-.23,-.06,.11):
        arch_trim(k,(x,-.272,0),.048,.347,.051,(0,-1),'#c9b99a')
        for dx in (-.018,0,.018):k.bar((x+dx,-.279,.145),(x+dx,-.279,.366),.003,'#bda57b',6,'DoorGrille')
    for i in range(28):
        a=i*math.tau/28;c,s=math.cos(a),math.sin(a)
        k.bar((.34+.085*c,.15+.085*s,.749),(.34+.085*c,.15+.085*s,.827),.003,'#dac9a7',6,'BalconyBaluster')
    annulus(k,(.34,.15,.826),.09,.082,.009,'#d4bf97',n=48)
    for z in (.185,.414,.615):annulus(k,(.34,.15,z),.077,.061,.012,'#cbb99b',n=32)
    annulus(k,(-.06,0,.479),.271,.248,.017,'#b7a582',n=56)
    for j in range(15):
        x=-.407+(j%5)*.139;y=-.324+(j//5)*.024
        k.cube((x,y,.055),(.128,.019,.009),'#baab91','CourtyardPaver')


def city_details(k):
    for ix,x in enumerate((-.34,-.12,.12,.34)):
        for iy,y in enumerate((-.33,0,.33)):
            h=(.21,.36,.27,.45,.24,.32,.41,.23,.34,.26,.39,.29)[ix*3+iy]
            for z in range(1,int(h/.08)+1):
                for dy in (-.071,0,.071):
                    k.cube((x+.09,y+dy,.065+z*.062),(.009,.041,.030),'#627a82','SideWindow')
            box=k.cube((x,y+.048,.090+h),(.065,.085,.044),'#a09f90','RoofPlant')
            for q in range(4):k.cube((x-.023+q*.015,y+.048,.115+h),(.005,.063,.006),'#65706b','PlantLouvre')
            k.cube((x,y-.129,.132),(.149,.050,.018),('#8c4d3f','#647c71','#bd9869')[(ix+iy)%3],'ShopAwning')
            k.cube((x-.044,y-.124,.087),(.041,.008,.067),'#415865','StreetEntrance')
    for y in (-.17,.17):
        for x in (-.03,-.012,.006,.024,.042):
            k.cube((x,y,.063),(.010,.062,.006),'cream','Crosswalk')
    for x,y in [(-.46,-.18),(.46,.16),(-.015,.46),(.018,-.45)]:
        k.bar((x,y,.053),(x,y,.145),.004,'#3e514e',8,'StreetLamp')
        k.ball((x,y,.15),(.012,.012,.014),'cream',n=12,rings=4,label='LampGlobe')


def sculpt_grotto(k):
    """Open section through a damp limestone passage with a broad, shadowed recess."""
    rng=random.Random(821)
    n,m=49,19
    inner=[];outer=[]
    for j in range(m):
        y=-.31+j*.036
        for i in range(n):
            a=i*math.pi/(n-1);cs,sn=math.cos(a),math.sin(a)
            ripple=.020*math.sin(7*a+j*.33)+.011*math.cos(17*a-j*.4)
            inner.append(((.39+ripple-.06*j/m)*cs+.026*math.sin(j*.24),y,.053+(.43+ripple-.05*j/m)*sn**.83))
            outer.append(((.55+ripple)*cs,y,.043+(.59+.038*math.sin(a*3+j*.2)+ripple)*sn**.74))
    stone=['#6e746f','#76776c','#858576','#8c8876','#646f6e','#9a9784','#515e5f']
    def skin(verts,faces,labels,name):
        mesh=k.mesh(verts,faces,stone[0],name)
        for color in stone[1:]:mesh.data.materials.append(material(color))
        for face,label in zip(mesh.data.polygons,labels):face.material_index=label
    def shell(layer,outside):
        faces=[];labels=[]
        for j in range(m-1):
            for i in range(n-1):
                a=j*n+i;faces.extend([(a,a+1,a+n+1),(a,a+n+1,a+n)])
                band=(i//5+j//3)%5
                labels.extend(([band,band] if outside else [4 if band!=1 else 0,4 if band!=1 else 6]))
        skin(layer,faces,labels,'WeatheredKarst' if outside else 'CavernVault')
    shell(outer,True);shell(inner,False)
    front=[];faces=[];colors=[]
    for j in range(7):
        v=j/6
        for i in range(n):
            p=Vector(inner[i]).lerp(Vector(outer[i]),v)
            p.y-=.009*math.sin(v*math.pi)+.012*math.sin(i*.57+v*2)*math.sin(v*math.pi)
            front.append(p)
    for j in range(6):
        for i in range(n-1):
            a=j*n+i;faces.extend([(a,a+1,a+n+1),(a,a+n+1,a+n)])
            colors.extend([((j//2+i//10)%4)+1]*2)
    skin(front,faces,colors,'LimestoneStrata')
    end=inner[(m-1)*n:];k.mesh(end+[(0,end[0][1],.048)],[(i,i+1,n) for i in range(n-1)],'#172e32','PassageDepth')
    k.cone((0,.015,.020),.57,.57,.040,'#386b6f',n=80,label='CavernPool')
    for i in range(87):
        col=rng.randint(7,41);row=rng.randint(0,16);x,y,z=inner[row*n+col]
        h=rng.uniform(.023,.10);rad=rng.uniform(.005,.016)
        k.cone((x,y,z-h*.43),.0013,rad,h,rng.choice(stone),n=9,label='Stalactite')
        if i%2==0:
            k.bar((x,y-.002,z-h*.67),(x+.001,y-.001,z-h-.012),.0011,'#738c85',5,'SilkThread')
            k.ball((x+.001,y-.002,z-h-.012),(.0025,.0025,.004),material('glow',emission=2.1),n=8,rings=3,label='Glowworm')
    for i in range(62):
        side=(-1,1)[i%2];y=rng.uniform(-.35,.37);x=side*rng.uniform(.34,.51);size=rng.uniform(.016,.063)
        rock=k.ball((x,y,.043+size*.20),(size,size*.54,size*.40),rng.choice(stone),n=7,rings=3,label='ShingleBank')
        rock.rotation_euler.z=rng.random()*math.tau
    rings=[(-.35,.002),(-.31,.047),(-.245,.071),(-.087,.074),(-.010,.052)]
    verts=[];faces=[]
    for y,width in rings:
        verts.extend([(-width*.52,y,.048),(-width,y,.093),(-width*.82,y,.098),(-width*.50,y,.061),
                      (width*.50,y,.061),(width*.82,y,.098),(width,y,.093),(width*.52,y,.048)])
    for j in range(len(rings)-1):
        for i in range(8):faces.append((j*8+i,(j+1)*8+i,(j+1)*8+(i+1)%8,j*8+(i+1)%8))
    hull=k.mesh(verts,faces,'#987653','CaveTender')
    for y in (-.252,-.18,-.10):k.cube((0,y,.087),(.115,.023,.009),'#b59569','BoatThwart')
    for i in range(7):
        x=.22*math.sin(i*2.8);y=-.35-i*.022;span=.035+i*.008
        k.bar((x-span,y,.042),(x+span,y+.003,.042),.0015,'#759794',5,'PoolRipple')


def lift_details(k):
    for i in range(3):
        x=-.44+i*.44;y=-.27+i*.27;z=.09+i*.09
        for side in (-1,1):
            k.bar((x+side*.026,y-.026,z+.017),(x+side*.026,y-.026,z+.49),.005,'#67716e',7,'LadderStile')
        for j in range(11):k.bar((x-.026,y-.028,z+.044+j*.041),(x+.026,y-.028,z+.044+j*.041),.004,'#a6aaa0',7,'LadderRung')
        for side in (-1,1):
            for j in (-1,0,1):
                k.cone((x+side*.10,y+j*.027,z+.539),.021,.021,.013,'#454e50',n=20,axis=(1,0,0),label='SheaveWheel')
            k.bar((x,y,z+.40),(x+side*.108,y,z+.519),.010,'rock',8,'TowerBrace')
    for x,y in ((-.35,.02),(.23,.04)):
        z=.06+(y+.38)*.342
        k.bar((x,y,z),(x,y,z+.123),.005,'#bc704d',7,'PisteMarker')
        k.ball((x,y,z+.126),(.016,.016,.017),'#cb8c58',n=10,rings=3,label='MarkerCap')


def glacier_details(k):
    rng=random.Random(375)
    for i in range(70):
        y=rng.uniform(-.50,.53);side=-1 if i%2 else 1
        x=.055*math.sin(y*4)+side*rng.uniform(.348,.46)
        size=rng.uniform(.022,.071)
        k.ball((x,y,size*.39),(size,size*.76,size*.59),rng.choice(('#728a88','#a4b9b0','#a5cbd0','#d1e2dd')),n=9,rings=4,label='LateralMoraine')
    for i in range(34):
        row=rng.randint(0,9);col=rng.randint(0,6);y=(row-4.5)*.112
        x=(col-3)*.111*(.79+.21*math.cos(y*2.7))+.055*math.sin(y*4)
        h=.14+row*.03+.09*math.sin(col*1.7+row*.7)
        k.cone((x+.022,y+.016,h+.027),.019,.004,.083,'#cfedf0',n=7,axis=(.21,.13,1),label='IceFin')


LANDMARK_DETAILS={'church_stone':chapel_details,'observatory':dome_details,'hot_tub':onsen_details,
                  'mosque':mosque_details,'city':city_details,
                  'ski_lift':lift_details,'glacier_ice':glacier_details}
