/* Run with Node. Compare the actual road triangles and playback poses with each edition's GLB terrain. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const THREE=require(path.join(root,'atlas/three-r147/three.min.js'));
global.THREE=THREE;
require(path.join(root,'atlas/three-r147/GLTFLoader.js'));
const read=name=>fs.readFileSync(path.join(root,name));
const travel=Function('THREE',read('atlas/surface-travel.js').toString()+'\nreturn SurfaceTravel;')(THREE);
const metre=JSON.parse(read('atlas/vehicle-dimensions.json')).mapUnitsPerMetre;

function registerMesh(index,mesh){
  const geometry=mesh.geometry,positions=geometry.getAttribute('position'),indices=geometry.index?.array;
  const x=new Float32Array(positions.count),y=new Float32Array(positions.count),z=new Float32Array(positions.count);
  const p=new THREE.Vector3();
  for(let i=0;i<positions.count;i++){
    p.fromBufferAttribute(positions,i).applyMatrix4(mesh.matrixWorld);
    x[i]=p.x;y[i]=p.y;z[i]=p.z;
  }
  const register=index.mesh(x,y,z,indices),count=indices?.length??positions.count;
  for(let i=0;i<count;i+=3)register(i/3,indices?.[i]??i,indices?.[i+1]??i+1,indices?.[i+2]??i+2);
}
function verifyRidgeView(){
  const terrain=travel.terrainIndex();
  const x=new Float32Array([0,0,1,1,2,2]),y=new Float32Array([0,0,1,1,0,0]),z=new Float32Array([-1,1,-1,1,-1,1]);
  const triangles=[0,2,1,1,2,3,2,4,3,3,4,5],add=terrain.mesh(x,y,z,triangles);
  for(let i=0;i<triangles.length;i+=3)add(i/3,...triangles.slice(i,i+3));
  const start=new THREE.Vector3(0,0,0),end=new THREE.Vector3(2,0,0);
  const line=travel.groundLine([start,end],terrain);
  assert.ok(line.some(p=>Math.abs(p.x-1)<1e-8&&Math.abs(p.y-1)<1e-8),'overview must touch the ridge');
  for(let i=1;i<line.length;i++){
    const middle=line[i-1].clone().lerp(line[i],.5);
    assert.ok(Math.abs(middle.y-terrain.height(middle.x,middle.z))<1e-8,'overview stroke floats');
  }
  assert.ok(Math.abs(travel.cameraFloor(terrain,start,end,.02)-2.02)<1e-8,'camera sightline must clear the ridge');
}
async function verify(edition,asset){
  const bytes=read(edition+'/assets/'+asset+'.glb');
  const gltf=await new THREE.GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  const terrain=travel.terrainIndex();
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(mesh=>{
    if(mesh.isMesh&&!/lake/i.test(mesh.name+' '+mesh.parent.name))registerMesh(terrain,mesh);
  });
  const routes=JSON.parse(read(edition+'/web_assets/routes.json')).routes;
  const project=([lat,lon])=>new THREE.Vector3((lon-170.5)*8.008,0,-(lat+44)*11.132);
  let triangleCount=0,poseCount=0,worstGap=0;
  for(const key of Object.keys(routes)){
    const mode=key.includes('milford')?'coach':'car';
    const tr=travel.forLeg(mode,'r:'+key,routes,{},project,terrain.height,0,.0005);
    const road=travel.ribbon(tr,metre,terrain),geometry=road.geometry;
    const v=geometry.getAttribute('position'),idx=geometry.index.array;
    const pavement=travel.terrainIndex();registerMesh(pavement,road);
    function checkSurface(x,y,z){
      const ground=terrain.height(x,z);
      assert.notEqual(ground,null,key+' has pavement outside the land mesh');
      const gap=Math.abs(y-ground);
      worstGap=Math.max(worstGap,gap);
      // Float32 map coordinates have ~2 microunits of horizontal precision.
      assert.ok(gap<.000025,key+' pavement/ground separation: '+gap);
    }
    for(let i=0;i<idx.length;i+=3){
      const a=idx[i],b=idx[i+1],c=idx[i+2];
      checkSurface((v.getX(a)+v.getX(b)+v.getX(c))/3,(v.getY(a)+v.getY(b)+v.getY(c))/3,(v.getZ(a)+v.getZ(b)+v.getZ(c))/3);
      triangleCount++;
    }
    for(let i=0;i<tr.points.length-1;i++){
      const q=travel.pose(tr,(tr.time[i]+tr.time[i+1])/(2*tr.duration)).p;
      const y=pavement.height(q.x,q.z);
      assert.notEqual(y,null,key+' has a gap under the vehicle at segment '+i);
      assert.ok(Math.abs(q.y-y)<.000025,key+' vehicle/pavement separation: '+Math.abs(q.y-y));
      checkSurface(q.x,q.y,q.z);poseCount++;
    }
    geometry.dispose();road.material.dispose();
  }
  console.log(edition+': '+Object.keys(routes).length+' roads, '+triangleCount+' pavement faces, '+poseCount+' in-between poses, maximum terrain error '+worstGap.toExponential(3)+' map units.');
}
(async()=>{verifyRidgeView();await verify('map3d','terrain_south_island');await verify('map3d-claude','terrain');})().catch(e=>{console.error(e);process.exitCode=1;});
