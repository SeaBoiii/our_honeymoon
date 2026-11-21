/* A continuous relief surface for close approaches. The geometry and vertex
   colours are the same ones used by the sampler and by the full-island view. */
function finishLandscape(root){
  const noise=`
    float atlasHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
    float atlasNoise(vec2 p){
      vec2 cell=floor(p),f=fract(p);f=f*f*(3.-2.*f);
      return mix(mix(atlasHash(cell),atlasHash(cell+vec2(1.,0.)),f.x),
                 mix(atlasHash(cell+vec2(0.,1.)),atlasHash(cell+vec2(1.)),f.x),f.y);
    }`;
  root.traverse(o=>{
    if(!o.isMesh)return;
    const lake=/lake/i.test(o.name)||/lake/i.test(o.parent?.name||'');
    if(!lake){o.geometry.computeVertexNormals();o.material.flatShading=false;}
    const m=o.material;
    m.onBeforeCompile=shader=>{
      shader.vertexShader='varying vec3 atlasWorld;\n'+shader.vertexShader.replace('#include <begin_vertex>',
        '#include <begin_vertex>\natlasWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
      const tint=lake?`
        vec2 p=atlasWorld.xz;
        float waves=atlasNoise(vec2(p.x*58.+p.y*12.,p.y*237.))*.65+atlasNoise(vec2(p.x*30.,p.y*80.))*.35;
        float soft=1.-smoothstep(.002,.017,max(fwidth(p.x),fwidth(p.y)));
        diffuseColor.rgb*=.87+soft*(waves-.5)*.21;
        diffuseColor.rgb+=vec3(.016,.03,.033)*smoothstep(.65,.86,waves)*soft;`:`
        vec2 p=atlasWorld.xz;
        float coarse=atlasNoise(p*8.2)*.65+atlasNoise(p*24.)*.35;
        float nearField=1.-smoothstep(.002,.04,max(fwidth(p.x),fwidth(p.y)));
        float grain=(atlasNoise(p*115.)-.5)*nearField;
        diffuseColor.rgb*=.93+.14*coarse+.075*grain;`;
      shader.fragmentShader='varying vec3 atlasWorld;\n'+noise+'\n'+shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\n'+tint);
    };
    m.customProgramCacheKey=()=>lake?'atlas-water-1':'atlas-ground-1';m.needsUpdate=true;
  });
}

function placeRoadsideHabitats(legs,trees,pines,flock,ground,water,west,random){
  const axis=new THREE.Vector3(0,1,0),q=new THREE.Quaternion(),size=new THREE.Vector3(),m=new THREE.Matrix4();
  for(const leg of legs){
    if(leg.mode!=='car'||![2,3,4,5,9,10,12].includes(leg.day))continue;
    const path=leg.travel;let next=1.3;
    for(let i=1;i<path.points.length-2;i++){
      if(path.dist[i]<next)continue;
      next+=.22+random()*.47;
      const a=path.points[i],b=path.points[i+1],dx=b.x-a.x,dz=b.z-a.z,l=Math.hypot(dx,dz),side=random()<.5?-1:1;
      const forest=west(a.x,a.z),isFlock=!forest&&leg.day<6&&random()<.53;
      const target=forest?trees:isFlock?flock:pines, count=isFlock?4:6;
      for(let j=0;j<count;j++){
        const beyond=side*(.006+random()*.033),along=(random()-.5)*.065;
        const x=a.x+(dx*along-dz*beyond)/l,z=a.z+(dz*along+dx*beyond)/l;
        const h=ground.height(x,z);
        if(h===null||h<.025||h>(isFlock?.33:.59)||water(x,z)>.001)continue;
        const edge=ground.height(x+.018,z+.018);
        if(edge===null||Math.abs(edge-h)>(isFlock?.012:.027))continue;
        q.setFromAxisAngle(axis,random()*Math.PI*2);size.setScalar(.62+random()*.52);
        target.push(m.compose(new THREE.Vector3(x,h,z),q,size).clone());
      }
    }
  }
}
