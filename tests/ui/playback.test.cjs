const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function setup() {
  const elements = new Map();
  const document = {getElementById(id) {
    if (!elements.has(id)) elements.set(id, {value:0, textContent:'', hidden:false, disabled:false,
      classList:{toggle(){}}, getContext(){return {};}});
    return elements.get(id);
  }};
  const context=vm.createContext({document,requestAnimationFrame(){},fetch(){throw Error('Playback must not dispatch');}});
  vm.runInContext(fs.readFileSync('apps/erp_ui/playback.js','utf8')+'\nMotionPlayer.prototype.draw=function(){};globalThis.player=new MotionPlayer();',context);
  return {player:context.player, el:id=>document.getElementById(id)};
}
function clip(count, complete=false, job='j1') {
  return {job_id:job, job_state:'UNKNOWN_OUTCOME', status:complete?'RECORDED':'RECORDING',
    recording:{complete,frames:Array.from({length:count},(_,i)=>({frame:i+1})),product_id:'red'},can_import:false};
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
  p.update({job_id:'j2',job_state:'FAILED',status:'UNAVAILABLE',recording:null});
  assert.equal(p.recording,null);assert.equal(p.playing,false);
});
