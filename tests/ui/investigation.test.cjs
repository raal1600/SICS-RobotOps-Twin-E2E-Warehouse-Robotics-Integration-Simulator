const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const guide=require('../../apps/erp_ui/workflow-guide.js');
const evidence=()=>({job:{job_id:'job-A',order_id:'order-A',state:'UNKNOWN_OUTCOME',line:{product_id:'box-A'}},
  command:{command_id:'command-A',product_id:'box-A'},journal:{status:'SUCCEEDED',effect_count:1},
  observations:[{observation_id:'planning',objects:[{product_id:'box-A',location_id:'destination',confidence:1}]}],
  verifications:[],reconciliations:[]});
test('investigation never turns animation, hidden truth or a successful receipt into verification',()=>{
  const data={...evidence(),world:{location:'destination'},scenario:'happy_path',frames:[{productAtDestination:true}]};
  const result=guide.inspect(data);
  assert.equal(result.assessed,undefined);assert.match(result.symptom,/no confirmed result/);
  assert.match(result.finding,/has not assessed a position check/);assert.match(result.limit,/does not prove/);
  assert.doesNotMatch(result.observation,/destination/);assert.equal(result.initialFault,null);
});
test('investigation uses the exact assessed observation, including earlier captures',()=>{
  const data=evidence();data.verifications=[{verification_id:'v',observation_id:'assessed',verdict:'INCONCLUSIVE',reason:'LOW_CONFIDENCE'}];
  data.observations=[{observation_id:'assessed',model_version:'observer-v',calibration_version:'cal-v',objects:[{product_id:'box-A',location_id:'source',confidence:.3}]},...data.observations];
  const result=guide.inspect(data);
  assert.equal(result.assessed.observation_id,'assessed');assert.match(result.observation,/source \(30% confidence\)/);
  assert.doesNotMatch(result.observation,/destination/);assert.match(result.finding,/not confident/);
});
test('missing assessed record remains missing even with favorable other evidence',()=>{
  const data=evidence();data.verifications=[{verification_id:'v',observation_id:'missing',verdict:'INCONCLUSIVE',reason:'JOURNAL_UNAVAILABLE'}];
  assert.equal(guide.inspect(data).assessed,undefined);assert.match(guide.inspect(data).observation,/No assessed sensor report/);
});
test('another job fault and later review injection cannot become this execution cause',()=>{
  const events=[{job_id:'job-B',order_id:'order-A',event_type:'FAULT_INJECTED',reason:'CELL_FAULT'},
    {job_id:null,order_id:'order-A',event_type:'ORDER_RECEIVED'},
    {job_id:'job-A',event_type:'JOB_TRANSITION',state_after:'UNKNOWN_OUTCOME'},
    {job_id:'job-A',event_type:'FAULT_INJECTED',reason:'CONTRADICTORY_OBSERVATION'}];
  const result=guide.inspect(evidence(),events);
  assert.equal(result.related.length,3);assert.equal(result.initialFault,null);
  assert.ok(!result.related.some(e=>e.job_id==='job-B'));
});
test('recorded initial injection is attributed to this job and separated from hypothesis',()=>{
  const result=guide.inspect(evidence(),[{job_id:'job-A',event_type:'FAULT_INJECTED',reason:'DROP_ACK_AFTER_EFFECT'},
    {job_id:'job-A',event_type:'JOB_TRANSITION',state_after:'UNKNOWN_OUTCOME'}]);
  assert.equal(result.initialFault,'DROP_ACK_AFTER_EFFECT');assert.match(result.hypothesis,/missing reply|unavailable result check/);
  assert.match(result.limit,/sensor report/);
});
test('no effect and an uncertain result remain distinct even with a zero-effect journal',()=>{
  const data=evidence();data.journal={status:'FAILED',effect_count:0};
  assert.match(guide.inspect(data).symptom,/no confirmed result/);
  data.job.state='FAILED';data.verifications=[{verification_id:'v',observation_id:'o',verdict:'VERIFIED_FAILURE',reason:'JOURNAL_AND_FRESH_SOURCE_PROVE_NO_EFFECT'}];
  assert.match(guide.inspect(data).finding,/prove no pick effect/);
});
test('every selectable scenario has a short purpose and concrete thing to watch',()=>{
  for(const {value} of guide.choices('scenario')){
    const [purpose,watch]=guide.brief(value);assert.ok(purpose.length>20&&purpose.length<150);assert.ok(watch.length>20&&watch.length<150);
    assert.doesNotMatch(purpose,/Choose a supported scenario/);assert.doesNotMatch(watch,/No behavior is defined/);
  }
});
test('all integration scenarios explain their actual boundary rather than an unsupported operation',()=>{
  for(const [value,purpose,watch] of [
    ['DUPLICATE_DELIVERY',/original command/,/only one physical effect/],
    ['BROKER_TRANSIENT',/publication attempt/,/same command/],
    ['EDGE_TRANSIENT',/inbox confirmation/,/consumer acceptance/],
    ['OPC_UA_DISCONNECT',/before command acceptance/,/physical authorization/],
    ['PLC_RESTART',/original command/,/must not authorize another pick/],
    ['WMS_UNAVAILABLE',/outcome has been verified/,/business reconciliation only/],
  ]){const brief=guide.brief(value);assert.match(brief[0],purpose);assert.match(brief[1],watch);}
  assert.match(guide.brief('UNSUPPORTED_OPERATION')[0],/Choose a supported scenario/);
  assert.match(guide.brief('UNSUPPORTED_OPERATION')[1],/No behavior is defined/);
});
test('manual inspection points to real checked-in engineering sources',()=>{
  for(const [path] of guide.inspect(evidence()).sources)assert.ok(fs.existsSync(path),path);
});
