const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function setup(){
  const elements=new Map(),requests=[],timers=[];
  const element=()=>({textContent:'',value:'',hidden:false,disabled:false,children:[],dataset:{},
    classList:{toggle(){}},setAttribute(){},append(...items){this.children.push(...items);},
    replaceChildren(...items){this.children=items;},scrollIntoView(){}});
  const document={createElement:element,getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);}};
  const context=vm.createContext({document,setTimeout(fn){const timer={fn,cancelled:false};timers.push(timer);return timer;},clearTimeout(timer){timer.cancelled=true;}});
  context.options={request(path,body){
    assert.equal(body,undefined,'live presentation must never issue a mutation');
    return new Promise((resolve,reject)=>requests.push({path,resolve,reject}));
  },path:value=>value,readOnly:()=>false,update(){},physical(){},activity(){}};
  vm.runInContext(fs.readFileSync('apps/erp_ui/integration-console.js','utf8')+'\nglobalThis.consoleView=new IntegrationConsole(options);',context);
  return {view:context.consoleView,el:id=>document.getElementById(id),requests,timers};
}
const session=(id,command,stage=16)=>({session_id:id,command_id:command,job_id:'job-'+command,revision:1,
  current_stage:stage,status:stage===22?'COMPLETED':'WAITING_AUTHORIZATION',context:{physical_authorized:stage>=16},steps:[]});
const flush=()=>new Promise(setImmediate);

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
