/* Sample the production timeline declarations with the production motion code. */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const read=name=>fs.readFileSync(path.join(root,name),'utf8');
const ctx=vm.createContext({THREE:require(path.join(root,'atlas/three-r147/three.min.js'))});
const html=read('map3d/index.html');
const dataset=html.slice(html.indexOf('const SIN='),html.indexOf('const STOPS='));
ctx.routes=JSON.parse(read('map3d/web_assets/routes.json')).routes;
ctx.cruises=JSON.parse(read('atlas/cruises.json'));
vm.runInContext(read('atlas/journey.js'),ctx);
const args=`
  const rev=a=>a.slice().reverse();
  ${dataset}
  const project=([lat,lon])=>new THREE.Vector3((lon-170.5)*8.008,0,-(lat+44)*11.132);
  LEGS.filter(l=>['car','coach','boat'].includes(l[1])).map(([day,mode,path,caption])=>{
    const tr=SurfaceTravel.forLeg(mode,path,routes,cruises,project,()=>0,0,.0005);
    return {day,mode,caption,points:tr.points.map((p,i)=>[p.x,p.z,tr.yaw[i]])};
  });
`;
process.stdout.write(JSON.stringify(vm.runInContext(read('atlas/surface-travel.js')+'\n'+args,ctx)));
