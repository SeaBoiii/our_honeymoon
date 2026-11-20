/* Studio lighting and framing for the same exported objects used on the route. */
const atlasPlaces = [
  {key:'valley', asset:'hooker_valley', day:3, title:'Hooker Valley', location:'Aoraki / Mount Cook',
   text:'A timber swing bridge crosses the glacial river beneath the snowline.', color:'#d4e4db', angle:[2.5,4.1,7.5]},
  {key:'chapel', asset:'church_stone', day:2, title:'The stone chapel', location:'Lake Tekapo',
   text:'Schist walls, a small belfry and a standing-seam roof on the lakeshore.', color:'#d9e4d0', angle:[-3.7,2,-4]},
  {key:'cruise', asset:'boat', day:6, title:'Into the fiord', location:'Milford Sound',
   text:'Follow the cruise from the wharf, past Mitre Peak and out towards the Tasman Sea.', color:'#cfe5e8', angle:[3.7,2.5,-4.4]},
  {key:'helicopter', asset:'helicopter', day:11, title:'Above the glacier', location:'Franz Josef',
   text:'The morning helicopter carries us up from the West Coast to the blue ice.', color:'#e9dfca', angle:[4.5,2,-3]}
];

function makeMiniatureStudio() {
  const stage=new THREE.Scene();
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
      controls.minDistance=1.05;controls.maxDistance=9;controls.maxPolarAngle=Math.PI*.49;
      controls.enablePan=false;controls.target.set(0,size.y*scale*.48,0);
      const dist=Math.max(3.55,3.3/camera.aspect);
      camera.position.fromArray(place.angle).normalize().multiplyScalar(dist).add(controls.target);
      controls.update();
    }
  };
}
