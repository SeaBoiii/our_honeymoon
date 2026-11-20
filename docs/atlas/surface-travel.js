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
    return path.points[i].clone().lerp(path.points[i+1],f);
  }

  // The ordinary map height raster is deliberately coarse. Intersect the
  // actual exported triangles under tyres so a neighbouring cliff cannot lift a car.
  function terrainIndex(){
    const tiles=new Map(),meshes=[];
    const tile=.38,key=(x,z)=>x+2048*z;
    return {
      mesh(x,y,z,index){
        const id=meshes.push({x,y,z,index})-1;
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
      height(px,pz){
        const hits=tiles.get(key(Math.floor(px/tile),Math.floor(pz/tile)));
        if(!hits)return null;
        let h=null;
        for(let i=0;i<hits.length;i+=2){
          const {x,y,z,index}=meshes[hits[i]],t=3*hits[i+1];
          const a=index?index[t]:t,b=index?index[t+1]:t+1,c=index?index[t+2]:t+2;
          const d=(z[b]-z[c])*(x[a]-x[c])+(x[c]-x[b])*(z[a]-z[c]);
          if(Math.abs(d)<1e-13)continue;
          const u=((z[b]-z[c])*(px-x[c])+(x[c]-x[b])*(pz-z[c]))/d;
          const v=((z[c]-z[a])*(px-x[c])+(x[a]-x[c])*(pz-z[c]))/d;
          if(u>=-.00001&&v>=-.00001&&u+v<=1.00001){
            const value=u*y[a]+v*y[b]+(1-u-v)*y[c];h=h===null?value:Math.max(h,value);
          }
        }
        return h;
      },
      release(){tiles.clear();meshes.length=0;}
    };
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
      const floor=points.map(p=>Math.max(ground(p.x,p.z)??0,0)+.0032);
      // A grade-limited upper envelope rounds approaches to DEM ridges. A
      // distance-weighted filter avoids overweighting densely sampled hairpins.
      const grade=.48,window=.048;
      for(let i=1;i<n;i++)floor[i]=Math.max(floor[i],floor[i-1]-grade*(dist[i]-dist[i-1]));
      for(let i=n-2;i>=0;i--)floor[i]=Math.max(floor[i],floor[i+1]-grade*(dist[i+1]-dist[i]));
      const area=[0];
      for(let i=1;i<n;i++)area.push(area[i-1]+(floor[i]+floor[i-1])*.5*(dist[i]-dist[i-1]));
      function integral(s){
        const i=segmentAt(dist,s),ds=s-dist[i],f=ds/(dist[i+1]-dist[i]);
        return area[i]+ds*(floor[i]+.5*f*(floor[i+1]-floor[i]));
      }
      for(let i=0;i<n;i++){
        const a=Math.max(0,dist[i]-window),b=Math.min(length,dist[i]+window);
        points[i].y=Math.max(floor[i],(integral(b)-integral(a))/(b-a));
      }
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
  function ribbon(path,metre,ground){
    const pos=[],uv=[],ix=[],banks=[],bankIx=[],half=2.95*metre;
    for(let i=0;i<path.points.length;i++){
      const p=path.points[i],direction=atDistance(path,path.dist[i]+.016).sub(atDistance(path,path.dist[i]-.016));
      const len=Math.hypot(direction.x,direction.z)||1;
      for(const sign of [-1,1]){
        const x=p.x+sign*half*direction.z/len,z=p.z-sign*half*direction.x/len;
        pos.push(x,p.y,z);
        const xOuter=p.x+sign*half*1.09*direction.z/len,zOuter=p.z-sign*half*1.09*direction.x/len;
        banks.push(x,p.y-.00002,z,xOuter,Math.min(p.y-.00018,ground(xOuter,zOuter)??0)-.00006,zOuter);
        uv.push((sign+1)*.5,path.dist[i]);
      }
      if(i){
        const j=i*2;ix.push(j-2,j-1,j,j,j-1,j+1);
        for(let side=0;side<2;side++){const a=(i-1)*4+2*side;bankIx.push(a,a+1,a+4,a+4,a+1,a+5);}
      }
    }
    const g=new THREE.BufferGeometry();
    g.setIndex(ix);g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
    const mat=new THREE.MeshBasicMaterial({color:'#545955',side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1});
    mat.onBeforeCompile=s=>{
      s.vertexShader='varying vec2 roadCoord;\n'+s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nroadCoord=uv;');
      s.fragmentShader='varying vec2 roadCoord;\n'+s.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
        float edge=smoothstep(.445,.475,abs(roadCoord.x-.5));
        float stripe=(1.-smoothstep(.012,.029,abs(roadCoord.x-.5)))*smoothstep(.38,.46,fract(roadCoord.y*280.));
        diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.77,.74,.60),max(edge*.68,stripe*.75));`);
    };
    const group=new THREE.Group(),bank=new THREE.BufferGeometry();
    bank.setIndex(bankIx);bank.setAttribute('position',new THREE.Float32BufferAttribute(banks,3));
    group.add(new THREE.Mesh(g,mat),new THREE.Mesh(bank,new THREE.MeshBasicMaterial({color:'#8b8775',side:THREE.DoubleSide})));
    return group;
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
  return {terrainIndex,forLeg,pose,ribbon};
})();
