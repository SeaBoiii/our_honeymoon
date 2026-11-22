/* The driving tour and the destination chapters use the same island and route geometries. */
const itineraryLandmarks=[
  // Asset, map position, original broad-map extent, illustrative extent in metres, fallback colour.
  ['hooker_valley',[-43.72,170.10],.72,610,'#8b9b83'],
  ['city',[-43.532,172.636],.16,130,'#ccc'],
  ['mosque',[-43.545,172.56],.26,42,'#eee',[-43.53289,172.61181]],
  ['church_stone',[-44.015,170.50],.22,21,'#a98',[-44.00334,170.48236]],
  ['observatory',[-43.975,170.455],.22,26,'#ddd'],
  ['lone_tree',[-44.693,169.115],.20,16,'#7a6'],
  ['glowworm_cave',[-45.29495,167.7269],.26,52,'#556'],
  ['hot_tub',[-44.985,168.66],.20,12,'#a86',[-44.981,168.68543]],
  ['ski_lift',[-44.92,168.745],.40,155,'#ddd'],
  ['glacier_ice',[-43.505,170.30],.60,320,'#cdeffa']
];

function fullDriveRequested(){
  const mode=new URLSearchParams(location.search).get('tour');
  if(location.hash.startsWith('#scene-'))return false;
  return mode==='drive'||(!mode&&location.hash.startsWith('#leg-'));
}

function buildItinerary(full,landmarks,project,terrain,water,requested){
  const chapters=[];
  function visit(id,day,title,where,cap,clock='',night=0,distance=.9){
    if(requested==='all'){
      chapters.push({id,day,title,dur:8});return;
    }
    let at;
    if(typeof where==='string'){
      const landmark=landmarks.get(where);
      at=landmark.center.clone();
      distance=landmark.extent*2.85;
    }else{
      const p=project(...where);
      at=new THREE.Vector3(p.x,Math.max(terrain.height(p.x,p.z)??-.018,water.height(p.x,p.z)??-.018),p.z);
    }
    chapters.push({id,day,title,at,site:typeof where==='string'?where:null,cap,clock,night,
      viewDistance:distance,mode:'stay',world:'nz',dur:8});
  }
  function clip(id,day,mode,title,seconds,from=0,to=1,key){
    const leg=full.find(l=>l.day===day&&l.mode===mode&&(!key||l.key===key));
    if(leg)chapters.push({...leg,id,title,dur:seconds,from,to,viewDistance:mode==='boat'?.55:undefined});
  }
  function extra(id,...args){
    if(id===requested||requested==='all'){visit(id,...args);chapters.at(-1).directOnly=true;}
  }
  clip('changi',0,'gstay','Changi Airport',4);
  clip('singapore-flight',0,'gfly','Singapore to the South Island',5,.20,.66);
  clip('christchurch-arrival',1,'plane','Arriving in Christchurch',4,.69,.98);
  extra('christchurch-pickup',1,'Christchurch Airport car pickup',[-43.488,172.54],'Collect the rental car and check the snow chains.','',0,.24);
  visit('al-noor',1,'Al Noor Mosque','mosque','After collecting the car, stop for Dhuhr in Riccarton.','13:00');
  visit('botanic-gardens',1,'Christchurch Botanic Gardens',[-43.530,172.620],'Walk beside the Avon before dinner in Riccarton.');
  visit('tekapo-chapel',2,'Church of the Good Shepherd','church_stone','Walk the Lake Tekapo foreshore to the stone chapel.');
  extra('tekapo-springs',2,'Tekapo Springs','thermal_pools','Soak in the outdoor pools above the lakeshore.');
  visit('mount-john',2,'Mount John after dark','observatory','After the hot pools at Tekapo Springs, head up to Mount John for the stars.','21:30',.83);
  extra('twizel',3,'Twizel village',[-44.257,170.098],'Pick up groceries in Twizel before the alpine section.', '',0,.27);
  clip('pukaki-road',3,'car','Lake Pukaki road',3,.44,.49,'twizel-mtcook');
  visit('hooker-valley',3,'Hooker Valley','hooker_valley','Follow the walking track and look up the valley towards Aoraki.','11:30');
  extra('lindis-pass',4,'Lindis Pass',[-44.589,169.643],'Cross the open tussock saddle in daylight.','',0,1.8);
  extra('wanaka-lakefront',4,'Wānaka lakefront',[-44.694,169.133],'Take a walk along the town waterfront.','',0,.84);
  visit('wanaka-tree',4,'That Wānaka Tree','lone_tree','Spend sunset on the lakefront after the crossing of Lindis Pass.','17:40',.30);
  extra('cromwell',5,'Cromwell',[-45.037,169.201],'Follow the route via Cromwell on the way to Te Anau.','',0,1.1);
  extra('frankton',5,'Frankton',[-45.012,168.743],'Stock up in Frankton for Fiordland and the Milford picnic.','',0,.67);
  clip('te-anau-crossing',5,'boat','Crossing Lake Te Anau',4,.35,.48,'te-anau');
  visit('glowworm-caves',5,'Te Anau Glowworm Caves','glowworm_cave','Leave the daylight at the cave entrance for the silent glowworm grotto.','17:15',.35);
  clip('eglinton-valley',6,'coach','Eglinton Valley',3,.26,.30,'teanau-milford');
  visit('milford-lookout',6,'Milford Sound / Piopiotahi',[-44.641,167.891],'From the head of the fiord, look across the water towards Mitre Peak.','',0,2.7);
  clip('milford-cruise',6,'boat','Milford Sound cruise',5,.06,.14,'milford');
  extra('te-anau-morning',7,'Te Anau lakefront',[-45.415,167.712],'Spend the morning by the lake before leaving for Queenstown.','',0,.9);
  extra('milford-retry',7,'Milford Sound weather alternative',[-44.641,167.891],'Return to the fiord if the previous day’s trip was cancelled.','',0,2.7);
  visit('queenstown-waterfront',7,'Queenstown lakefront',[-45.033,168.659],'Walk the waterfront, then find dinner in town.','18:30',.24,1.15);
  visit('coronet-ski',8,'Coronet Peak','ski_lift','The morning is for a first ski lesson.','10:00');
  visit('onsen-sunset',8,'Onsen at Arthurs Point','hot_tub','Soak in a cedar tub above the Shotover River as the sun goes down.','17:45',.48);
  clip('glenorchy-road',9,'car','The Glenorchy lake road',3,.36,.41,'onsen-glenorchy');
  visit('glenorchy-lagoon',9,'Glenorchy Lagoon',[-44.85,168.39],'Take the lagoon boardwalk and stop for a picnic by the water.','12:00');
  extra('arrowtown',9,'Arrowtown',[-44.939,168.831],'Explore Arrowtown as the wet-weather alternative.','',0,.58);
  extra('queenstown-prayer',9,'Queenstown Islamic Centre',[-45.019,168.661],'Stop for prayer on Gorge Road.','',0,.28);
  extra('lake-hawea',10,'Lake Hāwea',[-44.604,169.262],'Look over Lake Hāwea on the way to the West Coast.','',0,1.9);
  extra('blue-pools',10,'Blue Pools',[-44.161,169.278],'Walk through the beech forest to the Makarora River.','',0,.66);
  visit('haast-pass',10,'Haast Pass',[-44.107,169.354],'Cross from the lake country to the West Coast, with a stop for the Blue Pools.','',0,2.4);
  visit('franz-josef-town',10,'Franz Josef / Waiau',[-43.387,170.183],'Settle into the Rainforest Retreat ahead of the morning flight.');
  clip('glacier-flight',11,'heli','Flight to the glacier',4,.22,.71);
  visit('glacier-hike',11,'Franz Josef Glacier','glacier_ice','Step onto the blue ice for the guided heli-hike.','09:00');
  extra('glacier-valley',11,'Franz Josef Glacier valley',[-43.435,170.17],'Look up the glacier valley during the afternoon walk.','',0,1.85);
  extra('franz-retreat',11,'Evening in Franz Josef',[-43.387,170.183],'Return to the retreat for an evening soak.','',.4,.4);
  extra('hokitika-gorge',12,'Hokitika Gorge',[-42.957,171.017],'Visit the gorge inland from Hokitika.','',0,.87);
  visit('hokitika-beach',12,'Hokitika waterfront',[-42.717,170.958],'Stop on the West Coast before crossing the Southern Alps.');
  visit('arthurs-pass',12,'Arthur’s Pass',[-42.94,171.56],'Take in the alpine pass on the way back to Christchurch.','',0,2.2);
  visit('akaroa-harbour',13,'Akaroa Harbour',[-43.806,172.962],'Explore the harbour before the final evening in Christchurch.','',0,1.6);
  clip('akaroa-cruise',13,'boat','Looking for Hector’s dolphins',4,.23,.34,'akaroa');
  extra('hagley-park',13,'Hagley Park',[-43.53,172.615],'Take the Christchurch park walk as an alternative to Akaroa.','',0,.61);
  extra('al-noor-return',13,'Evening at Al Noor','mosque','Return to Al Noor before the final night in Christchurch.','',.25);
  extra('airport-terminal',14,'Christchurch Airport terminal',[-43.485,172.538],'Check in and visit the landside prayer room before security.','',0,.24);
  clip('christchurch-departure',14,'plane','Leaving Christchurch',4,.10,.38);
  clip('singapore-home',14,'gstay','Home in Singapore',5);
  let elapsed=0;
  for(const chapter of chapters){chapter.start=elapsed;chapter.cut=elapsed>0;elapsed+=chapter.dur;}
  return chapters;
}

// Pick a level dry spot beside the building. Both the visitor model and the building
// use the same illustrative metre, so the vehicle is a size reference at the stop.
function parkBesideLandmark(vehicle,landmark,spec,metre,terrain,water,eye){
  const {bounds,center}=landmark,span=spec.length*metre,width=spec.width*metre;
  const gap=width+span*.4;
  const options=[[bounds.max.x+gap,center.z,0],[bounds.min.x-gap,center.z,0],
    [center.x,bounds.max.z+gap,Math.PI/2],[center.x,bounds.min.z-gap,Math.PI/2]];
  let best=null;
  for(const [x,z,angle] of options){
    const h=terrain.height(x,z),dx=Math.sin(angle),dz=Math.cos(angle);
    if(h===null||water.height(x,z)!==null)continue;
    const supports=[];
    for(const side of [-1,1])for(const end of [-1,1]){
      const px=x+end*dx*span*.40+side*dz*width*.43,pz=z+end*dz*span*.40-side*dx*width*.43;
      const y=terrain.height(px,pz);if(y!==null&&water.height(px,pz)===null)supports.push(y);
    }
    if(supports.length<4)continue;
    const slope=Math.max(...supports)-Math.min(...supports);
    const pos=new THREE.Vector3(x,h+spec.height*metre*.5,z);
    const direction=pos.clone().sub(eye).normalize();
    const hit=new THREE.Ray(eye,direction).intersectBox(bounds,new THREE.Vector3());
    const hidden=hit&&eye.distanceToSquared(hit)<eye.distanceToSquared(pos);
    const score=slope+(hidden?landmark.extent:0);
    if(!best||score<best.score)best={x,z,h,angle,score,supports};
  }
  if(!best)return false;
  const {x,z,h,angle,supports:s}=best;
  vehicle.position.set(x,h,z);vehicle.rotation.order='YXZ';vehicle.rotation.y=angle;
  vehicle.rotation.x=-Math.atan2((s[1]+s[3]-s[0]-s[2])/2,span*.8);
  vehicle.rotation.z=Math.atan2((s[2]+s[3]-s[0]-s[1])/2,width*.86);
  return true;
}

// The direction points from the landmark towards the visitor's camera.
// A low view from the south shore puts Lake Tekapo and the Alps behind the chapel.
const activityViews = {
  'tekapo-chapel': {eye:[.23,.082,1],clearance:.0007,orbit:.018},
  'wanaka-tree': {eye:[.30,.13,1],clearance:.001,orbit:.025,dusk:true},
  'onsen-sunset': {eye:[-.50,.21,-.94],clearance:.0008,orbit:.015,dusk:true},
  'tekapo-springs': {eye:[-.70,.19,.72],clearance:.001,orbit:.025},
  'mount-john': {eye:[-.48,.14,.90],clearance:.001,orbit:.025},
  'coronet-ski': {eye:[.70,.31,.72],clearance:.002,orbit:.035}
};

function makeEveningSky(){
  // Match the illustrated sky in both editions regardless of the terrain exposure.
  const skyColour=hex=>{
    const colour=new THREE.Color(hex);
    return THREE.ColorManagement.legacyMode?colour.convertSRGBToLinear():colour;
  };
  const material=new THREE.ShaderMaterial({
    side:THREE.BackSide,depthWrite:false,fog:false,toneMapped:false,
    uniforms:{horizon:{value:skyColour('#df9c7e')},zenith:{value:skyColour('#545b89')}},
    vertexShader:'varying vec3 ray; void main(){ray=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader:`uniform vec3 horizon,zenith; varying vec3 ray;
      void main(){vec3 d=normalize(ray);float h=d.y;
      vec3 color=mix(horizon,zenith,smoothstep(-.25,.20,h));
      color=mix(color,zenith*.64,.72*(1.-smoothstep(-.76,-.31,h)));
      color+=vec3(.20,.075,.022)*pow(max(0.,dot(d,normalize(vec3(-.52,.08,-.85)))),22.);
      gl_FragColor=vec4(color,1.);
      #include <tonemapping_fragment>
      #include <encodings_fragment>
      }`
  });
  const sky=new THREE.Mesh(new THREE.SphereGeometry(450,48,20),material);
  sky.renderOrder=-100;sky.visible=false;
  return sky;
}

function addShotoverRiver(lines,scene,project,terrain){
  const water=new THREE.MeshBasicMaterial({color:'#50979b',polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2});
  for(const line of lines){
    const points=line.map(([lon,lat])=>{
      const p=project(lat,lon);return new THREE.Vector3(p.x,terrain.height(p.x,p.z)??0,p.z);
    });
    const dist=[0];
    for(let i=1;i<points.length;i++)dist.push(dist[i-1]+points[i].distanceTo(points[i-1]));
    // Drape a representative forty-metre channel over the island terrain triangles.
    const path={points,dist,roadSamples:points.map((_,i)=>i)};
    const river=SurfaceTravel.ribbon(path,.00068,terrain);
    river.material.dispose();river.material=water;river.name='Shotover River';scene.add(river);
  }
}

function makeThermalPools(){
  const site=new THREE.Group();
  const mat=color=>new THREE.MeshStandardMaterial({color,roughness:.76});
  const deck=mat('#ac9173'),rim=mat('#d5c6aa'),water=mat('#68b8c0'),steel=mat('#afb9b8');
  water.roughness=.24;
  const cylinder=new THREE.CylinderGeometry(1,1,1,64);
  function oval(x,y,z,w,h,d,material){
    const mesh=new THREE.Mesh(cylinder,material);
    mesh.position.set(x,y,z);mesh.scale.set(w,h,d);site.add(mesh);
  }
  for(const [x,z,w,d,h] of [[-9,2,7,4.3,1.1],[3,-3.5,6.3,4.3,1.8],[11.7,4.2,4.8,3.4,2.5]]){
    oval(x,h/2,z,w+1.6,h,d+1.6,deck);
    oval(x,h+.13,z,w+.3,.26,d+.3,rim);
    oval(x,h+.22,z,w,.13,d,water);
    for(const offset of [-.45,.45]){
      const curve=new THREE.CatmullRomCurve3([[x+offset,h,z+d+1.1],[x+offset,h+1.15,z+d+.8],[x+offset,h+1.2,z+d],[x+offset,h+.13,z+d-.6]].map(p=>new THREE.Vector3(...p)));
      site.add(new THREE.Mesh(new THREE.TubeGeometry(curve,12,.085,6,false),steel));
    }
  }
  return site;
}

function placeTourLandmarks(fit,models,scene,project,ground,water,coarseHeight,metre,drive,shadows){
  const landmarks=new Map();
  if(!drive){
    const p=project(-43.99474,170.4613);
    const pools=makeThermalPools(),extent=50*metre;
    const obj=fit(pools,extent,'#69b9bd');
    obj.position.set(p.x,ground.height(p.x,p.z)??0,p.z);
    scene.add(obj);
    const bounds=new THREE.Box3().setFromObject(obj);
    landmarks.set('thermal_pools',{bounds,center:bounds.getCenter(new THREE.Vector3()),extent});
  }
  for(const [name,ll,original,span,color,site] of itineraryLandmarks){
    const p=project(...(!drive&&site?site:ll)),extent=drive?original:span*metre;
    const obj=fit(models[name],extent,color);
    const y=drive?coarseHeight(p.x,p.z):Math.max(ground.height(p.x,p.z)??-.018,water.height(p.x,p.z)??-.018);
    obj.position.set(p.x,y,p.z);obj.name=name;
    if(shadows)obj.traverse(m=>{if(m.isMesh){m.castShadow=true;m.receiveShadow=true;}});
    scene.add(obj);
    const bounds=new THREE.Box3().setFromObject(obj);
    landmarks.set(name,{name,bounds,center:bounds.getCenter(new THREE.Vector3()),extent});
  }
  return landmarks;
}
