/* Render the continental shelf from the loaded coastline, in map coordinates.
   A quarter-resolution distance field is sufficient for the three broad depth bands. */
function shadeCoast(sea, grid, land) {
  const stride=4, pad=52;
  const cols=Math.ceil(grid.nx/stride), rows=Math.ceil(grid.nz/stride);
  const width=cols+2*pad, height=rows+2*pad;
  const distance=new Float32Array(width*height).fill(255);
  for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
    if(land[y*stride*grid.nx+x*stride]>=0)distance[(y+pad)*width+x+pad]=0;
  }
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const i=y*width+x;
    if(x)distance[i]=Math.min(distance[i],distance[i-1]+1);
    if(y)distance[i]=Math.min(distance[i],distance[i-width]+1);
    if(x&&y)distance[i]=Math.min(distance[i],distance[i-width-1]+1.414);
    if(x+1<width&&y)distance[i]=Math.min(distance[i],distance[i-width+1]+1.414);
  }
  const pixels=new Uint8Array(width*height*4);
  for(let y=height-1;y>=0;y--)for(let x=width-1;x>=0;x--){
    const i=y*width+x;
    if(x+1<width)distance[i]=Math.min(distance[i],distance[i+1]+1);
    if(y+1<height)distance[i]=Math.min(distance[i],distance[i+width]+1);
    if(x+1<width&&y+1<height)distance[i]=Math.min(distance[i],distance[i+width+1]+1.414);
    if(x&&y+1<height)distance[i]=Math.min(distance[i],distance[i+width-1]+1.414);
    pixels.set([Math.min(255,Math.round(distance[i]*5)),0,0,255],i*4);
  }
  const texture=new THREE.DataTexture(pixels,width,height);
  texture.magFilter=texture.minFilter=THREE.LinearFilter;texture.needsUpdate=true;
  sea.material.onBeforeCompile=shader=>{
    shader.uniforms.shelfDistance={value:texture};
    const step=stride*grid.step;
    shader.uniforms.shelfBounds={value:new THREE.Vector4(grid.x0-pad*step,grid.z0-pad*step,width*step,height*step)};
    shader.vertexShader='varying vec2 chartPosition;\n'+shader.vertexShader.replace('#include <begin_vertex>',
      '#include <begin_vertex>\n chartPosition=(modelMatrix*vec4(position,1.)).xz;');
    shader.fragmentShader='varying vec2 chartPosition; uniform sampler2D shelfDistance; uniform vec4 shelfBounds;\n'+
      shader.fragmentShader.replace('#include <color_fragment>',`
      #include <color_fragment>
      vec2 uvChart=(chartPosition-shelfBounds.xy)/shelfBounds.zw;
      float edge=min(min(uvChart.x,uvChart.y),min(1.-uvChart.x,1.-uvChart.y));
      float depth=mix(1.,texture2D(shelfDistance,clamp(uvChart,0.,1.)).r,smoothstep(0.,.035,edge));
      diffuseColor.rgb=mix(vec3(.24,.53,.48),vec3(.055,.20,.24),smoothstep(0.,.87,depth));
      float band=1.-smoothstep(.0,.012,abs(mod(depth+.055,.155)-.0775));
      diffuseColor.rgb+=vec3(.035,.05,.045)*band*(1.-smoothstep(.42,.74,depth));
      `);
  };
  sea.material.needsUpdate=true;
}

/* A screen-space stroke keeps the road legible at the whole-island scale.
   The tour itself still uses the elevation-following physical road meshes. */
function chartRoad(points, mode, canvas) {
  const pos=[], before=[], after=[], side=[], indices=[];
  for(let i=0;i<points.length;i++){
    for(const s of [-1,1]){
      points[i].toArray(pos,pos.length);
      points[Math.max(0,i-1)].toArray(before,before.length);
      points[Math.min(points.length-1,i+1)].toArray(after,after.length);
      side.push(s);
    }
    if(i){const j=i*2;indices.push(j-2,j-1,j,j,j-1,j+1);}
  }
  const g=new THREE.BufferGeometry();g.setIndex(indices);
  for(const [name,array,dim] of [['position',pos,3],['previous',before,3],['nextPoint',after,3],['side',side,1]]){
    g.setAttribute(name,new THREE.Float32BufferAttribute(array,dim));
  }
  const colors={car:'#a24029',coach:'#755017',boat:'#246375'};
  const road=new THREE.Group();
  for(const casing of [true,false]){
    const material=new THREE.ShaderMaterial({
      uniforms:{viewport:{value:new THREE.Vector2()},ink:{value:new THREE.Color(casing?'#fff6d9':colors[mode])},
        halfWidth:{value:casing?2.8:1.45}},depthTest:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-2,side:THREE.DoubleSide,
      vertexShader:`attribute vec3 previous,nextPoint;attribute float side;
      uniform vec2 viewport;uniform float halfWidth;
      void main(){
        mat4 mvp=projectionMatrix*modelViewMatrix;
        vec4 a=mvp*vec4(previous,1.), b=mvp*vec4(nextPoint,1.), p=mvp*vec4(position,1.);
        vec2 delta=(b.xy/b.w-a.xy/a.w)*viewport;
        vec2 dir=delta/max(length(delta),.00001);
        p.xy+=vec2(-dir.y,dir.x)*side*halfWidth*2./viewport*p.w;
        gl_Position=p;
      }`,
      fragmentShader:'uniform vec3 ink;void main(){gl_FragColor=vec4(ink,1.);}'
    });
    const mesh=new THREE.Mesh(g,material);
    mesh.renderOrder=casing?2:3;
    mesh.onBeforeRender=()=>material.uniforms.viewport.value.set(canvas.clientWidth,canvas.clientHeight);
    road.add(mesh);
  }
  return road;
}
