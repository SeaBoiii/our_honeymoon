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
        float coarse=atlasNoise(p*5.3)*.6+atlasNoise(p*24.)*.4;
        float detail=1.-smoothstep(.002,.04,max(fwidth(p.x),fwidth(p.y)));
        float grain=atlasNoise(p*128.)*.60+atlasNoise(p*380.)*.40;
        float height=atlasWorld.y;
        float plain=smoothstep(2.,7.,p.x)*(1.-smoothstep(-2.,1.,p.y))*(1.-smoothstep(.16,.33,height));
        // Riccarton and the airport suburbs are urban gardens on the plains.
        float suburb=1.-smoothstep(.45,.78,distance(p,vec2(16.56,-5.42)));
        plain*=1.-suburb;
        vec2 uvField=mat2(.956,-.292,.292,.956)*p*vec2(11.,7.);
        vec2 parcel=floor(uvField),boundary=min(fract(uvField),1.-fract(uvField));
        float field=atlasHash(parcel);
        float hedge=1.-smoothstep(.012,.042,min(boundary.x,boundary.y));
        vec3 pasture=mix(vec3(.28,.39,.135),vec3(.67,.58,.31),field)*(.94+.13*grain);
        diffuseColor.rgb=mix(diffuseColor.rgb,pasture,plain*.58);
        diffuseColor.rgb*=1.-hedge*.29*plain*detail;
        float folds=atlasNoise(vec2(p.x*33.+p.y*13.,p.y*5.))*.62+grain*.38;
        diffuseColor.rgb*=.76+.32*coarse+detail*((grain-.5)*.26+(folds-.5)*.19);
        float outcrop=smoothstep(.48,.86,height)*smoothstep(.48,.85,folds);
        diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.42,.43,.38),outcrop*.31);`;
      shader.fragmentShader='varying vec3 atlasWorld;\n'+noise+'\n'+shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\n'+tint);
    };
    m.customProgramCacheKey=()=>lake?'atlas-water-1':'atlas-ground-2';m.needsUpdate=true;
  });
}
