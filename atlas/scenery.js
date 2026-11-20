/* Keep the sculpted crowns and fleece close to the traveller. Each batch
   shares geometry and materials across every placement in that distance band. */
function makeScenery(near,far,placements){
  const group=new THREE.Group(),last=new THREE.Vector3(Infinity,Infinity,Infinity);
  const transform=new THREE.Matrix4();
  function batch(model){
    const parts=[];
    model.updateMatrixWorld(true);
    model.traverse(o=>{
      if(!o.isMesh)return;
      const mesh=new THREE.InstancedMesh(o.geometry,o.material,placements.length);
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      mesh.count=0;mesh.frustumCulled=false;group.add(mesh);
      parts.push({mesh,local:o.matrixWorld.clone()});
    });
    return parts;
  }
  const fine=batch(near),coarse=batch(far);
  group.userData.update=camera=>{
    if(last.distanceToSquared(camera)<.0025)return;
    last.copy(camera);
    const nearby=[],distant=[];
    for(const m of placements){
      const e=m.elements;
      ((camera.x-e[12])**2+(camera.y-e[13])**2+(camera.z-e[14])**2<.36?nearby:distant).push(m);
    }
    for(const [parts,items] of [[fine,nearby],[coarse,distant]]){
      for(const {mesh,local} of parts){
        items.forEach((p,i)=>mesh.setMatrixAt(i,transform.multiplyMatrices(p,local)));
        mesh.count=items.length;mesh.instanceMatrix.needsUpdate=true;
      }
    }
  };
  return group;
}
