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
  ['hot_tub',[-44.985,168.66],.20,12,'#a86'],
  ['ski_lift',[-44.92,168.745],.40,155,'#ddd'],
  ['glacier_ice',[-43.505,170.30],.60,320,'#cdeffa']
];

function fullDriveRequested(){
  const mode=new URLSearchParams(location.search).get('tour');
  return mode==='drive'||(!mode&&location.hash.startsWith('#leg-'));
}

function buildItinerary(full,landmarks,project,terrain,water){
  const chapters=[];
  function visit(day,title,where,cap,clock='',night=0,distance=.9){
    let at;
    if(typeof where==='string'){
      const landmark=landmarks.get(where);
      at=landmark.center.clone();
      distance=landmark.extent*2.85;
    }else{
      const p=project(...where);
      at=new THREE.Vector3(p.x,Math.max(terrain.height(p.x,p.z)??-.018,water.height(p.x,p.z)??-.018),p.z);
    }
    chapters.push({day,title,at,site:typeof where==='string'?where:null,cap,clock,night,
      viewDistance:distance,mode:'stay',world:'nz',dur:8});
  }
  function clip(day,mode,title,seconds,from=0,to=1,key){
    const leg=full.find(l=>l.day===day&&l.mode===mode&&(!key||l.key===key));
    if(leg)chapters.push({...leg,title,dur:seconds,from,to,viewDistance:mode==='boat'?.55:undefined});
  }
  clip(0,'gstay','Changi Airport',4);
  clip(0,'gfly','Singapore to the South Island',5,.20,.66);
  clip(1,'plane','Arriving in Christchurch',4,.69,.98);
  visit(1,'Al Noor Mosque','mosque','After collecting the car, stop for Dhuhr in Riccarton.','13:00');
  visit(1,'Christchurch Botanic Gardens',[-43.530,172.620],'Walk beside the Avon before dinner in Riccarton.');
  visit(2,'Church of the Good Shepherd','church_stone','Walk the Lake Tekapo foreshore to the stone chapel.');
  visit(2,'Mount John after dark','observatory','After the hot pools at Tekapo Springs, head up to Mount John for the stars.','21:30',.83);
  clip(3,'car','Lake Pukaki road',3,.44,.49,'twizel-mtcook');
  visit(3,'Hooker Valley','hooker_valley','Follow the walking track and look up the valley towards Aoraki.','11:30');
  visit(4,'That Wānaka Tree','lone_tree','Spend sunset on the lakefront after the crossing of Lindis Pass.','17:40',.30);
  clip(5,'boat','Crossing Lake Te Anau',4,.35,.48,'te-anau');
  visit(5,'Te Anau Glowworm Caves','glowworm_cave','Leave the daylight at the cave entrance for the silent glowworm grotto.','17:15',.35);
  clip(6,'coach','Eglinton Valley',3,.26,.30,'teanau-milford');
  visit(6,'Milford Sound / Piopiotahi',[-44.641,167.891],'From the head of the fiord, look across the water towards Mitre Peak.','',0,2.7);
  clip(6,'boat','Milford Sound cruise',5,.06,.14,'milford');
  visit(7,'Queenstown lakefront',[-45.033,168.659],'Walk the waterfront, then find dinner in town.','18:30',.24,1.15);
  visit(8,'Coronet Peak','ski_lift','The morning is for a first ski lesson.','10:00');
  visit(8,'Onsen at Arthurs Point','hot_tub','Soak in a cedar tub above the Shotover River as the sun goes down.','17:45',.48);
  clip(9,'car','The Glenorchy lake road',3,.36,.41,'onsen-glenorchy');
  visit(9,'Glenorchy Lagoon',[-44.85,168.39],'Take the lagoon boardwalk and stop for a picnic by the water.','12:00');
  visit(10,'Haast Pass',[-44.107,169.354],'Cross from the lake country to the West Coast, with a stop for the Blue Pools.','',0,2.4);
  visit(10,'Franz Josef / Waiau',[-43.387,170.183],'Settle into the Rainforest Retreat ahead of the morning flight.');
  clip(11,'heli','Flight to the glacier',4,.22,.71);
  visit(11,'Franz Josef Glacier','glacier_ice','Step onto the blue ice for the guided heli-hike.','09:00');
  visit(12,'Hokitika waterfront',[-42.717,170.958],'Stop on the West Coast before crossing the Southern Alps.');
  visit(12,'Arthur’s Pass',[-42.94,171.56],'Take in the alpine pass on the way back to Christchurch.','',0,2.2);
  visit(13,'Akaroa Harbour',[-43.806,172.962],'Explore the harbour before the final evening in Christchurch.','',0,1.6);
  clip(13,'boat','Looking for Hector’s dolphins',4,.23,.34,'akaroa');
  clip(14,'plane','Leaving Christchurch',4,.10,.38);
  clip(14,'gstay','Home in Singapore',5);
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

function placeTourLandmarks(fit,models,scene,project,ground,water,coarseHeight,metre,drive,shadows){
  const landmarks=new Map();
  for(const [name,ll,original,span,color,site] of itineraryLandmarks){
    const p=project(...(!drive&&site?site:ll)),extent=drive?original:span*metre;
    const obj=fit(models[name],extent,color);
    const y=drive?coarseHeight(p.x,p.z):Math.max(ground.height(p.x,p.z)??-.018,water.height(p.x,p.z)??-.018);
    obj.position.set(p.x,y,p.z);obj.name=name;
    if(shadows)obj.traverse(m=>{if(m.isMesh){m.castShadow=true;m.receiveShadow=true;}});
    scene.add(obj);
    const bounds=new THREE.Box3().setFromObject(obj);
    landmarks.set(name,{bounds,center:bounds.getCenter(new THREE.Vector3()),extent});
  }
  return landmarks;
}
