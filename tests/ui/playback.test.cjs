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
  const context=vm.createContext({document,SceneView:class {constructor(canvas){this.canvas=canvas;}render(){}reset(){}rotate(){}zoom(){}},requestAnimationFrame(){},fetch(){throw Error('Playback must not dispatch');}});
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
