/* Positions are in the map's 10 km units. Each surface leg owns one centreline
   for its visible road, overview stroke, wheel motion and distance clock. */
const SurfaceTravel=(()=>{
  function segmentAt(series,s){
    let lo=0,hi=series.length-1;
    while(hi-lo>1){const mid=(lo+hi)>>1;if(series[mid]<=s)lo=mid;else hi=mid;}
    return lo;
  }
  function atDistance(path,d){
    const s=Math.max(0,Math.min(path.length,d)),i=segmentAt(path.dist,s);
    const f=(s-path.dist[i])/(path.dist[i+1]-path.dist[i]);
    const p=path.points[i].clone().lerp(path.points[i+1],f);
    if(path.ground)p.y=path.ground(p.x,p.z)??p.y;
    return p;
  }

  // The ordinary map height raster is deliberately coarse. Intersect the
  // actual exported triangles under tyres so a neighbouring cliff cannot lift a car.
  function terrainIndex(){
    const tiles=new Map(),meshes=[];
    const tile=.16,key=(x,z)=>x+2048*z;
    let query=0;
    function facesIn(minX,minZ,maxX,maxZ,visit){
      const firstX=Math.floor(minX/tile),lastX=Math.floor(maxX/tile);
      const firstZ=Math.floor(minZ/tile),lastZ=Math.floor(maxZ/tile);
      const id=++query;
      for(let iz=firstZ;iz<=lastZ;iz++)for(let ix=firstX;ix<=lastX;ix++){
        const hits=tiles.get(key(ix,iz));
        if(!hits)continue;
        for(let i=0;i<hits.length;i+=2){
          const m=meshes[hits[i]],tri=hits[i+1],offset=tri*3;
          if(m.seen[tri]===id)continue;
          m.seen[tri]=id;
          const a=m.index?m.index[offset]:offset;
          let b=m.index?m.index[offset+1]:offset+1,c=m.index?m.index[offset+2]:offset+2;
          const x=m.x,z=m.z;
          if(maxX<Math.min(x[a],x[b],x[c])||minX>Math.max(x[a],x[b],x[c])||
             maxZ<Math.min(z[a],z[b],z[c])||minZ>Math.max(z[a],z[b],z[c]))continue;
          const det=(x[b]-x[a])*(z[c]-z[a])-(z[b]-z[a])*(x[c]-x[a]);
          if(Math.abs(det)<1e-14)continue;
          if(det<0){const swap=b;b=c;c=swap;}
          visit(m,a,b,c,Math.abs(det));
        }
      }
    }
    function height(px,pz){
      let h=null;
      facesIn(px,pz,px,pz,(m,a,b,c,det)=>{
        const dx=px-m.x[a],dz=pz-m.z[a];
        const wb=(dx*(m.z[c]-m.z[a])-dz*(m.x[c]-m.x[a]))/det;
        const wc=((m.x[b]-m.x[a])*dz-(m.z[b]-m.z[a])*dx)/det;
        if(wb>=-1e-8&&wc>=-1e-8&&wb+wc<=1+1e-8){
          const y=m.y[a]+wb*(m.y[b]-m.y[a])+wc*(m.y[c]-m.y[a]);
          h=h===null?y:Math.max(h,y);
        }
      });
      return h;
    }
    return {
      mesh(x,y,z,index,normals){
        const count=(index?index.length:x.length)/3;
        const id=meshes.push({x,y,z,index,normals,seen:new Float64Array(count)})-1;
        return (t,a,b,c)=>{
          const minX=Math.floor(Math.min(x[a],x[b],x[c])/tile),maxX=Math.floor(Math.max(x[a],x[b],x[c])/tile);
          const minZ=Math.floor(Math.min(z[a],z[b],z[c])/tile),maxZ=Math.floor(Math.max(z[a],z[b],z[c])/tile);
          for(let j=minZ;j<=maxZ;j++)for(let i=minX;i<=maxX;i++){
            const k=key(i,j);
            if(!tiles.has(k))tiles.set(k,[]);
            tiles.get(k).push(id,t);
          }
        };
      },
      height,facesIn
    };
  }

  // Keep corners in the rendered footprint while discarding collinear motion samples.
  // The maximum horizontal deviation is 12 cm in the map projection.
  function roadSampleIndices(points){
    const last=points.length-1,keep=new Uint8Array(points.length),stack=[[0,last]];
    const toleranceSq=.000012**2;
    keep[0]=keep[last]=1;
    while(stack.length){
      const [lo,hi]=stack.pop(),a=points[lo],b=points[hi],dx=b.x-a.x,dz=b.z-a.z;
      const lenSq=dx*dx+dz*dz;
      let split=-1,worst=toleranceSq;
      for(let i=lo+1;i<hi;i++){
        const sx=points[i].x-a.x,sz=points[i].z-a.z;
        const t=lenSq?Math.max(0,Math.min(1,(sx*dx+sz*dz)/lenSq)):0;
        const error=(sx-t*dx)**2+(sz-t*dz)**2;
        if(error>worst){worst=error;split=i;}
      }
      if(split!==-1){keep[split]=1;stack.push([lo,split],[split,hi]);}
    }
    const indices=[];
    for(let i=0;i<keep.length;i++)if(keep[i])indices.push(i);
    return indices;
  }

  function build(raw,mode,ground,level){
    const boat=mode==='boat',points=[raw[0].clone()],dist=[0];
    function append(p){
      const start=points[points.length-1],length=Math.hypot(p.x-start.x,p.z-start.z);
      if(length<1e-7)return;
      const pieces=Math.max(raw.length===2?2:1,Math.ceil(length/.009));
      for(let j=1;j<=pieces;j++){
        points.push(start.clone().lerp(p,j/pieces));dist.push(dist[dist.length-1]+length/pieces);
      }
    }
    // Local quadratic fillets cannot swing outside the triangle of their controls.
    // On a road the maximum trim is 25 m, even on highway-length segments.
    for(let i=1;i<raw.length-1;i++){
      const a=raw[i-1],b=raw[i],c=raw[i+1],ab=a.distanceTo(b),bc=b.distanceTo(c);
      if(ab<1e-7||bc<1e-7){append(b);continue;}
      const trim=Math.min(boat?.005:.0025,.34*ab,.34*bc);
      const entry=b.clone().lerp(a,trim/ab),exit=b.clone().lerp(c,trim/bc);
      append(entry);
      for(let j=1;j<=5;j++){
        const t=j/5;
        append(entry.clone().lerp(b,t).lerp(b.clone().lerp(exit,t),t));
      }
    }
    append(raw[raw.length-1]);
    if(points.length<2)return null;
    const length=dist[dist.length-1],n=points.length;
    const path={points,dist,length};
    if(boat){points.forEach(p=>p.y=level+.0007);}
    else{
      path.ground=ground;
      path.roadSamples=roadSampleIndices(points);
      for(const p of points)p.y=ground(p.x,p.z)??0;
    }
    // Limit lateral acceleration through bends, then propagate braking and
    // acceleration along distance. The speed table is independent of frame rate.
    const cruise=boat?.14:mode==='coach'?.43:.55,accel=boat?.06:.19;
    // Average unwrapped bearings in distance space. At a switchback the two
    // arms may point in opposite directions, so averaging their vectors is unstable.
    const headings=[],integrals=[0],yaw=[],speeds=new Float64Array(n).fill(cruise);
    for(let i=0;i<n-1;i++){
      const a=points[i],b=points[i+1];
      let angle=Math.atan2(b.x-a.x,b.z-a.z);
      if(i){const delta=angle-headings[i-1];angle=headings[i-1]+Math.atan2(Math.sin(delta),Math.cos(delta));}
      headings.push(angle);
      integrals.push(integrals[i]+angle*(dist[i+1]-dist[i]));
    }
    function headingIntegral(s){
      const i=segmentAt(dist,s);return integrals[i]+headings[i]*(s-dist[i]);
    }
    const look=boat?.006:.033,maxYaw=boat?1.15:1.65;
    for(const s of dist){
      const a=Math.max(0,s-look),b=Math.min(length,s+look);
      yaw.push((headingIntegral(b)-headingIntegral(a))/(b-a));
    }
    for(let i=1;i<n;i++){
      const bend=Math.abs(yaw[i]-yaw[i-1])/(dist[i]-dist[i-1]);
      if(bend<1e-6)continue;
      const limit=Math.min(maxYaw/bend,Math.sqrt((boat?.24:.78)/bend));
      speeds[i-1]=Math.min(speeds[i-1],limit);speeds[i]=Math.min(speeds[i],limit);
    }
    speeds[0]=speeds[n-1]=0;
    for(let i=1;i<n;i++)speeds[i]=Math.min(speeds[i],Math.sqrt(speeds[i-1]**2+2*accel*(dist[i]-dist[i-1])));
    for(let i=n-2;i>=0;i--)speeds[i]=Math.min(speeds[i],Math.sqrt(speeds[i+1]**2+2*accel*(dist[i+1]-dist[i])));
    const time=[0];
    for(let i=1;i<n;i++)time.push(time[i-1]+2*(dist[i]-dist[i-1])/(speeds[i]+speeds[i-1]));
    return Object.assign(path,{time,speeds,yaw,duration:time[n-1],boat});
  }
  function pose(path,u){
    const clock=Math.max(0,Math.min(1,u))*path.duration;
    const i=segmentAt(path.time,clock),dt=clock-path.time[i],span=path.time[i+1]-path.time[i];
    const s=path.dist[i]+dt*(path.speeds[i]+.5*(path.speeds[i+1]-path.speeds[i])*dt/span);
    const look=path.boat?.022:.052;
    const f=(s-path.dist[i])/(path.dist[i+1]-path.dist[i]);
    const bearing=path.yaw[i]+f*(path.yaw[i+1]-path.yaw[i]);
    const tangent=atDistance(path,s+look).sub(atDistance(path,s-look));
    const grade=path.boat?0:THREE.MathUtils.clamp(tangent.y/(Math.max(1e-5,Math.min(path.length,s+look)-Math.max(0,s-look))),-.13,.13);
    const heading=new THREE.Vector3(Math.sin(bearing),grade,Math.cos(bearing));
    return {p:atDistance(path,s),d:heading,s,speed:path.speeds[i]+(path.speeds[i+1]-path.speeds[i])*dt/span};
  }
  // Subdivide the overview centreline at triangle boundaries before depth testing it.
  function groundLine(points,terrain){
    const result=[points[0]];
    for(let i=1;i<points.length;i++){
      const p=points[i-1],q=points[i],cuts=[];
      terrain.facesIn(Math.min(p.x,q.x),Math.min(p.z,q.z),Math.max(p.x,q.x),Math.max(p.z,q.z),(m,a,b,c)=>{
        const corners=[a,b,c];let entry=0,exit=1;
        for(let k=0;k<3;k++){
          const j=corners[k],l=corners[(k+1)%3],dx=m.x[l]-m.x[j],dz=m.z[l]-m.z[j];
          const from=dx*(p.z-m.z[j])-dz*(p.x-m.x[j]),to=dx*(q.z-m.z[j])-dz*(q.x-m.x[j]);
          if(from<0&&to<0)return;
          if(from<0)entry=Math.max(entry,from/(from-to));
          if(to<0)exit=Math.min(exit,from/(from-to));
        }
        if(entry<=exit&&exit>1e-7&&exit<1-1e-7)cuts.push(exit);
      });
      cuts.sort((a,b)=>a-b);
      let previous=0;
      for(const t of cuts){
        if(t-previous<1e-7)continue;
        const v=p.clone().lerp(q,t);
        v.y=terrain.height(v.x,v.z)??v.y;result.push(v);previous=t;
      }
      result.push(q);
    }
    return result;
  }
  // Terrain height is linear within each face. Checking the face boundaries
  // yields the minimum eye height that clears every intervening ridge.
  function cameraFloor(terrain,target,eye,clearance){
    const dx=eye.x-target.x,dz=eye.z-target.z,lengthSq=dx*dx+dz*dz;
    let required=Math.max(terrain.height(eye.x,eye.z)??target.y,target.y)+clearance;
    if(lengthSq<1e-12)return required;
    const profile=groundLine([target,eye],terrain);
    for(let i=1;i<profile.length-1;i++){
      const p=profile[i],t=((p.x-target.x)*dx+(p.z-target.z)*dz)/lengthSq;
      if(t>1e-5)required=Math.max(required,target.y+(p.y-target.y)/t+clearance);
    }
    return required;
  }

  function wheelContact(travel,pose,spec,metre){
    const p=pose.p,len=Math.hypot(pose.d.x,pose.d.z),fx=pose.d.x/len,fz=pose.d.z/len;
    const axle=spec.length*metre*.32,side=spec.width*metre*.39;
    function support(forward,right){
      return travel.ground(p.x+fx*forward+fz*right,p.z+fz*forward-fx*right)??p.y;
    }
    const fl=support(axle,-side),fr=support(axle,side),bl=support(-axle,-side),br=support(-axle,side);
    const grade=(fl+fr-bl-br)/(4*axle),bank=(fr+br-fl-bl)/(4*side);
    pose.d.set(fx,grade,fz);
    return new THREE.Vector3(-fx*grade-fz*bank,1,-fz*grade+fx*bank).normalize();
  }

  // Clip the pavement footprint in XZ and lift each piece onto its terrain face.
  function clipEdge(polygon,ax,az,bx,bz){
    if(!polygon.length)return polygon;
    const output=[],dx=bx-ax,dz=bz-az;
    let prev=polygon[polygon.length-1],prevSide=dx*(prev.z-az)-dz*(prev.x-ax);
    for(const p of polygon){
      const side=dx*(p.z-az)-dz*(p.x-ax);
      if((side<0)!==(prevSide<0)){
        const f=prevSide/(prevSide-side);
        output.push({x:prev.x+(p.x-prev.x)*f,z:prev.z+(p.z-prev.z)*f,
          u:prev.u+(p.u-prev.u)*f,s:prev.s+(p.s-prev.s)*f});
      }
      if(side>=0)output.push(p);
      prev=p;prevSide=side;
    }
    return output;
  }
  function ribbon(path,metre,terrain){
    const pos=[],uv=[],normals=[],indices=[],half=2.95*metre;
    function drape(polygon){
      let minX=Infinity,minZ=Infinity,maxX=-Infinity,maxZ=-Infinity;
      for(const p of polygon){minX=Math.min(minX,p.x);minZ=Math.min(minZ,p.z);maxX=Math.max(maxX,p.x);maxZ=Math.max(maxZ,p.z);}
      terrain.facesIn(minX,minZ,maxX,maxZ,(m,a,b,c,det)=>{
        const {x,y,z}=m;
        let clipped=clipEdge(polygon,x[a],z[a],x[b],z[b]);
        clipped=clipEdge(clipped,x[b],z[b],x[c],z[c]);
        clipped=clipEdge(clipped,x[c],z[c],x[a],z[a]);
        if(clipped.length<3)return;
        const slopeX=((y[b]-y[a])*(z[c]-z[a])-(y[c]-y[a])*(z[b]-z[a]))/det;
        const slopeZ=((x[b]-x[a])*(y[c]-y[a])-(x[c]-x[a])*(y[b]-y[a]))/det;
        let area=0;
        for(let j=1;j<clipped.length-1;j++)area+=turn(clipped[0],clipped[j],clipped[j+1]);
        if(Math.abs(area)<1e-16)return;
        const start=pos.length/3;
        for(const v of clipped){
          pos.push(v.x,y[a]+slopeX*(v.x-x[a])+slopeZ*(v.z-z[a]),v.z);
          uv.push(v.u,v.s);
          // Use the same interpolated shading normals as the ground under the asphalt.
          if(m.normals){
            const dx=v.x-x[a],dz=v.z-z[a],n=m.normals;
            const wb=(dx*(z[c]-z[a])-dz*(x[c]-x[a]))/det;
            const wc=((x[b]-x[a])*dz-(z[b]-z[a])*dx)/det;
            for(let j=0;j<3;j++)normals.push((1-wb-wc)*n[3*a+j]+wb*n[3*b+j]+wc*n[3*c+j]);
          }else{
            const length=Math.hypot(slopeX,1,slopeZ);
            normals.push(-slopeX/length,1/length,-slopeZ/length);
          }
        }
        for(let i=1;i<clipped.length-1;i++){
          if(area>0)indices.push(start,start+i+1,start+i);
          else indices.push(start,start+i,start+i+1);
        }
      });
    }
    function turn(a,b,c){return (b.x-a.x)*(c.z-a.z)-(b.z-a.z)*(c.x-a.x);}
    let previous;
    const samples=path.roadSamples;
    const forward=new THREE.Vector2(),incoming=new THREE.Vector2(),bisector=new THREE.Vector2();
    for(let j=0;j<samples.length;j++){
      const i=samples[j],p=path.points[i],next=path.points[samples[Math.min(j+1,samples.length-1)]],last=path.points[samples[Math.max(0,j-1)]];
      incoming.set(p.x-last.x,p.z-last.z).normalize();
      forward.set(next.x-p.x,next.z-p.z).normalize();
      if(!i)incoming.copy(forward);
      if(i===path.points.length-1)forward.copy(incoming);
      bisector.copy(incoming).add(forward).normalize();
      if(bisector.lengthSq()<1e-10)bisector.copy(forward);
      const width=half/Math.max(.65,bisector.dot(forward));
      const dx=width*bisector.y,dz=-width*bisector.x;
      const left={x:p.x-dx,z:p.z-dz,u:0,s:path.dist[i]},right={x:p.x+dx,z:p.z+dz,u:1,s:path.dist[i]};
      if(previous){
        const outline=[previous.left,previous.right,right,left];
        if(outline.every((v,k)=>turn(v,outline[(k+1)%4],outline[(k+2)%4])>=0))drape(outline);
        else{drape([previous.left,previous.right,left]);drape([left,previous.right,right]);}
      }
      previous={left,right};
    }
    const g=new THREE.BufferGeometry();
    g.setIndex(indices);g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
    g.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));
    const mat=new THREE.MeshStandardMaterial({color:'#525852',roughness:.97,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1});
    mat.onBeforeCompile=s=>{
      s.vertexShader='varying vec2 roadCoord;\n'+s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nroadCoord=uv;');
      s.fragmentShader='varying vec2 roadCoord;\n'+s.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
        float edge=smoothstep(.445,.475,abs(roadCoord.x-.5));
        float stripe=(1.-smoothstep(.012,.029,abs(roadCoord.x-.5)))*smoothstep(.38,.46,fract(roadCoord.y*280.));
        diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.77,.74,.60),max(edge*.68,stripe*.75));`);
    };
    const mesh=new THREE.Mesh(g,mat);mesh.receiveShadow=true;mesh.renderOrder=1;
    return mesh;
  }
  function cruisePoints(record,direction,project){
    const points=record.points.map(project);
    if(direction==='back')return points.reverse();
    if(direction!=='round')return points;
    const last=points[points.length-1],along=last.clone().sub(points[points.length-2]).normalize();
    const across=new THREE.Vector3(-along.z,0,along.x),turn=points.slice(),radius=.0022;
    for(let j=1;j<=18;j++){
      const a=Math.PI*j/18;
      turn.push(last.clone().addScaledVector(along,radius*Math.sin(a)).addScaledVector(across,radius*(1-Math.cos(a))));
    }
    return turn.concat(points.slice(0,-1).reverse());
  }
  function forLeg(mode,path,routes,cruises,project,ground,seaHeight,verticalScale){
    const [,key,direction]=path.split(':'),boat=mode==='boat',record=(boat?cruises:routes)[key];
    if(!record||record.points.length<2)return null;
    const raw=boat?cruisePoints(record,direction,project):record.points.map(project);
    const level=boat&&record.level!==0?record.level*verticalScale:seaHeight;
    const travel=build(raw,mode,ground,level);
    if(travel)travel.km=record.km;
    return travel;
  }
  return {terrainIndex,forLeg,pose,ribbon,groundLine,cameraFloor,wheelContact};
})();
