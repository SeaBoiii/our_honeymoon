"""Silver touring SUV. Blender +Y faces the bonnet and +X is the axle axis."""
def build_car():
    k=Kit('Car',reset_collection('HM_Car'))
    paint,trim,glass,alloy,tyre='#858783','#282d2f','#435054','#b9c0bf','#252729'
    def curve(points,pairs,key):
        from bisect import bisect_right
        i=max(0,min(len(points)-2,bisect_right(points,key)-1))
        f=max(0,min(1,(key-points[i])/(points[i+1]-points[i])))
        return pairs[i]+(pairs[i+1]-pairs[i])*f
    def loft(rings,materials,bands,name,smooth=True):
        n=len(rings[0]); verts=[v for ring in rings for v in ring]
        faces=[tuple(reversed(range(n)))]
        for i in range(len(rings)-1):
            faces.extend((i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n) for j in range(n))
        faces.append(tuple(range(len(verts)-n,len(verts))))
        ob=k.mesh(verts,faces,materials[0],name)
        for m in materials[1:]:ob.data.materials.append(material(m))
        for face in list(ob.data.polygons)[1:-1]:
            face.material_index=bands[(face.index-1)%n];face.use_smooth=smooth
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
        return ob
    def tube(points,radius,col,name):
        # Swept circular tube, with shared rings for clean rails and light guides.
        vv=[Vector(p) for p in points];rings=[]
        for i,p in enumerate(vv):
            axis=(vv[min(len(vv)-1,i+1)]-vv[max(0,i-1)]).normalized()
            side=axis.cross(Vector((0,0,1)) if abs(axis.z)<.9 else Vector((0,1,0))).normalized()
            up=axis.cross(side)
            rings.append([p+radius*(side*math.cos(j*math.tau/8)+up*math.sin(j*math.tau/8)) for j in range(8)])
        return loft(rings,[col],[0]*8,name)
    axle=(-1.34,1.30); wheel_z=.395; arch=.449
    stations=[-2.22,-2.13,-1.91,-1.64,-.8,0,.78,1.42,1.91,2.10,2.22]
    widths=[.72,.874,.93,.96,.944,.941,.95,.96,.92,.88,.79]
    tops=[.99,1.10,1.16,1.19,1.16,1.14,1.13,1.10,1.055,1.03,.995]
    ys=set(stations)
    for cy in axle:
        for j in range(33):ys.add(cy+arch*math.cos(j*math.pi/32))
        ys.update((cy-arch-.022,cy+arch+.022))
    rings=[]
    for y in sorted(ys):
        w=curve(stations,widths,y);top=curve(stations,tops,y)
        dy=min(abs(y-a) for a in axle)
        base=wheel_z+math.sqrt(max(0,arch**2-dy**2)) if dy<=arch+1e-9 else .32
        section=[(0,.30),(.76,.30),(.81,base),(.98,base+.008),(1.002,base+.06),
                 (.985,base+(top-base)*.43),(1,top-.09),(.962,top-.035),(.86,top),
                 (.58,top+.018),(0,top+.026)]
        full=section+[(-x,z) for x,z in section[-2:0:-1]]
        rings.append([(x*w,y,z) for x,z in full])
    loft(rings,[paint,trim],[1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1],'WheelArchedBody')
    glazing=[(-2.045,.798,1.095,.75,1.23),(-1.91,.846,1.12,.748,1.52),
             (-1.65,.867,1.14,.733,1.64),(-1.37,.875,1.14,.737,1.69),
             (-.5,.872,1.134,.742,1.705),(.22,.866,1.124,.731,1.69),
             (.46,.865,1.12,.725,1.64),(.80,.862,1.115,.758,1.425),(1.15,.851,1.10,.819,1.155)]
    rings=[]
    for y,w,bottom,upper,top in glazing:
        half=[(0,bottom),(w,bottom),(w*.999,bottom+.027),(upper+.024,top-.054),(upper,top-.019),(.91*upper,top),(.66*upper,top+.016),(0,top+.020)]
        full=half+[(-x,z) for x,z in half[-2:0:-1]]
        rings.append([(x,y,z) for x,z in full])
    cabin=loft(rings,[glass,trim,paint],[1,1,0,1,2,2,2,2,2,2,1,0,1,1],'WraparoundGreenhouse')
    # Windshield and rear hatch span the upper face of their sloping end stations.
    for f in list(cabin.data.polygons)[1:-1]:
        j,band=divmod(f.index-1,14)
        if j in (0,6,7) and 4<=band<=9:f.material_index=0
    for side in (-1,1):
        def sidepath(coords,r,col,name):tube([(side*x,y,z) for x,y,z in coords],r,col,name)
        sidepath([(.839,-1.96,1.16),(.869,-1.65,1.16),(.883,-.4,1.15),(.862,1.12,1.125)],.013,alloy,'WindowSill')
        for y,offset,thick,col in [(-1.66,.16,.052,paint),(-.85,-.12,.047,trim),(.04,-.04,.042,trim),(.96,-.50,.034,paint)]:
            top=1.63 if y>.8 else 1.65
            sidepath([(.867,y,1.145),(.751,y+offset,top)],thick,col,'Pillar')
        for y in (-.82,.27,.89):
            sidepath([(.934,y,.48),(.943,y+.015,.85),(.924,y+.035,1.075)],.006,trim,'DoorGap')
        for y in (-.91,.15):
            k.ball((side*.943,y,.992),(.026,.113,.027),alloy,n=18,rings=4,label='DoorHandle')
        sidepath([(.944,-.84,.377),(.95,.05,.369),(.946,.81,.381)],.023,alloy,'RockerTrim')
        for y in (-1.39,.36):k.cube((side*.65,y,1.72),(.057,.13,.065),trim,'RailFoot')
        sidepath([(.65,-1.60,1.68),(.65,-1.39,1.76),(.65,-.53,1.78),(.65,.36,1.76),(.65,.58,1.66)],.028,alloy,'RaisedRoofRail')
        sidepath([(.846,.72,1.23),(.988,.71,1.28)],.033,trim,'MirrorArm')
        k.ball((side*1.005,.70,1.31),(.112,.12,.075),paint,n=22,rings=8,label='MirrorCap')
        k.ball((side*1.008,.613,1.31),(.092,.024,.055),glass,n=18,rings=6,label='MirrorGlass')
        for cy in axle:
            path=[(.951,cy+arch*math.cos(t*math.pi/40),wheel_z+arch*math.sin(t*math.pi/40)) for t in range(41)]
            sidepath(path,.026,trim,'WheelArchLip')
    for cy in axle:
        for side in (-1,1):
            wheel=root('Wheel_'+('L' if side<0 else 'R')+('F' if cy>0 else 'R'),k.col);wheel.parent=k.obj
            wheel.location=(side*.878,cy,wheel_z)
            profile=[(-.118,.258),(-.115,.333),(-.101,.369),(-.075,.39),(-.04,.394),(.04,.394),(.075,.39),(.102,.369),(.118,.335),(.12,.269),(.106,.254),(-.118,.258)]
            count=64
            vv=[(side*x,rad*math.cos(i*math.tau/count),rad*math.sin(i*math.tau/count)) for x,rad in profile for i in range(count)]
            ff=[(j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i) for j in range(len(profile)-1) for i in range(count)]
            rubber=k.mesh(vv,ff,tyre,'TyreProfile',parent=wheel)
            for p in rubber.data.polygons:p.use_smooth=True
            for x,rad,depth,col,name in [(.071,.267,.046,trim,'RimBarrel'),(.103,.193,.012,'#777d7d','Disc'),(.123,.069,.018,alloy,'Hub')]:
                k.cone((side*x,0,0),rad,rad,depth,col,n=44,axis=(1,0,0),parent=wheel,label=name)
            k.cube((side*.11,-.127,.064),(.019,.052,.125),'#6b726d','BrakeCaliper',parent=wheel)
            for j in range(7):
                a=j*math.tau/7
                polar=[(.058,a-.19),(.058,a+.19),(.17,a+.21),(.255,a+.32),(.262,a+.145),(.176,a+.048),(.255,a-.012),(.255,a-.15),(.16,a-.085)]
                vs=[(side*x,rad*math.cos(b),rad*math.sin(b)) for x in (.11,.132) for rad,b in polar];n=len(polar)
                fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
                k.mesh(vs,fs,alloy,'SplitSpoke',parent=wheel)
            for j in range(5):
                a=j*math.tau/5
                k.cone((side*.138,.042*math.cos(a),.042*math.sin(a)),.012,.012,.009,trim,n=6,axis=(1,0,0),parent=wheel,label='Lug')
    # Black mesh grille, narrow brow lamps and the vertical outboard light signatures.
    def fascia(points,m,y,name,thickness=.025):
        # Wrap the front assemblies around both fenders; bevel the face by a shallow inset.
        center=sum(x for x,z in points)/len(points),sum(z for x,z in points)/len(points)
        def forward(x):return y-.12*max(0,abs(x)-.56)**1.3
        rings=[[(x,forward(x)-thickness,z) for x,z in points],
               [(x,forward(x),z) for x,z in points],
               [(x*.976+center[0]*.024,forward(x)+.004,z*.96+center[1]*.04) for x,z in points]]
        return loft(rings,[m],[0]*len(points),name,False)
    fascia([(-.73,.966),(-.62,1.005),(.62,1.005),(.73,.966),(.66,.755),(.48,.716),(-.48,.716),(-.66,.755)],trim,2.241,'SculptedGrille')
    for j in range(4):
        for i in range(15):
            x=-.61+i*.085+(j%2)*.025
            if abs(x)>.63:continue
            z=.752+j*.057;y=2.256-.12*max(0,abs(x)-.56)**1.3
            tube([(x-.038,y,z+.008),(x-.023,y+.003,z+.027),(x+.022,y+.004,z+.027),(x+.038,y,z+.008)],.0068,'#696d68','GrilleCell')
    fascia([(-.82,.577),(-.65,.642),(.65,.642),(.82,.577),(.71,.36),(.48,.335),(-.48,.335),(-.71,.36)],trim,2.249,'LowerAirIntake')
    for z in (.427,.477,.528,.576):
        fascia([(-.51,z),(.51,z),(.49,z+.013),(-.49,z+.013)],'#4f5452',2.262,'LowerIntakeVane',.010)
    fascia([(-.79,.385),(-.53,.39),(-.46,.425),(.46,.425),(.53,.39),(.79,.385),(.69,.335),(-.69,.335)],alloy,2.264,'FormedSkidPlate')
    for side in (-1,1):
        def front(shape,mat,y,name):return fascia([(side*x,z) for x,z in shape],mat,y,name)
        front([(.654,.764),(.72,.982),(.844,.976),(.888,.913),(.843,.707),(.769,.677)],glass,2.272,'ProjectorHousing')
        front([(.636,.989),(.754,1.026),(.853,1.025),(.889,.990),(.855,.967),(.75,.994)],'#e8f1ed',2.281,'BladeHeadlamp')
        front([(.859,.992),(.885,.986),(.856,.766),(.828,.728),(.833,.789)],'#ecf1e9',2.286,'VerticalRunningLamp')
        for z in (.804,.873,.934):
            front([(.73,z),(.756,z+.022),(.801,z+.019),(.806,z-.008),(.747,z-.013)],'#a9bdbd',2.282,'ProjectorLens')
        front([(.54,.605),(.83,.677),(.87,.634),(.77,.594),(.69,.48),(.61,.466)],paint,2.261,'BumperCheek')
        front([(.65,.535),(.75,.573),(.823,.563),(.79,.492),(.69,.476)],'#303637',2.27,'FogRecess')
        for x in (.70,.755):front([(x,.505),(x+.025,.51),(x+.024,.537),(x,.533)],'#c7d5d1',2.28,'FogLamp')
        sidepath=lambda pts,rad,col,label:tube([(side*x,y,z) for x,y,z in pts],rad,col,label)
        sidepath([(.646,1.09,1.145),(.599,1.38,1.129),(.578,1.81,1.094),(.554,2.08,1.05)],.008,paint,'PressedBonnetRidge')
        sidepath([(.943,-1.79,1.048),(.963,-1.46,1.034),(.949,-.50,1.01),(.95,.47,1.006),(.96,1.28,1.023)],.011,paint,'ShoulderCrease')
        for sy in (-.64,.30):
            k.ball((side*.402,sy,1.251),(.185,.085,.179),'#444a49',n=18,rings=6,label='Seatback')
            k.ball((side*.402,sy-.018,1.456),(.115,.058,.079),'#4d5150',n=16,rings=6,label='Headrest')
    for sign in (-1,1):
        tube([(sign*.18,1.08,1.171),(sign*.41,1.04,1.205),(sign*.69,.994,1.226)],.009,trim,'WiperBlade')
    k.cube((0,-2.174,.47),(1.66,.10,.18),trim,'RearValance')
    k.cube((0,-1.88,1.574),(1.49,.19,.064),paint,'RoofSpoiler')
    for s in (-1,1):
        tube([(s*.36,-2.19,1.008),(s*.73,-2.18,1.009),(s*.855,-2.1,.96),(s*.86,-2.07,.777)],.025,'#962e23','RearLamp')
    return k.finish('car',True)
