/* Limit concurrent GLB decoding on mobile and retry an interrupted transfer once. */
function atlasLoader(){
  const loader=new THREE.GLTFLoader(),queue=[];
  let active=0;
  async function run(job){
    active++;
    try{
      for(let attempt=0;attempt<2;attempt++){
        try{
          const response=await fetch(job.url);
          if(!response.ok)throw Error('HTTP '+response.status);
          const {data}=await response.json(),bin=atob(data),bytes=new Uint8Array(bin.length);
          for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
          const gltf=await new Promise((resolve,reject)=>loader.parse(bytes.buffer,'',resolve,reject));
          job.resolve(gltf.scene);return;
        }catch(error){if(attempt)console.warn('Could not load miniature',job.url,error.message);}
      }
      job.resolve(null);
    }finally{active--;if(queue.length)run(queue.shift());}
  }
  return (name,base='web_assets/')=>new Promise(resolve=>{
    const job={url:base+name+'.json',resolve};
    if(active<4)run(job);else queue.push(job);
  });
}

function makeVehicle(source,fleet,mode){
  const spec=fleet.vehicles[mode],group=new THREE.Group();
  if(source)group.add(source.clone(true));
  else{
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(spec.width,spec.height,spec.length),new THREE.MeshStandardMaterial({color:'#79857c'}));
    mesh.position.y=spec.height/2;group.add(mesh);
  }
  const vehicle=new THREE.Group();group.scale.setScalar(fleet.mapUnitsPerMetre);
  vehicle.add(group);return vehicle;
}
