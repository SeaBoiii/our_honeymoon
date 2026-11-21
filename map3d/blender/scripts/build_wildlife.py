"""Detailed scatter silhouettes for close road shots. All meshes are deterministic."""
import random


def alpine_pine(k):
    rng=random.Random(447)
    k.cone((0,0,.46),.044,.011,.92,'#674e38',n=14,label='Bark')
    for tier in range(9):
        height=.20+tier*.086
        radius=.29*(1-tier/11)
        count=12-tier//2
        for j in range(count):
            a=math.tau*j/count+tier*2.31+rng.uniform(-.08,.08)
            length=radius*rng.uniform(.83,1.13)
            verts=[]
            for t,wide,up in ((0,.07,.06),(.30,.24,.065),(.62,.22,.015),(.84,.17,-.018),(1,.01,-.013)):
                for i in range(9):
                    b=math.tau*i/9
                    lateral=wide*length*math.cos(b)
                    along=t*length
                    verts.append((along*math.cos(a)-lateral*math.sin(a),along*math.sin(a)+lateral*math.cos(a),
                                  height+up*(1-tier*.065)+length*wide*.7*math.sin(b)))
            faces=[tuple(range(8,-1,-1)),tuple(range(36,45))]
            faces.extend((h*9+i,h*9+(i+1)%9,(h+1)*9+(i+1)%9,(h+1)*9+i) for h in range(4) for i in range(9))
            k.mesh(verts,faces,('#335d50','#476f58','#587b60','#658866')[(j+2*tier)%4],'NeedleSpray')
    k.cone((0,0,.958),.047,0,.14,'#547c62',n=13,label='Leader')


def beech(k):
    rng=random.Random(891)
    k.bar((0,0,0),(.025,0,.40),.038,'#695b49',n=14,label='Trunk')
    k.bar((.025,0,.37),(-.015,.026,.65),.025,'#756650',n=12,label='Leader')
    for j in range(14):
        a=j*2.39996;h=.32+j*.021;rad=.235-.005*j
        fork=(rad*.56*math.cos(a),rad*.56*math.sin(a),h+.10)
        k.bar((.018,0,h),fork,.018,'#695b49',n=9,label='Branch')
        for side in (-1,1):
            b=a+side*.39;end=(rad*math.cos(b),rad*math.sin(b),h+.18+rng.uniform(-.017,.055))
            k.bar(fork,end,.011,'#766a4e',n=7,label='Fork')
            scale=rng.uniform(.095,.138)
            ob=k.ball(end,(scale*1.05,scale,scale*.80),('#55785b','#64865f','#466950','#779266')[j%4],n=11,rings=5,label='Foliage')
            for v in ob.data.vertices:
                x,y,z=v.co
                v.co*=1+.08*math.sin(57*x+34*y)*math.cos(63*z-19*y)
    k.ball((0,.015,.795),(.138,.126,.11),'#728f64',n=14,rings=6,label='Crown')


def merino(k):
    fleece='#e5dfcc';skin='#b4a78f';hoof='#4d4840'
    # The fleece surface has small scalloped locks. Their amplitude tapers at the poles.
    n,m=100,42
    verts=[(0,0,.325)]
    for j in range(1,m):
        lat=-math.pi/2+math.pi*j/m
        for i in range(n):
            a=math.tau*i/n
            locks=math.cos(16*a+1.35*math.sin(9*lat))*math.cos(17*lat+1.25*math.sin(5*a))
            puff=1+.054*locks*math.cos(lat)
            verts.append((.252*math.cos(lat)*math.cos(a)*puff,
                          .39*math.cos(lat)*math.sin(a)*puff,
                          .55+.229*math.sin(lat)*puff))
    verts.append((0,0,.779))
    faces=[(0,1+(i+1)%n,1+i) for i in range(n)]
    for j in range(m-2):
        for i in range(n):
            a=1+j*n+i;b=1+j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
    faces.extend((1+(m-2)*n+i,1+(m-2)*n+(i+1)%n,len(verts)-1) for i in range(n))
    wool=k.mesh(verts,faces,fleece,'CrimpedFleece')
    for p in wool.data.polygons:p.use_smooth=True
    for x in (-.14,.14):
        for y in (-.211,.215):
            toe=y+(.018 if x*y>0 else -.014)
            k.ball((x,y,.326),(.068,.078,.137),fleece,n=15,rings=7,label='UpperLeg')
            k.bar((x,y,.29),(x*.99,toe,.085),.028,skin,n=12,label='Cannon')
            k.ball((x,toe+.012,.055),(.044,.066,.051),hoof,n=13,rings=5,label='ClovenHoof')
    k.ball((0,.305,.595),(.142,.15,.18),fleece,n=18,rings=8,label='Ruff')
    head=k.ball((0,.426,.64),(.111,.17,.124),'#cabfa9',n=23,rings=10,label='Head')
    head.rotation_euler.x=-.33
    k.ball((0,.556,.594),(.080,.083,.061),'#93877b',n=18,rings=7,label='Muzzle')
    k.ball((0,.393,.726),(.118,.116,.065),fleece,n=16,rings=6,label='Forelock')
    for s in (-1,1):
        ear=k.ball((s*.132,.388,.688),(.089,.046,.032),'#b5a88f',n=17,rings=6,label='Ear')
        ear.rotation_euler.y=s*.19
        k.ball((s*.097,.473,.673),(.016,.025,.018),'#302f29',n=12,rings=5,label='Eye')
        k.ball((s*.034,.624,.603),(.015,.010,.008),hoof,n=9,rings=4,label='Nostril')
    k.ball((0,-.366,.492),(.058,.081,.102),fleece,n=15,rings=6,label='Tail')
