// Model the arrival using Christchurch Airport's published 02/20 and 11/29 endpoints.
const airportRunways=[
  [[-43.497614,172.522113],[-43.474966,172.548293]],
  [[-43.484272,172.524408],[-43.494366,172.540878]]
];
function addChristchurchAirport(scene, project, terrain, runwayScale=1){
  const runways=airportRunways.map(pair=>pair.map(ll=>project(...ll)));
  const airfield=new THREE.Group();airfield.name='Christchurch Airport';
  function pavement(a,b,width,color,offset){
    const dx=b.x-a.x,dz=b.z-a.z,length=Math.hypot(dx,dz),rx=dz/length,rz=-dx/length;
    const positions=[],index=[],n=Math.ceil(length/.003);
    for(let i=0;i<=n;i++){
      for(const side of [-1,1]){
        const x=a.x+i/n*dx+side*rx*width/2,z=a.z+i/n*dz+side*rz*width/2;
        positions.push(x,terrain.height(x,z)??0,z);
      }
      if(i){const j=2*i;index.push(j-2,j,j-1,j-1,j,j+1);}
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setIndex(index);
    const mat=new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-offset,polygonOffsetUnits:-offset});
    const mesh=new THREE.Mesh(g,mat);mesh.renderOrder=offset;airfield.add(mesh);
  }
  for(const [a,b] of runways){
    const point=t=>({x:a.x+t*(b.x-a.x),z:a.z+t*(b.z-a.z)});
    pavement(a,b,.008*runwayScale,'#4f5552',1);
    for(let i=1;i<33;i++)pavement(point(i/34),point((i+.43)/34),.00046*runwayScale,'#f2edce',2);
  }
  const terminal=project(-43.48836,172.53970);
  const origin=new THREE.Group();origin.rotation.y=-.66;origin.position.set(terminal.x,terrain.height(terminal.x,terminal.z)??0,terminal.z);
  function block(x,y,z,w,h,d,color){
    const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),new THREE.MeshStandardMaterial({color,roughness:.78}));
    m.position.set(x,y,z);origin.add(m);
  }
  block(0,.0026,0,.016,.0052,.050,'#bcc3b7');
  block(-.008,.0022,0,.001,.003,.048,'#58777a');
  block(0,.0055,0,.018,.001,.052,'#808c8b');
  for(let i=-2;i<=2;i++)block(.004,.0064,i*.008,.005,.0012,.0035,'#aeb8b2');
  for(let i=-2;i<=2;i++)block(-.012,.0025,i*.009,.008,.0015,.0024,'#a9ada0');
  airfield.add(origin);scene.add(airfield);return runways;
}

const stopNames={air:'Christchurch Airport',chc:'Christchurch',tekapo:'Lake Tekapo',twizel:'Twizel',
  mtcook:'Aoraki / Mt Cook',wanaka:'Wānaka',teanau:'Te Anau',milford:'Milford Sound',qt:'Queenstown',
  coronet:'Coronet Peak',onsen:'Arthurs Point',glenorchy:'Glenorchy',franz:'Franz Josef',akaroa:'Akaroa'};
function routeInset(panel){
  const caption=panel.querySelector('span'),canvas=panel.querySelector('canvas'),ctx=canvas.getContext('2d');
  let previous=null,outline,project;
  return (leg,position)=>{
    panel.hidden=!leg?.travel;
    if(panel.hidden)return;
    if(previous!==leg){
      previous=leg;
      const names=leg.key.split('-');
      const destination=leg.travel.boat?(leg.key==='te-anau'?(leg.cap.startsWith('Back')?'Te Anau wharf':'Glowworm caves'):leg.key==='milford'?'Milford Sound cruise':'Akaroa Harbour cruise'):stopNames[names[1]];
      caption.textContent=(leg.travel.boat?'Cruising to ':'Driving to ')+destination;
      if(leg.travel.boat&&leg.key!=='te-anau')caption.textContent=destination;
      const tr=leg.travel,points=(tr.roadSamples||tr.points.map((p,i)=>i)).map(i=>tr.points[i]);
      let minX=Infinity,maxX=-Infinity,minZ=Infinity,maxZ=-Infinity;
      for(const p of points){minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minZ=Math.min(minZ,p.z);maxZ=Math.max(maxZ,p.z);}
      const scale=Math.min(182/Math.max(.001,maxX-minX),39/Math.max(.001,maxZ-minZ));
      project=p=>[100+(p.x-(minX+maxX)/2)*scale,25+(p.z-(minZ+maxZ)/2)*scale];
      outline=new Path2D();points.forEach((p,i)=>{const [x,y]=project(p);if(i)outline.lineTo(x,y);else outline.moveTo(x,y);});
    }
    ctx.setTransform(2,0,0,2,0,0);ctx.clearRect(0,0,200,50);
    ctx.strokeStyle='#9a8469';ctx.lineWidth=1.65;ctx.lineJoin='round';ctx.stroke(outline);
    function pin(p,r,color){const [x,y]=project(p);ctx.beginPath();ctx.arc(x,y,r,0,2*Math.PI);ctx.fillStyle=color;ctx.fill();ctx.strokeStyle='#fff8e9';ctx.lineWidth=1.2;ctx.stroke();}
    pin(leg.pts[leg.pts.length-1],3.3,'#ab593b');pin(position,4,'#215b4a');
  };
}


// Choose an open side of the valley on a camera cut. Keep that bearing through the leg.
function chooseValleyView(terrain,target,eye,distance){
  const offset=eye.clone().sub(target);
  const required=SurfaceTravel.cameraFloor(terrain,target,eye,.032);
  if(required<eye.y+distance*.18)return;
  const up=new THREE.Vector3(0,1,0);
  let best=required;
  for(const turn of [Math.PI/2,-Math.PI/2,Math.PI]){
    const candidate=offset.clone().applyAxisAngle(up,turn).add(target);
    const floor=SurfaceTravel.cameraFloor(terrain,target,candidate,.032);
    if(floor<best-distance*.08){best=floor;eye.copy(candidate);}
  }
}
