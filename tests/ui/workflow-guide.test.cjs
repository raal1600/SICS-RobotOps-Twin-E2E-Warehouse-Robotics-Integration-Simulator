const test=require('node:test');
const assert=require('node:assert/strict');
const guide=require('../../apps/erp_ui/workflow-guide.js');
const base={ready:true,busy:false,archived:false,pending:null,state:null,cellMode:'READY',blocked:null,available:3,product:'RED',evidence:null};

test('only persisted verification may describe success; scene and planning observation cannot',()=>{
  const evidence={command:{command_id:'c'},journal:{status:'SUCCEEDED',effect_count:1},
    observations:[{observation_id:'planning',captured_at:'before effect',objects:[{location_id:'destination'}]}],verifications:[]};
  const summary=guide.evidenceSummary(evidence);
  assert.match(summary.journal,/This alone does not confirm/);
  assert.match(summary.observation,/No post-pick observation has been assessed/);
  const result=guide.describe({...base,pending:{state:'UNKNOWN_OUTCOME'},state:'UNKNOWN_OUTCOME',evidence,
    world:{location:'destination'},frames:[{location:'destination'}]});
  assert.equal(result.action,'review');assert.equal(result.tone,'attention');assert.match(result.title,/uncertain/);
});

for(const [reason,explanation] of [
  ['CONTRADICTORY_OBSERVATION',/conflicting locations/],['LOW_CONFIDENCE',/not confident/],
  ['STALE_OR_FUTURE_OBSERVATION',/freshness window/],['MISSING_OBSERVATION',/does not contain/],
  ['JOURNAL_UNAVAILABLE',/journal is unavailable/],['JOURNAL_IDENTITY_MISMATCH',/original command identity/],
  ['JOURNAL_OBSERVATION_CONFLICT_OR_INCOMPLETE',/disagree/],['POSE_UNCERTAINTY',/too uncertain/]
])test('explain persisted '+reason+' and keep investigation available',()=>{
  const verification={verification_id:'v2',observation_id:'o2',verdict:'INCONCLUSIVE',reason};
  const evidence={verifications:[verification],observations:[{observation_id:'o1',captured_at:'planning'}, {observation_id:'o2',captured_at:'assessed'}],
    reconciliations:[{verification,observation:{observation_id:'o2',captured_at:'assessed'}}]};
  const summary=guide.evidenceSummary(evidence);assert.match(summary.decision,explanation);
  assert.match(summary.observation,/assessed/);assert.doesNotMatch(summary.observation,/planning/);
  assert.match(summary.attempts,/1 review attempt saved/);
  const result=guide.describe({...base,pending:{state:'REQUIRES_INTERVENTION'},evidence});
  assert.equal(result.action,'review');assert.equal(result.stage,2);assert.equal(result.tone,'attention');
  assert.match(result.detail,explanation);
});

test('missing assessed record never substitutes a different observation',()=>{
  const summary=guide.evidenceSummary({verifications:[{observation_id:'missing',reason:'LOW_CONFIDENCE'}],
    observations:[{observation_id:'other',captured_at:'wrong record'}]});
  assert.match(summary.observation,/assessed observation is unavailable/);assert.doesNotMatch(summary.observation,/wrong record/);
});

test('latest repeated assessment is shown with exact capture and immutable attempt count',()=>{
  const bad={verification_id:'bad',observation_id:'o1',reason:'LOW_CONFIDENCE',verdict:'INCONCLUSIVE'};
  const good={verification_id:'good',observation_id:'o2',reason:'JOURNAL_AND_FRESH_DESTINATION_AGREE',verdict:'VERIFIED_SUCCESS'};
  const summary=guide.evidenceSummary({verifications:[bad,good],observations:[],reconciliations:[
    {verification:bad,observation:{captured_at:'first capture'}},{verification:good,observation:{captured_at:'latest capture'}}]});
  assert.match(summary.observation,/latest capture/);assert.match(summary.decision,/reached the destination/);
  assert.match(summary.attempts,/2 review attempts/);
});

test('uncertainty takes precedence over a stopped cell, exhausted inventory and success in another job',()=>{
  const result=guide.describe({...base,pending:{state:'UNKNOWN_OUTCOME'},cellMode:'FAULT',available:0,state:'COMPLETED'});
  assert.equal(result.action,'review');assert.equal(result.tone,'attention');
});

test('archived test and running operation offer no mutation or premature review',()=>{
  assert.equal(guide.describe({...base,archived:true,pending:{state:'REQUIRES_INTERVENTION'}}).action,'current');
  assert.equal(guide.describe({...base,busy:true,pending:{state:'UNKNOWN_OUTCOME'}}).action,'none');
  assert.equal(guide.describe({...base,blocked:'LEASE_HELD'}).action,'none');
});

test('proven no effect stays a failed pick; normal observation is never a promise of success',()=>{
  const evidence={command:{command_id:'c'},verifications:[{reason:'JOURNAL_AND_FRESH_SOURCE_PROVE_NO_EFFECT'}]};
  const result=guide.describe({...base,state:'FAILED',evidence});
  assert.equal(result.tone,'attention');assert.match(result.detail,/no pick effect/);
  assert.match(guide.observation(''),/still needs consistent evidence/);
});
