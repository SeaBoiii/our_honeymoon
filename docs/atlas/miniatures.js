/* Studio lighting and framing for the same exported objects used on the route. */
const atlasPlaces = [
  {key:'fleet',asset:'fleet',day:1,title:'Vehicles to scale',location:'Transport',
   text:'The 4.82 m SUV shares a scale with the 12.6 m coach, 12.9 m helicopter, 24 m cruise boat and 64 m airliner. Lengths represent their vehicle classes.',color:'#e1e7db',angle:[.07,1.9,-1.1]},
  {key:'observatory',asset:'observatory',day:2,title:'The observatory',location:'Mount John',text:'Shutter guides cross the segmented dome above its circular service walkway.',color:'#dfdfcd',angle:[-3.1,2.1,-4.4]},
  {key:'willow',asset:'lone_tree',day:4,title:'The lakeside willow',location:'Wānaka',text:'Long leaf sprays hang from a bent trunk over a shallow shingle bed.',color:'#d0e6dc',angle:[-3.7,1.4,-3.8]},
  {key:'onsen',asset:'hot_tub',day:8,title:'The cedar onsen',location:'Arthurs Point',text:'Cedar staves, metal hoops and a timber stair enclose the pool above the river.',color:'#e5dcca',angle:[-3.6,3.2,-4.3]},
  {key:'mosque',asset:'mosque',day:1,title:'The prayer hall',location:'Christchurch',text:'A miniature prayer hall with arched glazing, a ribbed balcony around the minaret and a paved courtyard.',color:'#e4dfcd',angle:[-3.4,2.2,-4.2]},
  {key:'city',asset:'city',day:1,title:'A city block',location:'Christchurch',text:'Shop awnings, painted crossings and roof vents mark the streets in this miniature city block.',color:'#d9dfd7',angle:[-3.4,3.1,-4.2]},
  {key:'cave',asset:'glowworm_cave',day:5,title:'The glowworm caves',location:'Te Anau',text:'A small tender sits beneath a limestone arch, hanging stalactites and points of glowworm light.',color:'#acbfbc',angle:[-.9,1.5,4.5]},
  {key:'skilift',asset:'ski_lift',day:8,title:'The chairlift',location:'Coronet Peak',text:'Ladders climb the lift towers to the sheave trains that guide the chair cables.',color:'#d9e7e7',angle:[-3.5,2.6,-3.7]},
  {key:'ice',asset:'glacier_ice',day:11,title:'The glacier tongue',location:'Franz Josef',text:'Open crevasses separate layered blue séracs above a ridge of moraine stones.',color:'#d5e6e7',angle:[-3,2.8,-4]},

  {key:'suv', asset:'car', day:1, title:'Our touring SUV', location:'Christchurch',
   text:'Orbit the silver SUV to see its split-spoke wheels, dark glass and roof rails.', color:'#d6ded8', angle:[-4.6,2,-5.5]},
  {key:'merino', asset:'sheep', day:2, title:'A high-country merino', location:'Mackenzie Country',
   text:'A closer look at the crimped fleece, curled horns and cloven hooves of a South Island ram.', color:'#e7e6cb', angle:[-3.8,1.9,-4.8]},
  {key:'valley', asset:'hooker_valley', day:3, title:'Hooker Valley', location:'Aoraki / Mount Cook',
   text:'A timber swing bridge crosses the glacial river beneath the snowline.', color:'#d4e4db', angle:[2.5,4.1,7.5]},
  {key:'chapel', asset:'church_stone', day:2, title:'The stone chapel', location:'Lake Tekapo',
   text:'Schist walls, a small belfry and a standing-seam roof on the lakeshore.', color:'#d9e4d0', angle:[-3.7,2,-4]},
  {key:'cruise', asset:'boat', day:6, title:'Into the fiord', location:'Milford Sound',
   text:'Follow the cruise from the wharf, past Mitre Peak and out towards the Tasman Sea.', color:'#cfe5e8', angle:[3.7,2.5,-4.4]},
  {key:'helicopter', asset:'helicopter', day:11, title:'Above the glacier', location:'Franz Josef',
   text:'The morning helicopter carries us up from the West Coast to the blue ice.', color:'#e9dfca', angle:[4.5,2,-3]}
];

function makeFleetDisplay(models,fleet){
  const group=new THREE.Group();
  // Boats, coaches and cars line the near edge of the apron, clear of the wings.
  const small=['boat','heli','coach','car'],specs=fleet.vehicles;
  const span=small.reduce((sum,key)=>sum+specs[key].width,0)+(small.length-1)*3.6;
  let edge=-span/2;
  for(const mode of [...small,'plane']){
    const spec=specs[mode],source=models[spec.asset];
    if(!source)return null;
    const model=source.clone(true);
    model.position.set(mode==='plane'?0:edge+spec.width/2,0,(mode==='plane'?1:-27)+spec.length/2);
    group.add(model);edge+=spec.width+3.6;
  }
  return group;
}

function makeMiniatureStudio(renderer) {
  const stage=new THREE.Scene(),room=new THREE.Scene();
  room.background=new THREE.Color('#84968f');
  for(const [x,y,z,width,height,color] of [[-5,4,1,3,6,'#fff7e8'],[3,2,4,5,2,'#e9f1ed'],[1,5,-4,6,1,'#cbdeed']]){
    const panel=new THREE.Mesh(new THREE.PlaneGeometry(width,height),new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide}));
    panel.position.set(x,y,z);panel.lookAt(0,0,0);room.add(panel);
  }
  const generator=new THREE.PMREMGenerator(renderer);
  stage.environment=generator.fromScene(room,.035).texture;
  generator.dispose();room.children.forEach(p=>{p.geometry.dispose();p.material.dispose();});
  const light=new THREE.DirectionalLight('#fff0d4',1.10);
  light.position.set(-3,6,4);
  light.castShadow=true;light.shadow.mapSize.set(1024,1024);
  Object.assign(light.shadow.camera,{left:-2,right:2,top:2,bottom:-2,near:1,far:14});
  light.shadow.normalBias=.003;
  const rim=new THREE.DirectionalLight('#dceeff',.32);
  rim.position.set(3,2,-3);
  stage.add(new THREE.HemisphereLight('#f6faf5','#808976',.67),light,rim);
  const spot=document.createElement('canvas');
  spot.width=spot.height=128;
  const ctx=spot.getContext('2d');
  const blur=ctx.createRadialGradient(64,64,0,64,64,63);
  blur.addColorStop(0,'rgba(29,53,40,.34)');
  blur.addColorStop(.52,'rgba(29,53,40,.18)');
  blur.addColorStop(1,'rgba(29,53,40,0)');
  ctx.fillStyle=blur;ctx.fillRect(0,0,128,128);
  const shadow=new THREE.Mesh(new THREE.PlaneGeometry(1,1),new THREE.MeshBasicMaterial({
    map:new THREE.CanvasTexture(spot),transparent:true,depthWrite:false}));
  shadow.rotation.x=-Math.PI/2;shadow.position.y=-.025;stage.add(shadow);
  let model=null;
  return {
    scene:stage,
    show(source,place,camera,controls) {
      if(model)stage.remove(model);
      model=source.clone(true);
      model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
      const bounds=new THREE.Box3().setFromObject(model);
      const size=bounds.getSize(new THREE.Vector3());
      const scale=2.5/Math.max(size.x,size.y,size.z);
      const center=bounds.getCenter(new THREE.Vector3());
      model.scale.multiplyScalar(scale);
      model.position.set(-center.x*scale,-bounds.min.y*scale,-center.z*scale);
      stage.add(model);
      shadow.scale.set(Math.max(size.x*scale*1.42,.6),Math.max(size.z*scale*1.42,.6),1);
      stage.background=new THREE.Color(place.color);
      controls.minDistance=place.key==='fleet'?.25:.72;controls.maxDistance=9;controls.maxPolarAngle=Math.PI*.49;
      controls.enablePan=false;controls.target.set(0,size.y*scale*.48,0);
      const radius=size.length()*scale*.5;
      const dist=Math.max(3.65,1.12*radius/Math.sin(THREE.MathUtils.degToRad(camera.fov*.5)))/Math.min(1,camera.aspect);
      camera.position.fromArray(place.angle).normalize().multiplyScalar(dist).add(controls.target);
      controls.update();
    }
  };
}
