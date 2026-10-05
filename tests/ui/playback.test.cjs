const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function setup() {
  const elements = new Map();
  const document = {getElementById(id) {
    if (!elements.has(id)) elements.set(id, {value:0, textContent:'', hidden:false, disabled:false,
      dataset:{},setAttribute(){},getAttribute(){return '';},classList:{toggle(){}}, getContext(){return {};}});
    return elements.get(id);
  }};
  const context=vm.createContext({document,SceneView:class {constructor(canvas){this.canvas=canvas;this.views=[];}render(){}reset(){}rotate(){}zoom(){}configure(){}viewpoint(name){this.views.push(name);}},requestAnimationFrame(){},fetch(){throw Error('Playback must not dispatch');}});
  vm.runInContext(fs.readFileSync('apps/erp_ui/playback.js','utf8')+'\nglobalThis.player=new MotionPlayer();',context);
  return {player:context.player, el:id=>document.getElementById(id)};
}
function clip(count, complete=false, job='j1') {
  return {job_id:job, job_state:'UNKNOWN_OUTCOME', status:complete?'RECORDED':'RECORDING',
    scene:{source:'SAVED_START_SCENE',objects:[]},events:[],recording:{complete,objects:[],frames:Array.from({length:count},(_,i)=>({frame:i+1,phase:'TRANSFER',positions:{}})),product_id:'red'},can_import:false};
}
test('live playback waits at last received pose; pause survives incoming frames',()=>{
  const {player:p,el}=setup();p.select('j1');p.update(clip(12));
  for(let i=0;i<50;i++)p.tick(i*100);
  assert.equal(p.cursor,11);assert.equal(p.playing,true);
  el('motion-play').onclick();assert.equal(p.playing,false);
  p.update(clip(20));assert.equal(p.playing,false);assert.equal(p.cursor,11);
  el('motion-scrub').oninput({target:{value:99}});assert.equal(p.cursor,19);
});
test('replay rewinds only the view; source outcome stays unknown',()=>{
  const {player:p,el}=setup();p.select('j1');p.update(clip(100,true));
  for(let i=0;i<60;i++)p.tick(i*100);
  assert.equal(p.cursor,99);assert.equal(p.playing,false);
  el('motion-replay').onclick();assert.equal(p.cursor,0);assert.equal(p.playing,true);
  el('motion-speed').onchange({target:{value:'0.5'}});assert.equal(p.speed,0.5);
  assert.equal(el('motion-outcome').textContent,'Job: UNKNOWN_OUTCOME');
});
test('switching orders rejects late data and unavailable evidence clears motion',()=>{
  const {player:p,el}=setup();p.select('j1');p.update(clip(12));p.select('j2');p.update(clip(100,true));
  assert.equal(p.recording,null);assert.equal(el('motion-play').disabled,true);
  p.update(clip(20,false,'j2'));assert.equal(p.recording.frames.length,20);
  p.update({job_id:'j2',job_state:'FAILED',status:'UNAVAILABLE',recording:null,scene:{source:'SAVED_START_SCENE',objects:[]},events:[]});
  assert.equal(p.recording,null);assert.equal(p.playing,false);
});

test('blocked scenarios replay audit events while all physical poses remain fixed',()=>{
  for(const fault of ['LOGICAL_ESTOP','CELL_FAULT','BRAIN_TIMEOUT','BRAIN_INVALID_OUTPUT','DROP_ACK_BEFORE_EFFECT']){
    const {player:p,el}=setup();p.select('j1');
    const objects=[{name:'Robot',position:[0,0,1]},{name:'Products/red',product_id:'red',position:[-0.5,0,0.1]}];
    p.update({job_id:'j1',job_state:'FAILED',status:'UNAVAILABLE',scene:{source:'SAVED_START_SCENE',objects},recording:null,
      events:[{event_type:'FAULT_INJECTED',reason:fault},{event_type:'TRANSITION',state_after:'FAILED',reason:fault}]});
    assert.equal(el('motion-replay').disabled,false);assert.equal(el('motion-rotate').disabled,false);
    for(let i=0;i<24;i++){p.cursor=i;assert.deepEqual(p.pose().objects,objects);assert.equal(Object.keys(p.pose().positions).length,0);}
    p.draw();assert.match(el('motion-event').textContent,new RegExp(fault));
    el('motion-replay').onclick();assert.equal(p.cursor,0);assert.equal(p.playing,true);
  }
});
test('event replay brackets actual motion and freezes partial poses without inventing the endpoint',()=>{
  const {player:p,el}=setup();p.select('j1');
  const data=clip(100,true);data.events=[
    {event_type:'TRANSITION',state_after:'EXECUTING',reason:'DISPATCH_INTENT'},
    {event_type:'TRANSITION',state_after:'UNKNOWN_OUTCOME',reason:'COMMUNICATION_UNCERTAIN'}];
  data.recording.objects=[{name:'red',position:[-1,0,0]}];
  data.recording.frames.forEach((frame,i)=>{frame.positions={red:[i/99,0,0]};});
  p.update(data);p.cursor=0;assert.equal(Object.keys(p.pose().positions).length,0);
  p.cursor=62;assert.equal(p.pose().positions.red[0],50/99);
  p.cursor=p.limit();assert.equal(p.pose().positions.red[0],1);p.draw();
  assert.match(el('motion-event').textContent,/Outcome uncertain/);
  data.recording.frames=data.recording.frames.slice(0,12);data.recording.complete=false;data.status='PARTIAL';
  p.update(data);p.cursor=p.limit();assert.equal(p.pose().positions.red[0],11/99);
  assert.equal(p.track.at(-1).kind,'motion');
});
test('idle scene appears before orders and current-reference provenance is explicit',()=>{
  const {player:p,el}=setup(),scene={source:'CURRENT_WORLD_REFERENCE',objects:[{name:'Robot'}]};
  p.previewScene(scene);assert.deepEqual(p.pose().objects,scene.objects);
  p.select('legacy');p.update({job_id:'legacy',job_state:'FAILED',status:'UNAVAILABLE',recording:null,scene,events:[]});
  assert.match(el('motion-detail').textContent,/historical starting scene unavailable/);
});

test('already-picked rejection explains how to repeat the scenario without hiding the failure',()=>{
  const {player:p,el}=setup();p.select('j1');
  p.update({job_id:'j1',job_state:'FAILED',status:'UNAVAILABLE',recording:null,
    scene:{source:'SAVED_START_SCENE',objects:[]},events:[{event_type:'JOB_TRANSITION',state_after:'FAILED',reason:'PLANNING_REJECTED:SOURCE_NOT_OBSERVED'}]});
  p.draw();assert.match(el('motion-event').textContent,/Start fresh scene/);
  assert.match(el('motion-event').textContent,/No pick dispatched/);
  p.select(null);assert.equal(p.track.length,0);assert.equal(el('motion-outcome').textContent,'Current cell');
});

function deliveryClips(){
  return ['red','blue','green'].map((product,index)=>{
    const data=clip(100,true,'job-'+product);data.product_id=product;data.job_state='COMPLETED';
    data.events=[{event_type:'JOB_TRANSITION',state_after:'EXECUTING',reason:'DISPATCH_INTENT'},
      {event_type:'JOB_TRANSITION',state_after:'COMPLETED',reason:'VERIFIED_SUCCESS'}];
    data.recording.objects=['red','blue','green'].map((name,i)=>({name,position:[i<index?1:-1,0,0]}));
    data.recording.frames.forEach((frame,f)=>{frame.positions=Object.fromEntries(data.recording.objects.map(obj=>[obj.name,obj.name===product?[-1+2*f/99,0,0]:obj.position]));});
    return data;
  });
}
test('full delivery plays all three original clips with cumulative product positions and read-only replay',()=>{
  const {player:p,el}=setup(),jobs=deliveryClips();p.select('delivery:scene');
  p.updateDelivery({delivery_id:'scene',scene:jobs[0].scene,jobs,reason:'Original clips'});
  assert.equal(p.track.length,372);assert.equal(el('motion-outcome').textContent,'3/3 completed');
  for(let i=0;i<3;i++){
    p.cursor=i*124+12;let pose=p.pose();
    assert.equal(pose.data.product_id,['red','blue','green'][i]);
    for(const previous of ['red','blue','green'].slice(0,i))assert.equal(pose.positions[previous][0],1);
    p.cursor=i*124+111;assert.equal(p.pose().positions[['red','blue','green'][i]][0],1);
  }
  el('motion-replay').onclick();assert.equal(p.cursor,0);assert.equal(p.pose().data.product_id,'red');
  p.updateDelivery({delivery_id:'other',jobs:[],scene:{objects:[]}});assert.equal(p.track.length,372);
});
test('delivery stops at a partial clip and retains uncertain status; no future segment is invented',()=>{
  const {player:p,el}=setup(),jobs=deliveryClips();p.select('delivery:scene');
  jobs[1].job_state='UNKNOWN_OUTCOME';jobs[1].status='PARTIAL';jobs[1].recording.complete=false;jobs[1].recording.frames.length=20;
  p.updateDelivery({delivery_id:'scene',jobs,scene:jobs[0].scene});
  assert.equal(p.track.length,156);p.cursor=p.limit();assert.equal(p.pose().data.product_id,'blue');
  assert.equal(p.pose().positions.blue[0],-1+2*19/99);
  assert.match(el('motion-outcome').textContent,/uncertain outcome/);
});
test('paused delivery cursor stays on its product when earlier reconciliation events are appended',()=>{
  const {player:p,el}=setup(),jobs=deliveryClips();p.select('delivery:scene');
  const data={delivery_id:'scene',jobs,scene:jobs[0].scene};p.updateDelivery(data);
  el('motion-scrub').oninput({target:{value:124+62}});
  const before=p.pose().positions.blue[0];
  jobs[0].events.push({event_type:'JOB_TRANSITION',state_after:'COMPLETED',reason:'LATE_AUDIT'});
  p.updateDelivery(data);assert.equal(p.playing,false);assert.equal(p.pose().data.product_id,'blue');
  assert.equal(p.pose().positions.blue[0],before);
});


test('version 2 replay interpolates actual rotations, positions and scale without changing evidence',()=>{
  const {player:p,el}=setup();
  const q=[0,0,Math.SQRT1_2,Math.SQRT1_2];
  const object={schema_version:'2.0',name:'Robot/link',position:[0,0,0],quaternion_xyzw:[0,0,0,1],scale:[1,1,1],visible:true};
  const data=clip(2,true);data.recording.schema_version='2.0';data.recording.total_frames=2;data.recording.objects=[object];
  data.recording.frames=[
    {schema_version:'2.0',frame:1,phase:'LIFT',positions:{},sim_time_s:0,active_tool_id:'EE_VAC_ARRAY',rack_tool_ids:[],transforms:{'Robot/link':{position:[0,0,0],quaternion_xyzw:[0,0,0,1],scale:[1,1,1],visible:true}}},
    {schema_version:'2.0',frame:2,phase:'SAFE_TRANSFER',positions:{},sim_time_s:1,active_tool_id:'EE_VAC_ARRAY',rack_tool_ids:[],transforms:{'Robot/link':{position:[2,0,1],quaternion_xyzw:q,scale:[1,1,2],visible:false}}},
  ];
  const before=JSON.stringify(data);p.select('j1');p.update(data);p.cursor=.5;
  const transform=p.pose().transforms['Robot/link'];
  assert.deepEqual(Array.from(transform.position),[1,0,.5]);assert.deepEqual(Array.from(transform.scale),[1,1,1.5]);
  assert.ok(Math.abs(transform.quaternion_xyzw[2]-Math.sin(Math.PI/8))<1e-8);
  assert.ok(Math.abs(Math.hypot(...transform.quaternion_xyzw)-1)<1e-8);assert.equal(transform.visible,true);
  p.cursor=1;assert.equal(p.pose().transforms['Robot/link'].visible,false);p.draw();
  assert.match(el('motion-tool').textContent,/EE_VAC_ARRAY/);assert.equal(JSON.stringify(data),before);
});

test('camera selection, frame stepping and 4x speed change only presentation',()=>{
  const {player:p,el}=setup();p.select('j1');const data=clip(5,true);p.update(data);
  const before=JSON.stringify(data);
  for(const [id,name] of [['camera-operator','OperatorOverview'],['camera-overhead','OverheadObservation'],['camera-side','SideInspection'],['camera-follow','FollowTCP']]){
    el(id).onclick();assert.equal(p.view.views.at(-1),name);
  }
  p.cursor=2.7;el('motion-step-back').onclick();assert.equal(p.cursor,1);assert.equal(p.playing,false);
  el('motion-step-forward').onclick();assert.equal(p.cursor,2);assert.equal(p.manualPause,true);
  el('motion-speed').onchange({target:{value:'4'}});assert.equal(p.speed,4);
  assert.equal(JSON.stringify(data),before);assert.equal(data.job_state,'UNKNOWN_OUTCOME');
});

test('display refresh is bounded without slowing replay time or changing evidence',()=>{
  for(const displayHz of [60,144]){
    for(const speed of [0.25,1,4]){
      const {player:p}=setup();p.select('j1');const data=clip(250,true);p.update(data);p.speed=speed;
      const before=JSON.stringify(data);let drawings=0;p.view.render=()=>{drawings++;};
      for(let i=0;i<=displayHz;i++)p.tick(i*1000/displayHz);
      assert.ok(drawings>=24&&drawings<=25,`${displayHz} Hz rendered ${drawings} times`);
      assert.ok(Math.abs(p.cursor-24*speed)<1e-8,'one second still advances by the selected replay speed');
      assert.equal(JSON.stringify(data),before);
    }
  }
});

test('opening an investigation can freeze a replay without losing its frame or sending a command',()=>{
  const {player:p,el}=setup();p.select('j1');p.update(clip(20));p.cursor=8.5;
  p.pause();assert.equal(p.playing,false);assert.equal(p.manualPause,true);
  p.update(clip(40));p.tick(100);p.tick(200);
  assert.equal(p.cursor,8.5);assert.equal(p.job,'j1');
  el('motion-play').onclick();assert.equal(p.playing,true);assert.equal(p.cursor,8.5);
});

test('guided intake gate blocks autoplay and temporal handlers while cameras remain inspectable',()=>{
  const {player:p,el}=setup(),scene={source:'CURRENT_WORLD_REFERENCE',objects:[{name:'Robot',position:[0,0,1]}]};
  p.previewScene(scene);p.setExecutionGate(true);p.select('guided');
  const data={job_id:'guided',job_state:'QUEUED',status:'UNAVAILABLE',scene,recording:null,
    events:[{event_type:'JOB_TRANSITION',state_after:'QUEUED',reason:'WMS_TASK_ACCEPTED'}]};
  p.update(data);assert.ok(p.track.length>0);assert.equal(p.playing,false);
  const before=JSON.stringify(data);
  for(const id of ['motion-play','motion-replay','motion-scrub','motion-speed','motion-step-back','motion-step-forward'])assert.equal(el(id).disabled,true,id);
  for(const id of ['motion-play','motion-replay','motion-step-back','motion-step-forward'])el(id).onclick();
  el('motion-scrub').oninput({target:{value:11}});el('motion-speed').onchange({target:{value:4}});
  p.tick(0);p.tick(100);p.update(data);
  assert.equal(p.cursor,0);assert.equal(p.speed,1);assert.equal(p.playing,false);
  assert.deepEqual(p.pose().objects,scene.objects);assert.equal(p.pose().event,null);
  assert.equal(el('motion-state').textContent,'Physical execution not authorized');
  assert.equal(el('motion-phase').textContent,'Physical execution not authorized');
  assert.match(el('motion-event').textContent,/Static scene view/);
  for(const id of ['motion-rotate','motion-home','motion-zoom-in','motion-zoom-out'])assert.equal(el(id).disabled,false,id);
  el('camera-overhead').onclick();assert.equal(p.view.views.at(-1),'OverheadObservation');
  assert.equal(JSON.stringify(data),before);
});

test('guided gate replaces historical robot poses with the static current cell without altering evidence',()=>{
  const {player:p,el}=setup(),current={source:'CURRENT_WORLD_REFERENCE',objects:[{name:'Robot',position:[7,0,0]}]};
  p.previewScene(current);p.select('j1');const data=clip(5,true);
  data.scene.objects=[{name:'Robot',position:[-5,0,0]}];data.recording.objects=data.scene.objects;
  data.recording.frames.forEach((frame,index)=>{frame.positions={Robot:[index,0,0]};});
  p.update(data);p.cursor=2;assert.equal(p.pose().positions.Robot[0],2);
  const before=JSON.stringify(data);p.setExecutionGate(true);
  assert.equal(p.playing,false);assert.deepEqual(p.pose().objects,current.objects);
  assert.equal(Object.keys(p.pose().positions).length,0);assert.equal(Object.keys(p.pose().transforms).length,0);
  p.update(data);p.cursor=4;p.tick(0);p.tick(100);p.draw();
  assert.deepEqual(p.pose().objects,current.objects);assert.equal(Object.keys(p.pose().positions).length,0);
  assert.doesNotMatch(el('motion-event').textContent,/evaluated Blender poses/);assert.equal(el('motion-tool').textContent,'');
  assert.equal(el('motion-outcome').textContent,'Robot execution not authorized');
  assert.match(el('motion-detail').textContent,/Static scene preview while execution is unauthorized/);
  const refreshed={...current,objects:[{name:'Robot',position:[8,0,0]}]};
  p.previewScene(refreshed);assert.deepEqual(p.pose().objects,refreshed.objects);
  assert.equal(JSON.stringify(data),before);
  p.setExecutionGate(false);assert.equal(p.playing,true);assert.equal(el('motion-replay').disabled,false);
  assert.equal(el('motion-state').textContent,'Recorded 3D scenario');
  assert.equal(el('motion-outcome').textContent,'Job: UNKNOWN_OUTCOME');
  assert.match(el('motion-detail').textContent,/Original Blender poses/);
  el('motion-replay').onclick();p.tick(200);assert.ok(p.cursor>0);assert.ok(p.pose().positions.Robot[0]>0);
});

test('releasing the guided gate preserves an existing manual pause and enables explicit replay',()=>{
  const {player:p,el}=setup();p.select('j1');p.update(clip(20,true));p.pause();
  p.setExecutionGate(true);p.update(clip(40,true));p.setExecutionGate(false);
  assert.equal(p.playing,false);assert.equal(p.manualPause,true);assert.equal(el('motion-play').disabled,false);
  el('motion-play').onclick();assert.equal(p.playing,true);
});

function realSceneTypes(){
  const context=vm.createContext({fetch(){throw Error('Presentation must not send commands or capture evidence');}});
  vm.runInContext(fs.readFileSync('apps/erp_ui/scene-view.js','utf8')+'\nglobalThis.types={SceneView,SoftwareSceneView};',context);
  return context.types;
}

function softwareCanvas(){
  const points=[];
  const drawing={fillRect(){},beginPath(){},moveTo(...point){points.push(point);},lineTo(){},stroke(){},closePath(){},fill(){},fillText(){},measureText(){return {width:0};}};
  return {points,canvas:{width:1000,height:600,getContext(){return drawing;},addEventListener(){}}};
}

test('actual camera presets widen presentation projection and reset without changing sensor metadata',()=>{
  const {SceneView,SoftwareSceneView}=realSceneTypes(),{canvas}=softwareCanvas();
  const cameras=[
    {name:'Camera/OperatorOverview',position:[3.7,-4.7,3.4],target:[0,0,.55],sensor_id:'operator-overview',calibration_version:'hkm-cal-1'},
    {name:'Camera/OverheadObservation',position:[0,0,2.6],target:[0,0,.18],sensor_id:'overhead-observation',calibration_version:'hkm-cal-1'},
    {name:'Camera/SideInspection',position:[-1.85,-.65,1.25],target:[0,0,.18],sensor_id:'side-inspection',calibration_version:'hkm-cal-1'},
  ];
  const before=JSON.stringify(cameras);
  let updates=0;
  const view=Object.create(SceneView.prototype);
  view.fallback=new SoftwareSceneView(canvas);
  view.camera={position:{set(){}},fov:42,updateProjectionMatrix(){updates++;}};
  view.controls={target:{set(){}},update(){}};
  view.configure(cameras);
  for(const [preset,fov] of [['OverheadObservation',84],['SideInspection',84],['OperatorOverview',42],['SideInspection',84],['FollowTCP',42]]){
    const prior=updates;view.viewpoint(preset);
    assert.equal(view.camera.fov,fov);assert.equal(view.fallback.fov,fov);
    assert.equal(updates,prior+1);assert.equal(view.following,preset==='FollowTCP');
  }
  view.viewpoint('OverheadObservation');view.reset();
  assert.equal(view.camera.fov,42);assert.equal(view.fallback.fov,42);assert.equal(view.following,false);
  assert.equal(JSON.stringify(cameras),before);
});

test('software projection uses vertical field of view and redraws when only framing changes',()=>{
  const {SoftwareSceneView}=realSceneTypes(),{canvas,points}=softwareCanvas();
  const view=new SoftwareSceneView(canvas),camera={position:[0,0,2.6],target:[0,0,.18]};
  view.viewpoint(camera,42);view.render([],{},null);
  const narrow=points[0],drawn=points.length;
  view.viewpoint(camera,84);view.render([],{},null);
  assert.ok(points.length>drawn,'a framing-only change invalidates the render cache');
  const wide=points[drawn],focalLength=canvas.height/(2*Math.tan(84*Math.PI/360));
  assert.ok(Math.abs(wide[0]-(canvas.width/2-2*focalLength/2.71))<1e-9);
  assert.ok(Math.abs(wide[1]-(canvas.height/2-2*focalLength/2.71))<1e-9);
  assert.ok(narrow[1]<0,'the old narrow overhead frame crops the cell floor');
  assert.ok(wide[1]>0&&wide[1]<canvas.height,'the wider frame includes the floor');
  assert.deepEqual(camera,{position:[0,0,2.6],target:[0,0,.18]});
});
