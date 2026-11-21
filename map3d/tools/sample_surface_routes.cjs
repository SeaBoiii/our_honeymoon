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
ctx.highlights=process.argv.includes('--itinerary');
vm.runInContext(read('atlas/itinerary.js'),ctx);
const args=`
  const rev=a=>a.slice().reverse();
  ${dataset}
  const project=([lat,lon])=>new THREE.Vector3((lon-170.5)*8.008,0,-(lat+44)*11.132);
  const surface=LEGS.filter(l=>['car','coach','boat'].includes(l[1])).map(([day,mode,path,caption])=>{
    const tr=SurfaceTravel.forLeg(mode,path,routes,cruises,project,()=>0,0,.0005);
    return {day,mode,cap:caption,key:path.slice(2).split(':')[0],travel:tr};
  });
  const sites=new Map(itineraryLandmarks.map(([id])=>[id,{center:new THREE.Vector3(),extent:1}]));
  const flat={height:()=>0};
  const tracks=highlights?buildItinerary(surface,sites,(lat,lon)=>project([lat,lon]),flat,flat).filter(l=>l.travel):surface;
  tracks.map(l=>{
    const tr=l.travel,points=[];
    if(highlights){
      const endpoint=u=>{const q=SurfaceTravel.pose(tr,u);return [q.p.x,q.p.z,Math.atan2(q.d.x,q.d.z)];};
      points.push(endpoint(l.from));
      for(let i=1;i<tr.points.length-1;i++)if(tr.time[i]>l.from*tr.duration&&tr.time[i]<l.to*tr.duration)
        points.push([tr.points[i].x,tr.points[i].z,tr.yaw[i]]);
      points.push(endpoint(l.to));
      for(let i=1;i<points.length;i++){
        const delta=points[i][2]-points[i-1][2];
        points[i][2]=points[i-1][2]+Math.atan2(Math.sin(delta),Math.cos(delta));
      }
    }else tr.points.forEach((p,i)=>points.push([p.x,p.z,tr.yaw[i]]));
    return {mode:l.mode,day:l.day,caption:l.cap,points};
  });
`;
process.stdout.write(JSON.stringify(vm.runInContext(read('atlas/surface-travel.js')+'\n'+args,ctx)));
