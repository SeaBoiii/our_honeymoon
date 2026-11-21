/* Deterministic local tiles keep farms and forest in the same places on the return trip.
   Only nearby tiles own GPU instances. Coordinates use the terrain's island projection. */
function roadsideLandscape(pack, sheep, terrain, water, legs, west, airport, settlements) {
  const group=new THREE.Group(), batches=new Map(), cache=new Map(), roads=new Map();
  const cell=.10, key=(x,z)=>x+4096*z;
  const coord=(lat,lon)=>[(lon-170.5)*8.008,-(lat+44)*11.132];
  const towns=[[-43.531,172.60,1.04],[-43.502,172.554,.40],[-44.005,170.48,.12],[-44.258,170.098,.16],
    [-44.70,169.135,.22],[-45.41,167.718,.18],[-45.031,168.662,.22],[-43.387,170.183,.12],
    [-43.804,172.968,.12],[-44.09,171.24,.18],[-44.10,170.83,.13]].map(([lat,lon,r])=>[...coord(lat,lon),r]);
  const houses=new Map(), streetTiles=new Map();
  for(const [x,z,length,width,angle] of settlements.buildings){
    const k=key(Math.floor(x/1000),Math.floor(z/1000));
    if(!houses.has(k))houses.set(k,[]);
    houses.get(k).push([x/10000,z/10000,length/10000,width/10000,-angle*Math.PI/180]);
  }
  for(const street of settlements.streets){
    const points=[],dist=[],roadSamples=[];
    for(const [x,z] of street){
      const p=new THREE.Vector3(x/10000,0,z/10000),previous=points[points.length-1];
      if(previous&&p.distanceToSquared(previous)<1e-12)continue;
      roadSamples.push(points.length);dist.push(previous?dist[dist.length-1]+previous.distanceTo(p):0);points.push(p);
    }
    if(points.length<2)continue;
    const center=points[Math.floor(points.length/2)],id=key(Math.floor(center.x/.23),Math.floor(center.z/.23));
    if(!streetTiles.has(id))streetTiles.set(id,{pos:[],uv:[],normals:[],indices:[]});
    SurfaceTravel.ribbon({points,dist,roadSamples},.000115,terrain,streetTiles.get(id));
  }
  const streets=new THREE.Group();streets.name='Settlement streets';
  const material=new THREE.MeshBasicMaterial({color:'#727768',polygonOffset:true,polygonOffsetFactor:-.5,polygonOffsetUnits:-.5});
  for(const buffers of streetTiles.values()){
    const g=new THREE.BufferGeometry();
    g.setIndex(buffers.indices);g.setAttribute('position',new THREE.Float32BufferAttribute(buffers.pos,3));
    streets.add(new THREE.Mesh(g,material));
  }
  streetTiles.clear();group.userData.streets=streets;
  for(const leg of legs){
    const tr=leg.travel;
    if(!tr||tr.boat)continue;
    for(let j=1;j<tr.roadSamples.length;j++){
      const a=tr.points[tr.roadSamples[j-1]],b=tr.points[tr.roadSamples[j]];
      for(let iz=Math.floor((Math.min(a.z,b.z)-.022)/cell);iz<=Math.floor((Math.max(a.z,b.z)+.022)/cell);iz++)
        for(let ix=Math.floor((Math.min(a.x,b.x)-.022)/cell);ix<=Math.floor((Math.max(a.x,b.x)+.022)/cell);ix++){
          const k=key(ix,iz);if(!roads.has(k))roads.set(k,[]);
          roads.get(k).push([a.x,a.z,b.x-a.x,b.z-a.z]);
        }
    }
  }
  function distanceToSegment(x,z,ax,az,dx,dz){
    const f=THREE.MathUtils.clamp(((x-ax)*dx+(z-az)*dz)/(dx*dx+dz*dz||1),0,1);
    return Math.hypot(x-ax-dx*f,z-az-dz*f);
  }
  const apron=coord(-43.489,172.533);
  function nearAirport(x,z,r){
    if(Math.hypot(x-apron[0],z-apron[1])<.057+r)return true;
    return airport.some(([a,b])=>distanceToSegment(x,z,a.x,a.z,b.x-a.x,b.z-a.z)<.012+r);
  }
  const names=['Beech','Poplar','Tussock','Schist','Villa','VillaZinc','VillaSlate','Woolshed','Sheep'];
  pack.updateMatrixWorld(true);
  for(const name of names)for(const detail of ['Near','Far']){
    let source=name==='Sheep'?sheep:pack.getObjectByName(name+detail);
    if(!source)continue;
    // The wildlife file may contain several material groups. Preserve its fit and origin.
    source.updateWorldMatrix(true,true);
    const parts=[];
    source.traverse(o=>{if(o.isMesh)parts.push({geometry:o.geometry,material:o.material,local:o.matrixWorld.clone(),mesh:null})});
    batches.set(name+detail,parts);
  }
  let lastX,lastZ;
  const object=new THREE.Object3D(),matrix=new THREE.Matrix4();
  function tile(ix,iz){
    const k=key(ix,iz);
    if(cache.has(k))return cache.get(k);
    let seed=(Math.imul(ix+437,73856093)^Math.imul(iz+719,19349663))>>>0;
    const rnd=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
    const entries=[],x0=ix*cell,z0=iz*cell,cx=x0+cell*.5,cz=z0+cell*.5;
    function put(name,x,z,size,yaw=rnd()*Math.PI*2,width=size,height=size){
      const h=terrain.height(x,z);
      const margin=name==='Sheep'?.001:name==='Beech'?size*.44:Math.hypot(size,width)*.48;
      if(h===null||water(x,z)||h<-.001||nearAirport(x,z,margin))return;
      const network=roads.get(key(Math.floor(x/cell),Math.floor(z/cell)))||[];
      if(network.some(s=>distanceToSegment(x,z,...s)<.0015+margin))return;
      const dx=(terrain.height(x+.003,z)??h)-h,dz=(terrain.height(x,z+.003)??h)-h;
      const slope=Math.hypot(dx,dz)/.003;
      if(slope>((name.startsWith('Villa')||name==='Woolshed'||name==='Sheep')?.52:name==='Schist'?4:3.6))return;
      object.position.set(x,h-size*.018,z);object.rotation.set(0,yaw,0);object.scale.set(size,height,width);object.updateMatrix();
      entries.push([name,object.matrix.clone()]);
    }
    const forest=west(cx,cz),h=terrain.height(cx,cz)??0;
    const town=towns.some(([x,z,r])=>(x-cx)**2+(z-cz)**2<r*r);
    const plains=cx>4&&cz<-1&&h<.26&&!forest;
    const surveyed=settlements.areas.some(([l,n,r,s])=>cx*10000>l-500&&cx*10000<r+500&&cz*10000>n-500&&cz*10000<s+500);
    const lakeside=cx>-19&&cx<-14.4&&cz>8&&cz<14;
    if(surveyed){
      for(const [x,z,length,width,yaw] of houses.get(k)||[]){
        const shed=length>.0034;
        const villa=['Villa','VillaSlate','VillaZinc'][Math.floor(rnd()*3)];
        put(shed?'Woolshed':villa,x,z,length/(shed?1:.85),yaw,width/(shed?.64:.58),Math.min(length,.0017));
        if(!shed&&rnd()<.44){
          const offset=width*.64+.0007;
          put('Beech',x-Math.sin(yaw)*offset,z+Math.cos(yaw)*offset,.0014+rnd()*.0015);
        }
      }
    }else if(town&&h<.4){
      for(let j=0;j<5;j++){
        const x=x0+rnd()*cell,z=z0+rnd()*cell;
        put('Villa',x,z,.003+rnd()*.002,.31);
        put('Poplar',x+.004,z+.003,.004+rnd()*.004);
      }
    }else if((forest&&h<.70)||(lakeside&&h<.54)){
      const density=Math.round((forest?27:16)+(forest?18:12)*Math.sin(cx*9+cz*6));
      for(let i=0;i<density;i++){
        const x=x0+rnd()*cell,z=z0+rnd()*cell,scale=.008+rnd()*.014;
        put('Beech',x,z,scale);
        if(rnd()<.85)put('Beech',x+.006,z+.006,scale*.8);
      }
    }else if(plains||(!forest&&h<.29)){
      // Long shelterbelts between cropped paddocks, with gaps, outbuildings and grazing mobs.
      const a=x0+cell*(.15+.1*rnd());
      if(rnd()<.82)for(let j=0;j<11;j++)put('Poplar',a+j*.0024,z0+j*.009,.009+rnd()*.005,.2);
      if(rnd()<.20){
        put('Woolshed',x0+.052,z0+.050,.016,.29);
        put('Villa',x0+.070,z0+.070,.009,.29);
      }
      if(rnd()<.45)for(let j=0;j<9;j++)put('Sheep',x0+.05+rnd()*.034,z0+.032+rnd()*.037,.0011+rnd()*.0004);
    }else{
      for(let j=0;j<18;j++){
        const x=x0+rnd()*cell,z=z0+rnd()*cell;
        if(h<1.1)put('Tussock',x,z,.0026+rnd()*.0048);
        if(j<3)put('Schist',x,z,.006+rnd()*.008);
        if(h<.44&&j<3)put('Beech',x,z,.006+rnd()*.006);
      }
    }
    const sphere=new THREE.Sphere(new THREE.Vector3(cx,h,cz),.082);
    for(const [,m] of entries)sphere.radius=Math.max(sphere.radius,Math.abs(m.elements[13]-h)+.09);
    const result={entries,sphere};cache.set(k,result);return result;
  }
  const lastEye=new THREE.Vector3(Infinity,Infinity,Infinity),lastLook=new THREE.Quaternion();
  const frustum=new THREE.Frustum(),clip=new THREE.Matrix4(),sphere=new THREE.Sphere();
  const sight=new THREE.Line3(),nearest=new THREE.Vector3(),lastAnchor=new THREE.Vector3(Infinity,Infinity,Infinity);
  group.userData.update=(target,distance,camera,traveller)=>{
    group.visible=distance<3.8;
    if(!group.visible){lastX=lastZ=undefined;return;}
    const ix=Math.floor(target.x/cell),iz=Math.floor(target.z/cell);
    const moved=traveller&&lastAnchor.distanceToSquared(traveller)>.00010;
    if(!moved&&ix===lastX&&iz===lastZ&&lastEye.distanceToSquared(camera.position)<.0005&&lastLook.angleTo(camera.quaternion)<.07)return;
    if(traveller){lastAnchor.copy(traveller);sight.set(camera.position,traveller);}
    else lastAnchor.set(Infinity,Infinity,Infinity);
    lastX=ix;lastZ=iz;lastEye.copy(camera.position);lastLook.copy(camera.quaternion);
    camera.updateMatrixWorld();frustum.setFromProjectionMatrix(clip.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));
    const visible=new Map(),nearRadius=Math.min(.086,distance*.39);
    for(let dz=-4;dz<=4;dz++)for(let dx=-4;dx<=4;dx++){
      const patch=tile(ix+dx,iz+dz);
      if(!frustum.intersectsSphere(patch.sphere))continue;
      for(const [name,m] of patch.entries){
        const e=m.elements,size=Math.hypot(e[0],e[1],e[2]);
        sphere.center.set(e[12],e[13],e[14]);sphere.radius=.028+size;
        if(!frustum.intersectsSphere(sphere))continue;
        // Leave the line from the lens to the traveller free of foreground crowns and roofs.
        if(traveller){
          sphere.center.y+=.5*Math.abs(e[5]);
          sight.closestPointToPoint(sphere.center,true,nearest);
          if(nearest.distanceToSquared(sphere.center)<(.0015+size*.64)**2)continue;
        }
        const near=(e[12]-target.x)**2+(e[14]-target.z)**2<nearRadius*nearRadius;
        const id=name+(near&&size/distance>.022?'Near':'Far');
        if(!visible.has(id))visible.set(id,[]);visible.get(id).push(m);
      }
    }
    for(const [id,parts] of batches){
      const list=visible.get(id)||[];
      for(const part of parts){
        let mesh=part.mesh;
        if(list.length&&(!mesh||mesh.instanceMatrix.count<list.length)){
          if(mesh){group.remove(mesh);mesh.dispose();}
          const capacity=2**Math.ceil(Math.log2(Math.max(16,list.length)));
          mesh=part.mesh=new THREE.InstancedMesh(part.geometry,part.material,capacity);
          mesh.frustumCulled=false;mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);group.add(mesh);
        }
        if(!mesh)continue;
        list.forEach((m,i)=>mesh.setMatrixAt(i,matrix.multiplyMatrices(m,part.local)));
        mesh.count=list.length;mesh.visible=!!list.length;mesh.instanceMatrix.needsUpdate=true;
      }
    }
    if(cache.size>400){const active=new Set();for(let j=-4;j<=4;j++)for(let i=-4;i<=4;i++)active.add(key(ix+i,iz+j));
      for(const k of cache.keys()){if(cache.size<=230)break;if(!active.has(k))cache.delete(k);}
    }
  };
  return group;
}
