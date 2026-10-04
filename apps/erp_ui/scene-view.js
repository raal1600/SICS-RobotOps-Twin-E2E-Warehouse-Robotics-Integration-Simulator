"use strict";
// Both renderers consume the same meshes/poses. Neither can send robot commands.
function rotateVector([x,y,z],[qx,qy,qz,qw]=[0,0,0,1]) {
  const tx=2*(qy*z-qz*y),ty=2*(qz*x-qx*z),tz=2*(qx*y-qy*x);
  return [x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx];
}
class SoftwareSceneView {
  constructor(canvas) {
    this.canvas=canvas; this.ctx=canvas.getContext("2d"); this.reset();
    let drag=null;
    canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY,e.button];canvas.setPointerCapture(e.pointerId);};
    canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};
    canvas.oncontextmenu=e=>e.preventDefault();
    canvas.onpointermove=e=>{
      if(!drag)return;
      const dx=e.clientX-drag[0],dy=e.clientY-drag[1];
      if(drag[2]===2 || e.shiftKey){this.pan[0]+=dx;this.pan[1]+=dy;}
      else{this.yaw-=dx*0.008;this.pitch=Math.max(0.15,Math.min(1.45,this.pitch+dy*0.008));}
      drag=[e.clientX,e.clientY,drag[2]];
    };
    canvas.addEventListener("wheel",e=>{e.preventDefault();this.distance=Math.max(2,Math.min(9,this.distance*Math.exp(e.deltaY*0.001)));},{passive:false});
  }
  reset(){this.yaw=-1.05;this.pitch=0.58;this.distance=5;this.pan=[0,0];this.target=[0,0,0.5];this.fov=42;}
  viewpoint(camera,fov=42){
    const delta=camera.position.map((v,i)=>v-camera.target[i]);
    this.yaw=Math.atan2(delta[1],delta[0]);this.pitch=Math.atan2(delta[2],Math.hypot(delta[0],delta[1]));
    this.distance=Math.hypot(...delta);this.target=[...camera.target];this.pan=[0,0];this.fov=fov;
  }
  rotate(){this.yaw+=Math.PI/6;}
  zoom(factor){this.distance=Math.max(2,Math.min(9,this.distance*factor));}
  render(objects,positions,product,transforms={}) {
    const key=JSON.stringify([objects,positions,transforms,product,this.yaw,this.pitch,this.distance,this.pan,this.target,this.fov]);
    if(key===this.lastRender)return;
    this.lastRender=key;
    const c=this.ctx,w=this.canvas.width,h=this.canvas.height;
    c.fillStyle="#112630";c.fillRect(0,0,w,h);
    const cy=Math.cos(this.yaw),sy=Math.sin(this.yaw),cp=Math.cos(this.pitch),sp=Math.sin(this.pitch);
    const view=([x,y,z])=>{x-=this.target[0];y-=this.target[1];z-=this.target[2];return [-sy*x+cy*y,-sp*cy*x-sp*sy*y+cp*z,this.distance-cp*cy*x-cp*sy*y-sp*z];};
    const focalLength=h/(2*Math.tan(this.fov*Math.PI/360));
    const project=p=>{const [x,y,z]=view(p);return [w/2+x*focalLength/z+this.pan[0],h/2-y*focalLength/z+this.pan[1]];};
    const line=(a,b)=>{c.beginPath();c.moveTo(...project(a));c.lineTo(...project(b));c.stroke();};
    c.lineWidth=1;c.strokeStyle="#2b4651";
    for(let n=-8;n<=8;n++){line([n/4,-2,-0.11],[n/4,2,-0.11]);line([-2,n/4,-0.11],[2,n/4,-0.11]);}
    const faces=[];
    for(const o of objects){
      const t=transforms[o.name]||{};
      if((t.visible??o.visible)===false)continue;
      const p=t.position||positions[o.name]||o.position,scale=t.scale||o.scale||[1,1,1],s=o.size.map((v,i)=>v*scale[i]/2),q=t.quaternion_xyzw||o.quaternion_xyzw;
      let local=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]];
      let topology=[[0,1,2,3],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0],[4,7,6,5]];
      if(o.primitive==="cylinder"){
        local=[-1,1].flatMap(z=>Array.from({length:16},(_,i)=>[Math.cos(i*Math.PI/8),Math.sin(i*Math.PI/8),z]));
        topology=[Array.from({length:16},(_,i)=>i),Array.from({length:16},(_,i)=>i+16),...Array.from({length:16},(_,i)=>[i,(i+1)%16,(i+1)%16+16,i+16])];
      }
      const vertices=local.map(v=>rotateVector(v.map((a,i)=>a*s[i]),q).map((a,i)=>p[i]+a));
      topology.forEach((indices,i)=>{
        const points=indices.map(n=>vertices[n]);
        faces.push({base:o.name==="RobotOpsTwin/Cell",points,depth:points.reduce((n,p)=>n+view(p)[2],0)/points.length,color:o.color,opacity:o.opacity??1,shade:[0.5,0.8,0.9,0.7,0.75,1.2][i%6],selected:!!product&&o.product_id===product});
      });
    }
    faces.sort((a,b)=>Number(b.base)-Number(a.base)||b.depth-a.depth);
    for(const f of faces){
      c.globalAlpha=f.opacity;
      c.beginPath();f.points.forEach((p,i)=>i?c.lineTo(...project(p)):c.moveTo(...project(p)));c.closePath();
      c.fillStyle=`rgb(${f.color.map(v=>Math.min(255,Math.round(v*255*f.shade))).join(",")})`;c.fill();
      c.lineWidth=f.selected?2:0.5;c.strokeStyle=f.selected?"#ffdf83":"#18333d";c.stroke();
    }
    c.globalAlpha=1;
    for(const o of objects){
      if((transforms[o.name]?.visible??o.visible)===false)continue;
      const label=o.label||(o.name==="SourceTote"?"SOURCE":o.name==="DestinationTote"?"DESTINATION":o.product_id===product?product:null);
      if(!label)continue;
      const p=[...(transforms[o.name]?.position||positions[o.name]||o.position)];p[2]+=o.product_id?0.2:0.03;if(!o.product_id)p[1]-=0.5;
      const [x,y]=project(p);c.font="bold 14px system-ui";c.textAlign="center";
      c.fillStyle="#112630e8";c.fillRect(x-c.measureText(label).width/2-8,y-18,c.measureText(label).width+16,26);
      c.fillStyle=o.product_id?"#ffdf83":"#c5dfe6";c.fillText(label,x,y);
    }
  }
}

class SceneView {
  constructor(canvas){
    this.canvas=canvas;this.fallback=new SoftwareSceneView(canvas);this.meshes=new Map();this.labels=[];
    this.objectsKey="";this.ready=this.initialize();
  }
  async initialize(){
    try {
      const T=await import("/ui/vendor/three.module.min.js");
      const {OrbitControls}=await import("/ui/vendor/OrbitControls.js");
      const canvas=document.createElement("canvas");
      canvas.id=this.canvas.id;canvas.width=1000;canvas.height=600;canvas.tabIndex=0;
      canvas.setAttribute("role","img");canvas.setAttribute("aria-label","Interactive 3D warehouse cell");
      const renderer=new T.WebGLRenderer({canvas,antialias:true,alpha:false});
      renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
      renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
      this.T=T;this.renderer=renderer;
      this.scene=new T.Scene();this.scene.background=new T.Color("#112630");
      this.camera=new T.PerspectiveCamera(42,5/3,0.05,40);this.camera.up.set(0,0,1);
      this.controls=new OrbitControls(this.camera,canvas);this.controls.enableDamping=true;
      this.controls.addEventListener("change",()=>{this.dirty=true;});
      this.controls.minDistance=2;this.controls.maxDistance=9;this.controls.maxPolarAngle=Math.PI*0.48;
      this.reset();
      this.scene.add(new T.HemisphereLight(0xe4f5ff,0x254553,2.6));
      const light=new T.DirectionalLight(0xffffff,3.2);light.position.set(1,-2,5);light.castShadow=true;
      light.shadow.mapSize.set(1024,1024);light.shadow.camera.left=-2;light.shadow.camera.right=2;
      light.shadow.camera.top=2;light.shadow.camera.bottom=-2;light.shadow.bias=-0.001;this.scene.add(light);
      const floor=new T.Mesh(new T.PlaneGeometry(8,8),new T.MeshStandardMaterial({color:0x182f39,roughness:1}));
      floor.position.z=-0.105;floor.receiveShadow=true;this.scene.add(floor);
      const grid=new T.GridHelper(8,32,0x496572,0x2d4651);grid.rotation.x=Math.PI/2;grid.position.z=-0.103;this.scene.add(grid);
      this.canvas.replaceWith(canvas);this.canvas=canvas;
      canvas.addEventListener("webglcontextlost",e=>{e.preventDefault();this.useFallback();});
      document.getElementById("motion-renderer").textContent="3D · orbit, pan and zoom";
    } catch(error){this.useFallback();}
  }
  useFallback(){
    if(this.renderer){
      this.controls.dispose();this.renderer.dispose();this.renderer=null;
      const canvas=document.createElement("canvas");canvas.id=this.canvas.id;canvas.width=1000;canvas.height=600;canvas.tabIndex=0;
      canvas.setAttribute("role","img");this.canvas.replaceWith(canvas);this.canvas=canvas;
      this.fallback=new SoftwareSceneView(canvas);
    }
    document.getElementById("motion-renderer").textContent="Software 3D · orbit, pan and zoom";
  }
  reset(){
    this.following=false;
    this.fallback.reset();
    if(this.cameras?.length){this.viewpoint("OperatorOverview");return;}
    if(this.controls){this.camera.fov=42;this.camera.updateProjectionMatrix();this.camera.position.set(2.4,-3.3,2.5);this.controls.target.set(0,0,0.6);this.controls.update();}
  }
  configure(cameras){
    const key=JSON.stringify(cameras||[]);
    if(this.cameraKey===key)return;
    this.cameraKey=key;this.cameras=cameras||[];this.reset();
  }
  viewpoint(name){
    this.following=name==="FollowTCP";
    const chosen=this.cameras?.find(camera=>camera.name==="Camera/"+name)||this.cameras?.[0];
    if(!chosen)return;
    // Sensor locations are useful presentation presets, not pixel/sensor evidence.
    const fov=name==="OverheadObservation"||name==="SideInspection"?84:42;
    this.fallback.viewpoint(chosen,fov);
    if(this.controls){
      this.camera.fov=fov;this.camera.updateProjectionMatrix();
      this.camera.position.set(...chosen.position);this.controls.target.set(...chosen.target);
      this.controls.maxPolarAngle=Math.PI*0.499;this.controls.update();this.dirty=true;
    }
  }
  rotate(){
    this.fallback.rotate();
    if(this.renderer){const offset=this.camera.position.clone().sub(this.controls.target);offset.applyAxisAngle(new this.T.Vector3(0,0,1),Math.PI/6);this.camera.position.copy(this.controls.target).add(offset);this.controls.update();}
  }
  zoom(factor){
    this.fallback.zoom(factor);
    if(this.renderer){const offset=this.camera.position.clone().sub(this.controls.target);offset.setLength(Math.max(2,Math.min(9,offset.length()*factor)));this.camera.position.copy(this.controls.target).add(offset);this.controls.update();}
  }
  label(text,color){
    const T=this.T,canvas=document.createElement("canvas");canvas.height=64;
    const c=canvas.getContext("2d");c.font="bold 30px system-ui";canvas.width=Math.ceil(c.measureText(text).width)+36;
    c.fillStyle="#112630df";c.fillRect(0,0,canvas.width,64);
    c.fillStyle=color;c.font="bold 30px system-ui";c.textAlign="center";c.fillText(text,canvas.width/2,43);
    const sprite=new T.Sprite(new T.SpriteMaterial({map:new T.CanvasTexture(canvas),depthTest:false,transparent:true}));
    sprite.scale.set(canvas.width/64*0.13,0.13,1);sprite.renderOrder=10;this.scene.add(sprite);return sprite;
  }
  render(objects,positions,product,transforms={}){
    if(this.following){
      const tcp=transforms["Robot/ActiveTool"]?.position||transforms["Robot/ToolChanger"]?.position||objects.find(o=>o.name==="Robot/ToolChanger")?.position;
      if(tcp){
        this.fallback.target=[...tcp];this.fallback.distance=2.4;
        if(this.controls){const offset=this.camera.position.clone().sub(this.controls.target).setLength(2.4);this.controls.target.set(...tcp);this.camera.position.copy(this.controls.target).add(offset);this.dirty=true;}
      }
    }
    if(!this.renderer){this.fallback.render(objects,positions,product,transforms);return;}
    const T=this.T,key=JSON.stringify([objects,product]);
    if(key!==this.objectsKey){
      for(const mesh of this.meshes.values()){this.scene.remove(mesh);mesh.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});}
      for(const {sprite} of this.labels){this.scene.remove(sprite);sprite.material.map.dispose();sprite.material.dispose();}
      this.meshes.clear();this.labels=[];this.objectsKey=key;this.dirty=true;
      for(const o of objects){
        const selected=!!product&&o.product_id===product;
        const geometry=o.primitive==="cylinder"?new T.CylinderGeometry(0.5,0.5,1,16).rotateX(Math.PI/2).scale(...o.size):new T.BoxGeometry(...o.size);
        const opacity=o.opacity??1;
        const mesh=new T.Mesh(geometry,new T.MeshStandardMaterial({color:new T.Color(...o.color),roughness:0.6,metalness:o.product_id?0:0.25,opacity,transparent:opacity<1,depthWrite:opacity===1}));
        mesh.castShadow=true;mesh.receiveShadow=true;
        mesh.add(new T.LineSegments(new T.EdgesGeometry(mesh.geometry),new T.LineBasicMaterial({color:selected?0xffdc83:0x23414a})));
        this.meshes.set(o.name,mesh);this.scene.add(mesh);
        const text=o.label||(o.name==="SourceTote"?"SOURCE":o.name==="DestinationTote"?"DESTINATION":selected?product:null);
        if(text)this.labels.push({name:o.name,product:selected,sprite:this.label(text,selected?"#ffdc83":"#d2e8ed")});
      }
    }
    const poseKey=JSON.stringify([positions,transforms]);
    if(this.poseKey!==poseKey){this.poseKey=poseKey;this.dirty=true;}
    for(const o of objects){
      const mesh=this.meshes.get(o.name),t=transforms[o.name]||{};
      mesh.position.set(...(t.position||positions[o.name]||o.position));
      mesh.quaternion.set(...(t.quaternion_xyzw||o.quaternion_xyzw||[0,0,0,1]));
      mesh.scale.set(...(t.scale||o.scale||[1,1,1]));
      mesh.visible=(t.visible??o.visible)!==false;
    }
    for(const label of this.labels){label.sprite.visible=this.meshes.get(label.name).visible;label.sprite.position.copy(this.meshes.get(label.name).position);label.sprite.position.z+=label.product?0.23:0.03;if(!label.product)label.sprite.position.y-=0.51;}
    const w=this.canvas.clientWidth||1000,h=w*0.6;
    if(this.width!==w){this.width=w;this.renderer.setSize(w,h,false);this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.dirty=true;}
    this.controls.update();
    if(this.dirty){this.renderer.render(this.scene,this.camera);this.dirty=false;}
  }
}
