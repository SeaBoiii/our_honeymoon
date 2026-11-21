/* Browser integration check. Supply Playwright via NODE_PATH and serve docs at ATLAS_URL. */
const assert=require('node:assert/strict');
const {chromium}=require('playwright-core');

async function tourAudit(){
  // Exercise the production frame loop with a deterministic display clock. Draw each
  // leg once with WebGL, then update matrices between frames for projection checks.
  const enqueue=window.requestAnimationFrame,render=renderer.render,delta=clock.getDelta;
  window.requestAnimationFrame=()=>{};
  let shouldRender=false;
  renderer.render=function(worldScene,cam){
    if(shouldRender)render.call(this,worldScene,cam);
    else cam.updateMatrixWorld();
  };
  clock.getDelta=()=>1/24;
  const tracked=new Set(),errors=[];
  const check=(ok,message)=>{if(!ok&&errors.length<10)errors.push(message);};
  let minPlane=Infinity,frames=0;
  try{
    follow=true;started=true;t=0;curLeg=-1;setPlaying(true);
    while(playing&&frames<40000){
      const last=curLeg;shouldRender=last<0||t+1/24>=legs[last].start+legs[last].dur&&!tracked.has(last+1);
      frame();frames++;
      const leg=legs[curLeg],id=leg.day+' '+leg.mode+' at '+t.toFixed(2);
      tracked.add(curLeg);
      if(leg.world==='nz'){
        const floor=terrainSurface.height(camera.position.x,camera.position.z)??-.02;
        check(camera.position.y>=floor-1e-5,'camera below ground '+id);
      }
      if(/stay/.test(leg.mode)){check(!active,'vehicle persisted at stop '+id);continue;}
      check(active&&active.visible,'missing vehicle '+id);
      if(!active)continue;
      active.updateWorldMatrix(true,true);
      const center=active.position.clone().project(camera);
      check([center.x,center.y,center.z,...active.quaternion.toArray()].every(Number.isFinite),'invalid pose '+id);
      check(Math.abs(center.x)<.97&&Math.abs(center.y)<.97&&Math.abs(center.z)<1,'vehicle offscreen '+id);
      if(leg.mode==='gfly'){
        const size=MODE.plane.len*active.scale.x*canvas.clientHeight/(2*camera.position.distanceTo(active.position)*Math.tan(camera.fov*Math.PI/360));
        minPlane=Math.min(minPlane,size);check(size>=30,'airliner too small '+id);
      }
      if(leg.travel){
        check(!$('route-inset').hidden,'missing destination '+id);
        if(!leg.travel.boat)check(Math.abs(active.position.y-terrainSurface.height(active.position.x,active.position.z))<.000025,'lost road contact '+id);
      }
    }
    check(t===TOTAL&&!playing,'playback did not end');
    // Exact seeks across both scene boundaries and the first road junction.
    for(const i of [1,2,3,36,37,3]){
      const l=legs[i];t=l.start+.55*l.dur;curLeg=-1;shouldRender=true;frame();
      const q=active.position.clone().project(camera);
      check(active.visible&&Math.max(Math.abs(q.x),Math.abs(q.y))<.9,'seek missed '+l.mode);
    }
  }finally{renderer.render=render;clock.getDelta=delta;window.requestAnimationFrame=enqueue;setPlaying(false);}
  return {frames,legs:tracked.size,seconds:TOTAL,errors,minPlane};
}

(async()=>{
  const opts={args:['--enable-unsafe-swiftshader','--use-angle=swiftshader']};
  if(process.env.CHROMIUM_PATH)opts.executablePath=process.env.CHROMIUM_PATH;
  const browser=await chromium.launch(opts),base=process.env.ATLAS_URL||'http://127.0.0.1:8796';
  try{
    for(const cut of ['3d','claude-cut']){
      const page=await browser.newPage({viewport:process.env.MOBILE?{width:390,height:844}:{width:1180,height:760}});
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
      await page.route('**/'+cut+'/',async route=>{
        const response=await route.fetch(),body=await response.text();
        await route.fulfill({contentType:'text/html; charset=utf-8',body:body.replace('  buildTimeline();','  buildTimeline(); window.tourAudit='+tourAudit.toString()+';')});
      });
      await page.goto(base+'/'+cut+'/');
      await page.waitForFunction(()=>window.tourAudit&&document.querySelector('#status').hidden,null,{timeout:120000});
      const result=await page.evaluate(()=>window.tourAudit());
      assert.deepEqual([...errors,...result.errors],[]);assert.equal(result.legs,39);
      console.log(cut,result.frames+' animation frames, '+result.legs+' legs, '+Math.round(result.seconds)+' seconds, globe plane ≥'+Math.round(result.minPlane)+' px');
      await page.close();
    }
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
