/* Read the exported GLB positions and node transforms. Run with Node from any directory. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),THREE=require(path.join(root,'atlas/three-r147/three.min.js'));
const fleet=JSON.parse(fs.readFileSync(path.join(root,'atlas/vehicle-dimensions.json'))).vehicles;
for(const spec of Object.values(fleet)){
  const bytes=fs.readFileSync(path.join(root,'map3d/assets',spec.asset+'.glb'));
  const jsonLength=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+jsonLength)),bin=28+jsonLength;
  const bounds=new THREE.Box3(),point=new THREE.Vector3();
  function visit(index,parent){
    const node=doc.nodes[index],local=new THREE.Matrix4();
    if(node.matrix)local.fromArray(node.matrix);
    else local.compose(new THREE.Vector3().fromArray(node.translation||[0,0,0]),
      new THREE.Quaternion().fromArray(node.rotation||[0,0,0,1]),new THREE.Vector3().fromArray(node.scale||[1,1,1]));
    const world=new THREE.Matrix4().multiplyMatrices(parent,local);
    for(const primitive of doc.meshes[node.mesh]?.primitives||[]){
      const acc=doc.accessors[primitive.attributes.POSITION],view=doc.bufferViews[acc.bufferView];
      assert.equal(acc.componentType,5126);assert.equal(acc.type,'VEC3');
      const start=bin+(view.byteOffset||0)+(acc.byteOffset||0),stride=view.byteStride||12;
      for(let i=0;i<acc.count;i++){
        const b=start+i*stride;
        point.set(bytes.readFloatLE(b),bytes.readFloatLE(b+4),bytes.readFloatLE(b+8)).applyMatrix4(world);
        bounds.expandByPoint(point);
      }
    }
    for(const child of node.children||[])visit(child,world);
  }
  for(const node of doc.scenes[doc.scene||0].nodes)visit(node,new THREE.Matrix4());
  const size=bounds.getSize(new THREE.Vector3());
  for(const [measured,expected] of [[size.x,spec.width],[size.y,spec.height],[size.z,spec.length]])
    assert.ok(Math.abs(measured-expected)<.005,spec.label+' dimensions '+size.toArray());
  assert.ok(Math.abs(bounds.min.y)<.005,spec.label+' ground contact');
  console.log(spec.label+'  '+size.z.toFixed(2)+' m long');
}
