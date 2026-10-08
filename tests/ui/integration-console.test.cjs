const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function setup(){
  const elements=new Map(),requests=[],timers=[];
  const element=()=>({textContent:'',value:'',hidden:false,disabled:false,children:[],dataset:{},
    attributes:{},classList:{toggle(){}},setAttribute(k,v){this.attributes[k]=v;},append(...items){this.children.push(...items);},
    replaceChildren(...items){this.children=items;},scrollIntoView(){},focus(){this.focused=true;}});
  const document={createElement:element,getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);}};
  const context=vm.createContext({document,crypto:{randomUUID:()=>"request-1"},URL,location:{href:"http://localhost/",protocol:"http:"},setTimeout(fn){const timer={fn,cancelled:false};timers.push(timer);return timer;},clearTimeout(timer){timer.cancelled=true;}});
  context.options={request(path,body){
    assert.equal(body,undefined,'live presentation must never issue a mutation');
    return new Promise((resolve,reject)=>requests.push({path,resolve,reject}));
  },path:value=>value,readOnly:()=>false,update(){},physical(){},activity(){}};
  vm.runInContext(fs.readFileSync('apps/erp_ui/integration-console.js','utf8')+'\nglobalThis.consoleView=new IntegrationConsole(options);',context);
  return {view:context.consoleView,el:id=>document.getElementById(id),requests,timers,context};
}
const session=(id,command,stage=16)=>({session_id:id,command_id:command,job_id:'job-'+command,revision:1,
  current_stage:stage,status:stage===22?'COMPLETED':'WAITING_AUTHORIZATION',context:{physical_authorized:stage>=16},steps:[]});
const flush=()=>new Promise(setImmediate);

const inspection=(stepId, marker='CURRENT')=>({session_id:'run',step_id:stepId,read_at:'2026-10-08T00:00:00Z',session_revision:20,
  source_catalog:[{key:'entry',label:'Saved entry',path:'robotops/workflow/engine.py',symbol:'Engine'},
    {key:'plc',label:'Virtual PLC',path:'robotops/lab/opcua.py',symbol:'VirtualPLC.start'}],
  source_scope:'Current implementation, not a call trace.',protocol:{protocol:'OPC UA',classification:'REAL PROTOCOL',scope:'Saved evidence',input:{},facts:[{field:'wire.result',value:marker}]},
  records:{items:[],unresolved_selected_ids:[]},related_steps:[]});

test('engineering reads reject stale steps and mismatched identities without any mutation',async()=>{
  const {view,el,requests}=setup();view.accept(saved());view.tab='Protocol';view.inspect();
  assert.equal(requests.length,1);assert.match(requests[0].path,/step-8\/inspection$/);
  view.selectStep(view.session.steps[0]);assert.equal(requests.length,2);
  requests[0].resolve(inspection('step-8','STALE'));await flush();
  assert.equal(view.engineeringDocument.status,'loading');
  requests[1].resolve(inspection('step-5'));await flush();
  assert.equal(view.engineeringDocument.step_id,'step-5');
  assert.equal(el('integration-inspector').hidden,true);
  assert.equal(el('integration-engineering').hidden,false);
  const refresh=view.loadEngineering(true);requests[2].resolve(inspection('wrong-step'));await refresh;
  assert.equal(view.engineeringDocument.status,'unavailable');
  assert.match(el('integration-engineering-status').textContent,/another step/);
  view.tab='Source';view.inspect();
  assert.match(el('integration-source-catalog-status').textContent,/unavailable.*Full Python file.*retry/);
  const retry=view.loadEngineering();
  assert.equal(view.engineeringDocument.status,'loading');
  requests[3].resolve(inspection('step-5'));await retry;
  assert.equal(view.engineeringDocument.status,'available');
  assert.match(el('integration-source-catalog-status').textContent,/Choose one/);
});

test('Full Python file always shows the component selector and Saved excerpt hides it',async()=>{
  const {view,el,requests}=setup();const state=saved();state.steps[1].source={path:'robotops/workflow/engine.py',symbol:'Engine',excerpt:'saved snippet'};view.accept(state);
  const cached=view.loadEngineering();requests[0].resolve(inspection('step-8'));await cached;
  view.tab='Source';view.inspect();
  assert.equal(el('integration-source-browser').hidden,true);
  const full=el('integration-source-full').onclick();
  assert.equal(el('integration-source-browser').hidden,false);
  assert.equal(el('integration-source-select').disabled,false);
  assert.equal(requests.length,2,'the cached catalog needs no second read');
  requests[1].resolve({path:state.steps[1].source.path,status:'available',content:'FULL CODE'});await full;
  el('integration-source-excerpt').onclick();
  assert.equal(el('integration-source-browser').hidden,true);
  assert.equal(el('integration-inspector').textContent,'saved snippet');
});

test('Full Python file keeps a disabled selector during loading and retries failed catalog reads',async()=>{
  const {view,el,requests}=setup();const state=saved();state.steps[1].source={path:'robotops/workflow/engine.py',symbol:'Engine',excerpt:'saved snippet'};view.accept(state);view.tab='Source';
  const full=el('integration-source-full').onclick();
  assert.equal(el('integration-source-browser').hidden,false);
  assert.equal(el('integration-source-select').disabled,true);
  requests[0].resolve({path:state.steps[1].source.path,status:'available',content:'FULL CODE'});
  requests[1].reject(Error('Catalog unavailable'));await full;
  assert.equal(el('integration-source-browser').hidden,false);
  assert.equal(el('integration-inspector').textContent,'FULL CODE');
  assert.match(el('integration-source-catalog-status').textContent,/Full Python file to retry/);
  const retry=el('integration-source-full').onclick();
  requests[2].resolve({path:state.steps[1].source.path,status:'available',content:'FULL CODE'});
  requests[3].resolve(inspection('step-8'));await retry;
  assert.equal(el('integration-source-select').disabled,false);
  assert.equal(el('integration-source-select').children.length,2);
});

test('related source uses catalog keys and a late component response cannot replace the selected file',async()=>{
  const {view,el,requests}=setup();const state=saved();state.steps[1].source={path:'robotops/workflow/engine.py',symbol:'Engine',excerpt:'class Engine:'};view.accept(state);
  const catalog=view.loadEngineering();requests[0].resolve(inspection('step-8'));await catalog;
  view.tab='Source';const old=view.loadSourceFile('plc');const current=view.loadSourceFile('entry');
  assert.match(requests[1].path,/source\?component=plc$/);
  requests[2].resolve({path:'robotops/workflow/engine.py',status:'available',content:'CURRENT FILE'});await current;
  requests[1].resolve({path:'robotops/lab/opcua.py',status:'available',content:'OLD PLC FILE'});await old;
  assert.equal(el('integration-inspector').textContent,'CURRENT FILE');
  assert.equal(view.sourceDocument.component,'entry');
});

test('related code highlights only its range, preserves copied text, and clears on missing range or saved excerpt',async()=>{
  const {view,el,requests}=setup();const state=saved();state.steps[1].source={path:'robotops/workflow/engine.py',symbol:'Engine',excerpt:'saved excerpt'};view.accept(state);
  const cached=view.loadEngineering();requests[0].resolve(inspection('step-8'));await cached;
  view.tab='Source';const reading=view.loadSourceFile('plc');
  const content='import os\nclass VirtualPLC:\n    def start(self):\n        return "<img src=x>"\n\ndef unrelated():\n    return 0\n';
  requests[1].resolve({path:'robotops/lab/opcua.py',symbol:'VirtualPLC',symbol_kind:'class',status:'available',content,symbol_start_line:2,symbol_end_line:4});await reading;
  assert.equal(el('integration-inspector').children.map(n=>n.textContent).join(''),content);
  const highlights=el('integration-inspector').children.filter(n=>n.className?.includes('source-related-line'));
  assert.deepEqual(highlights.map(n=>n.dataset.sourceLine),[2,3,4]);
  assert.match(el('integration-source-highlight-label').textContent,/VirtualPLC.*lines 2–4/);
  el('integration-source-excerpt').onclick();
  assert.equal(el('integration-source-highlight').hidden,true);
  assert.equal(el('integration-inspector').textContent,'saved excerpt');
  const missing=view.loadSourceFile('plc');requests[2].resolve({path:'robotops/lab/opcua.py',status:'available',content,symbol_start_line:null,symbol_end_line:null});await missing;
  assert.equal(el('integration-inspector').children.filter(n=>n.className?.includes('source-related-line')).length,0);
  assert.match(el('integration-source-highlight-label').textContent,/location is unavailable/);
});

test('new physical consent reveals a current-command placeholder, never the previous protocol response',async()=>{
  const {view,el,requests}=setup();view.accept(session('old-session','old-command',22));
  requests[0].resolve({command_id:'old-command',events:[{value:'OLD_PROTOCOL_EVENT'}]});await flush();
  assert.match(el('integration-protocol-live').textContent,/OLD_PROTOCOL_EVENT/);
  view.accept(session('new-session','new-command',15));
  assert.equal(el('integration-live').hidden,true);
  assert.doesNotMatch(el('integration-protocol-live').textContent,/old-command|OLD_PROTOCOL_EVENT/);
  view.accept({...session('new-session','new-command'),revision:2});
  assert.equal(el('integration-live').hidden,false);
  assert.match(el('integration-protocol-live').textContent,/Waiting.*new-command/);
  requests[1].resolve({command_id:'new-command',events:[{value:'NEW_PROTOCOL_EVENT'}]});await flush();
  assert.match(el('integration-protocol-live').textContent,/NEW_PROTOCOL_EVENT/);
  assert.doesNotMatch(el('integration-protocol-live').textContent,/old-command|OLD_PROTOCOL_EVENT/);
});

for(const nextSession of ['same-session','other-session'])for(const staleError of [false,true]){
  test(`late ${staleError?'error':'response'} cannot alter ${nextSession} command or release its active poll`,async()=>{
    const {view,el,requests,timers}=setup();view.accept(session('same-session','command-1'));
    view.accept({...session(nextSession,'command-2'),revision:2});
    assert.equal(requests.length,2);assert.equal(view.pollingLive,true);
    if(staleError)requests[0].reject(Error('OLD_COMMAND_ERROR'));
    else requests[0].resolve({command_id:'command-1',events:[{value:'OLD_COMMAND_EVENT'}]});
    await flush();
    assert.equal(view.pollingLive,true);assert.equal(timers.length,0);
    assert.match(el('integration-protocol-live').textContent,/Waiting.*command-2/);
    requests[1].resolve({command_id:'command-2',events:[]});await flush();
    assert.equal(view.pollingLive,false);assert.equal(timers.length,1);
    assert.match(el('integration-protocol-live').textContent,/command-2/);
    assert.doesNotMatch(el('integration-protocol-live').textContent,/command-1|OLD_COMMAND/);
  });
}

test('a mismatched live response is unavailable evidence and clear invalidates outstanding reads',async()=>{
  const {view,el,requests,timers}=setup();view.accept(session('same-session','current-command'));
  requests[0].resolve({command_id:'different-command',events:[{value:'UNRELATED_EVENT'}]});await flush();
  assert.match(el('integration-protocol-live').textContent,/unavailable for command current-command/);
  assert.doesNotMatch(el('integration-protocol-live').textContent,/UNRELATED_EVENT|different-command/);
  timers[0].fn();assert.equal(requests.length,2);view.clear();
  requests[1].resolve({command_id:'current-command',events:[{value:'LATE_AFTER_CLEAR'}]});await flush();
  assert.equal(el('integration-live').hidden,true);assert.equal(view.pollingLive,false);
  assert.equal(el('integration-protocol-live').textContent,'No protocol evidence loaded for this session.');
  assert.equal(timers.length,1);
});

const step=(stage,sequence=stage,output={})=>({stage,sequence,step_id:`step-${sequence}`,job_id:'job-command',command_id:'command',title:`Stage ${stage}`,status:'COMPLETED',component:'workflow',protocol:'SQL',classification:'REAL CODE',input:{command_id:'command'},output,evidence_ids:[`evidence-${sequence}`],state_before:'READY',state_after:'READY'});
const saved=(stage=10,revision=20)=>({...session('run','command',stage),revision,context:{},steps:[step(5),step(8)],pending_authorization:{stage,title:`Stage ${stage}`,label:'Publish command',expected_revision:revision}});

test('historical inspection stays pinned through newer WebSocket revisions and Follow current clears filters without work',()=>{
  const {view,el,requests,context}=setup();
  context.WebSocket=class{constructor(){this.close=()=>{};}};
  view.accept(saved());view.watch();
  assert.equal(el('integration-follow').textContent,'Latest step selected');
  assert.equal(el('integration-follow').disabled,true);
  assert.equal(el('integration-follow-mobile').disabled,true);
  el('integration-events').children[0].children[0].onclick();
  assert.equal(view.selected.stage,5);assert.equal(view.pinned,true);
  assert.equal(el('integration-follow').textContent,'Follow latest step');
  assert.equal(el('integration-follow').disabled,false);
  el('integration-search').value='not present';el('integration-search').oninput();
  const newer={...saved(11,22),steps:[step(5),step(8),step(10)]};
  view.socket.onmessage({data:JSON.stringify({session:newer})});
  assert.equal(view.selected.stage,5);assert.equal(view.session.current_stage,11);
  assert.match(el('integration-position').textContent,/Step 11/);
  assert.match(el('integration-inspection-position').textContent,/historical.*step 11/);
  view.socket.onmessage({data:JSON.stringify(saved(9,19))});
  assert.equal(view.session.revision,22);
  el('integration-follow').onclick();
  assert.equal(view.pinned,false);assert.equal(view.selected.stage,10);
  assert.equal(el('integration-follow').disabled,true);
  assert.equal(el('integration-search').value,'');assert.equal(requests.length,0);
});

test('execution authorization always uses current backend stage and revision while inspection remains pinned',async()=>{
  const {view,el}=setup();view.accept(saved());view.selectStep(view.session.steps[0]);
  const mutations=[];view.request=async(path,body)=>{mutations.push({path,body});return {...saved(11,22),steps:[step(5),step(8),step(10)]};};
  await el('integration-advance').onclick();
  assert.equal(mutations.length,1);assert.equal(mutations[0].body.stage,10);assert.equal(mutations[0].body.expected_revision,20);
  assert.equal(view.selected.stage,5);assert.equal(view.session.current_stage,11);
});

test('phase, perspective, protocol and repeated-delivery filters only select saved evidence',()=>{
  const {view,el,requests}=setup();view.accept({...saved(12),steps:[step(5),step(8),step(11,11,{redelivery:{deliveries:2,redelivered:true}})]});
  el('integration-map').children[3].children[0].onclick();
  assert.equal(view.selected.stage,11);assert.equal(el('integration-events').children.length,1);
  el('integration-repeat-filter').value='repeated';el('integration-repeat-filter').oninput();
  assert.match(el('integration-events').children[0].children[0].children.at(-1).textContent,/Deliveries 2.*broker redelivery/);
  el('integration-perspective').value='business';el('integration-perspective').oninput();
  assert.equal(el('integration-events').children.length,0);
  assert.match(el('integration-position').textContent,/Step 12/);
  el('integration-reset-filters').onclick();
  assert.equal(el('integration-events').children.length,3);assert.equal(requests.length,0);
});

test('inspection links use the historical job, and JSON-shaped markup is rendered as text',()=>{
  const {view,el}=setup();const historical={...step(8),job_id:'older-job',summary:'<img src=x onerror=alert(1)>'};
  view.accept({...saved(),steps:[historical,step(5,9)]});view.selectStep(historical);
  assert.equal(el('integration-evidence').href,'/jobs/older-job/evidence');
  assert.ok(el('integration-overview').children.some(item=>item.textContent===historical.summary));
  el('integration-tabs').children.find(item=>item.textContent==='Raw JSON').onclick();
  assert.match(el('integration-inspector').textContent,/<img/);assert.equal(el('integration-payload').open,true);
});

test('Source renders the saved Python excerpt with real newlines and loads the full file read-only',async()=>{
  const {view,el,requests}=setup();
  const source={path:'robotops/workflow/engine.py',symbol:'Engine.stage_observe',excerpt:'    def stage_observe(self, job_id):\n        return "<not-html>"'};
  view.accept({...saved(),steps:[{...step(5),source}]});
  el('integration-tabs').children.find(item=>item.textContent==='Source').onclick();
  assert.equal(el('integration-inspector').textContent,source.excerpt);
  assert.match(el('integration-source-identity').textContent,/engine.py\nEngine.stage_observe/);
  assert.equal(el('integration-source').hidden,false);
  assert.equal(el('integration-payload').open,true);
  assert.equal(requests.length,0);
  const loading=el('integration-source-full').onclick();
  assert.equal(requests[0].path,'/integration/sessions/run/steps/step-5/source');
  requests[0].resolve({...source,status:'available',content:'import os\n\n'+source.excerpt,line_count:4,excerpt_start_line:3,scope:'Current application file, not a snapshot.',displayed_sha256:'abc'});
  requests[1].resolve(inspection('step-5'));
  await loading;
  assert.equal(el('integration-inspector').textContent,'import os\n\n'+source.excerpt);
  assert.match(el('integration-source-note').textContent,/Current application file.*not a snapshot/);
  assert.match(el('integration-source-note').textContent,/line 3/);
  el('integration-source-excerpt').onclick();
  assert.equal(el('integration-inspector').textContent,source.excerpt);
  el('integration-tabs').children.find(item=>item.textContent==='Raw JSON').onclick();
  assert.equal(JSON.parse(el('integration-inspector').textContent).source.excerpt,source.excerpt);
  assert.equal(el('integration-source').hidden,true);
});

test('a late full-file response cannot replace another stage and unavailable files preserve saved code',async()=>{
  const {view,el,requests}=setup();
  const older={...step(5),source:{path:'robotops/workflow/engine.py',symbol:'Engine.stage_observe',excerpt:'OLD_CODE'}};
  const newer={...step(8),source:{path:'robotops/workflow/store.py',symbol:'Store.prepare',excerpt:'NEW_CODE'}};
  view.accept({...saved(),steps:[older,newer]});view.selectStep(older);
  el('integration-tabs').children.find(item=>item.textContent==='Source').onclick();
  const pending=el('integration-source-full').onclick();view.selectStep(newer);
  requests[0].resolve({path:older.source.path,status:'available',content:'OLD_FULL_FILE'});requests[1].resolve(inspection('step-5'));await pending;
  assert.equal(el('integration-inspector').textContent,'NEW_CODE');
  const missing=el('integration-source-full').onclick();requests[2].reject(Error('Source service unavailable'));requests[3].resolve(inspection('step-8'));await missing;
  assert.match(el('integration-source-note').textContent,/unavailable/);
  el('integration-source-excerpt').onclick();assert.equal(el('integration-inspector').textContent,'NEW_CODE');
});

test('missing and mismatched replay stay unavailable; controller or replay success does not set proof',()=>{
  const {view,el}=setup();view.accept(saved());
  view.replayEvidence({job_id:'job-command',command_id:'command',status:'UNAVAILABLE',reason:'Headless runtime'});
  assert.match(el('integration-replay-evidence').textContent,/UNAVAILABLE.*No recorded Blender motion.*Headless/);
  view.replayEvidence({job_id:'different-job',command_id:'different-command',recording:{complete:true}});
  assert.match(el('integration-replay-evidence').textContent,/No matching replay/);
  view.replayEvidence({job_id:'job-command',command_id:'command',recording:{complete:true}});
  assert.match(el('integration-replay-evidence').textContent,/RECORDED.*does not prove verification/);
  assert.equal(el('integration-proofs').children.length,0);
});


test('a late authorization reply cannot restore a cleared view or trigger physical dispatch',async()=>{
  const {view}=setup();view.accept({...saved(15),pending_authorization:{stage:15,label:'AUTHORIZE ROBOT EXECUTION'}});
  let reply;const mutations=[];view.request=(path,body)=>{mutations.push({path,body});return new Promise(resolve=>{reply=resolve;});};
  const running=view.advance();view.clear();reply({...saved(16,22),context:{physical_authorized:true}});await running;
  assert.equal(view.session,null);assert.equal(mutations.length,1);assert.equal(mutations[0].body.stage,15);
});
