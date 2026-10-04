const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

async function dashboard({hkm=false,empty=false,profiles=null}={}){
  const hkmCatalogue=JSON.parse(fs.readFileSync('robotops/robotics/catalogue-v1.json','utf8'));
  const registeredProfiles=profiles||[{cell_profile_id:'hkm_inspired_v1',display_name:'HKM1800-inspired warehouse cell',description:'Six product families and six interchangeable tools.',selectable:true,product_count:6,tool_count:6},{cell_profile_id:'legacy_cartesian_v1',display_name:'Legacy Cartesian cell',description:'Saved historical tests only.',selectable:false,product_count:3,tool_count:1}];
  const elements=new Map(),posts=[],requests=[],worlds=new Map(),failures=[],managementResults=new Map();
  let active=empty?null:'original',sequence=0,worldNumber=0;
  const makeWorld=(id,profile=hkm?'hkm_inspired_v1':'legacy_cartesian_v1')=>{
    const catalogue=profile==='legacy_cartesian_v1'?null:hkmCatalogue;
    const sources=catalogue?Object.fromEntries(catalogue.products.map(p=>['product-'+p.sku+'-01',catalogue.layout.sources[p.sku].location_id])):{};
    return {id,number:++worldNumber,cell_profile_id:profile,cell_display_name:profile==='legacy_cartesian_v1'?'Legacy Cartesian cell':registeredProfiles.find(p=>p.cell_profile_id===profile)?.display_name,
      catalogue,sources,destination:catalogue?.layout.destination.location_id||'destination',orders:[],groups:[{delivery_id:id+'-scene-1',started_at:'2026-10-03T14:00:00Z',current:true,executions:[]}],epoch:1,cellMode:'READY',blocked:null,
      inventory:catalogue?catalogue.products.map(p=>({product_id:'product-'+p.sku+'-01',location_id:sources['product-'+p.sku+'-01']})):['red','blue','green'].map(color=>({product_id:'product-'+color,location_id:'source'}))};
  };
  if(active)worlds.set(active,makeWorld(active));
  const initial=active?worlds.get(active):{orders:[],groups:[],inventory:[]};
  const history=()=>({active_test_id:active,tests:[...worlds.values()].map(w=>({test_id:w.id,number:w.number,active:w.id===active,order_count:w.orders.length,outcomes:w.orders.map(o=>o.status),cell_profile_id:w.cell_profile_id,cell_display_name:w.cell_display_name}))});
  const makeElement=id=>({value:id==='replay-scope'?'delivery':'',textContent:'',disabled:false,hidden:false,open:false,options:[],children:[],
    add(option){this.options.push(option);if(this.options.length===1)this.value=option.value;},
    replaceChildren(...nodes){this.options=[];this.children=[];this.value='';for(const node of nodes){if('value' in node&&'text' in node)this.add(node);else this.children.push(node);}},
    addEventListener(event,fn){this['on'+event]=fn;},showModal(){this.open=true;this.hidden=false;},close(){this.open=false;this.onclose?.();},
    attributes:{},classList:{toggle(){}},focus(){this.focusCount=(this.focusCount||0)+1;},
    append(...nodes){this.children.push(...nodes);},setAttribute(key,value){this.attributes[key]=value;},getAttribute(key){return this.attributes[key]||'';},removeAttribute(key){delete this.attributes[key];},closest(){return this;},scrollIntoView(){this.scrolled=true;}});
  const el=id=>{if(!elements.has(id))elements.set(id,makeElement(id));return elements.get(id);};
  const player={select(id){this.selected=id;},previewScene(scene){this.scene=scene;},update(data){this.data=data;},updateDelivery(data){this.data=data;}};
  const reply=(data,status=200)=>({ok:status<400,status,json:async()=>JSON.parse(JSON.stringify(data))});
  async function fetch(path,options={}){
    const body=options.body?JSON.parse(options.body):null,originalPath=path;
    requests.push({path,method:options.method||'GET',body});
    if(options.method==='POST')posts.push({path,body});
    const failIndex=failures.findIndex(f=>f.path===path),failure=failIndex<0?null:failures.splice(failIndex,1)[0];
    if(failure&&!failure.afterCommit)return reply({reason:failure.reason},failure.status);
    const respond=data=>failure?reply({reason:failure.reason},failure.status):reply(data);
    if(path==='/cell-profiles')return reply({default_cell_profile_id:'hkm_inspired_v1',profiles:registeredProfiles});
    if(path==='/simulation-tests'){
      if(!body)return reply(history());
      const key=path+':'+body.request_id;
      if(managementResults.has(key))return respond(managementResults.get(key));
      if(!registeredProfiles.some(p=>p.cell_profile_id===body.cell_profile_id&&p.selectable))return reply({reason:'CELL_PROFILE_NOT_AVAILABLE'},422);
      active=body.request_id;worlds.set(active,makeWorld(active,body.cell_profile_id));
      const result=history().tests.find(t=>t.test_id===active);managementResults.set(key,result);return respond(result);
    }
    const deletion=path.match(/^\/simulation-tests\/([^/]+)\/delete$/);
    if(path==='/simulation-tests/clear'||deletion){
      const key=path+':'+body.request_id;
      if(managementResults.has(key))return respond(managementResults.get(key));
      const ids=deletion?[deletion[1]]:[...worlds.keys()];
      if(!deletion&&JSON.stringify([...body.expected_test_ids].sort())!==JSON.stringify([...worlds.keys()].sort()))return reply({reason:'TEST_HISTORY_CHANGED'},409);
      if(ids.some(id=>!worlds.has(id)))return reply({reason:'TEST_NOT_FOUND'},404);
      ids.forEach(id=>worlds.delete(id));if(ids.includes(active))active=null;
      const result={deleted_test_ids:ids,cleanup_pending:false,history:history()};managementResults.set(key,result);return respond(result);
    }
    let data,status=200;
    const match=path.match(/^\/simulation-tests\/([^/]+)(\/.*)$/),id=match?match[1]:'original';
    if(match)path=match[2];
    const world=worlds.get(id);
    if(!world)return reply({reason:'TEST_NOT_FOUND'},404);
    const {orders,groups,inventory,catalogue,sources}=world;
    if(body&&id!==active)return reply({reason:'TEST_ARCHIVED_READ_ONLY'},409);
    const scene=()=>({scene_epoch:id+'-scene-'+world.epoch,source:'CURRENT_WORLD_REFERENCE',objects:[]});
    const fixture=()=>({runtime:'headless',scene_epoch:scene().scene_epoch,source_id:catalogue?sources[inventory[0].product_id]:'source',destination_id:world.destination,
      robot_profile_version:catalogue?world.cell_profile_id:null,products:inventory.map(item=>({product_id:item.product_id,sku:catalogue?item.product_id.slice(8,-3):item.product_id})),catalogue,product_sources:sources,inventory,scene_reset_blocked_reason:world.blocked});
    if(path==='/orders'&&body){
      data={...body,job_ids:['job-'+orders.length],status:'RECEIVED'};orders.push(data);
    }else if(path==='/orders')data=orders;
    else if(path==='/fixtures')data=fixture();
    else if(path==='/cell')data={mode:world.cellMode};
    else if(path==='/cell/reset'){world.cellMode='READY';data={mode:'READY'};}
    else if(path==='/cell/scene')data=scene();
    else if(path==='/deliveries')data=groups;
    else if(path==='/fixtures/fresh-scene'){
      if(world.blocked){status=409;data={reason:world.blocked};}
      else{groups.forEach(group=>{group.current=false;});world.epoch++;groups.push({delivery_id:scene().scene_epoch,started_at:'2026-10-03T14:00:00Z',current:true,executions:[]});inventory.forEach(item=>{item.location_id=sources[item.product_id]||'source';});world.cellMode='READY';data=scene();}
    }else if(path.startsWith('/deliveries/')&&path.endsWith('/playback')){
      const group=groups.find(item=>path.includes('/'+item.delivery_id+'/'));
      data={...group,scene:scene(),jobs:group.executions.map(item=>({job_id:item.job_id,job_state:item.state,status:'UNAVAILABLE'}))};
    }else if(path.startsWith('/jobs/')){
      const order=orders.find(item=>path.includes('/'+item.job_ids[0]+'/'));
      if(path.endsWith('/run')){
        order.fault=body.fault;
        order.status=body.fault?.startsWith('DROP_ACK_')||body.fault?.includes('OBSERVATION')?'UNKNOWN_OUTCOME':['LOGICAL_ESTOP','CELL_FAULT','BRAIN_TIMEOUT','BRAIN_INVALID_OUTPUT'].includes(body.fault)?'FAILED':'COMPLETED';
        if(body.fault==='LOGICAL_ESTOP')world.cellMode='ESTOP_LOGICAL';
        else if(body.fault==='CELL_FAULT')world.cellMode='FAULT';
        else if(order.status!=='FAILED'&&body.fault!=='DROP_ACK_BEFORE_EFFECT')inventory.find(item=>item.product_id===order.lines[0].product_id).location_id=world.destination;
        if(order.status==='UNKNOWN_OUTCOME')world.blocked='SCENE_RESET_BLOCKED_UNRESOLVED_JOBS';
        groups.at(-1).executions.push({job_id:order.job_ids[0],order_id:order.order_id,product_id:order.lines[0].product_id,state:order.status});
        data={state:order.status};
      }else if(path.endsWith('/reconcile')){
        order.status=body.fault?'REQUIRES_INTERVENTION':order.fault==='DROP_ACK_BEFORE_EFFECT'?'FAILED':'COMPLETED';
        groups.flatMap(g=>g.executions).find(j=>j.job_id===order.job_ids[0]).state=order.status;
        if(order.status!=='REQUIRES_INTERVENTION')world.blocked=null;
        data={state:order.status};
      }else if(path.endsWith('/evidence')){
        const planned=!['BRAIN_INVALID_OUTPUT','BRAIN_TIMEOUT'].includes(order.fault);
        data={job:{job_id:order.job_ids[0],state:order.status},verifications:[],observations:[],reconciliations:[],
          command:planned?{command_id:'command-'+order.job_ids[0],product_id:order.lines[0].product_id}:null,
          journal:planned?{status:order.fault==='DROP_ACK_BEFORE_EFFECT'?'FAILED':'SUCCEEDED',effect_count:order.fault==='DROP_ACK_BEFORE_EFFECT'?0:1}:null};
      }
      else if(path.endsWith('/playback'))data={job_id:order.job_ids[0],status:'UNAVAILABLE'};
    }else if(path.endsWith('/timeline'))data=[];
    if(data===undefined)throw Error('Unexpected request '+originalPath);
    return reply(data,status);
  }
  const context=vm.createContext({document:{getElementById:el,createElement:tag=>makeElement(tag)},
    Option:class{constructor(text,value){this.text=text;this.value=value;}},MotionPlayer:class{constructor(){return player;}},
    fetch,crypto:{randomUUID:()=>String(++sequence)},setInterval(){},console});
  vm.runInContext(fs.readFileSync('apps/erp_ui/workflow-guide.js','utf8'),context);
  vm.runInContext(fs.readFileSync('apps/erp_ui/app.js','utf8'),context);
  await new Promise(setImmediate);
  return {el,posts,requests,...initial,player,worlds,profiles:registeredProfiles,
    evidence:data=>{context.evidence=data;vm.runInContext('roboticsEvidence(evidence)',context);},
    current:()=>worlds.get(active),activeId:()=>active,refresh:()=>vm.runInContext('refresh()',context),
    poll:()=>vm.runInContext('(async()=>{await refreshHistory();await refresh();})()',context),
    block:reason=>{worlds.get(active).blocked=reason;},
    failNext:(path,{afterCommit=false,status=503,reason='SIMULATED_RESPONSE_FAILURE'}={})=>failures.push({path,afterCommit,status,reason}),
    serverDelete:id=>{worlds.delete(id);if(active===id)active=null;},
    serverStart:()=>{active='external-'+(++sequence);worlds.set(active,makeWorld(active,'hkm_inspired_v1'));return active;}};
}

test('three product clicks build one delivery; scenario selection is pure configuration and explicit restock preserves playback',async()=>{
  const {el,posts,orders,groups,inventory,player}=await dashboard();
  for(let i=0;i<3;i++)await el('create').onclick();
  assert.deepEqual(orders.map(order=>order.lines[0].product_id),['product-red','product-blue','product-green']);
  assert.equal(groups.length,1);assert.equal(player.data.jobs.length,3);
  assert.equal(el('create').disabled,false);assert.match(el('create').textContent,/Start new delivery/);
  el('scenario').value='LOGICAL_ESTOP';await el('scenario').onchange();
  assert.equal(groups.length,1);assert.ok(inventory.every(item=>item.location_id==='destination'));
  await el('fresh-scene').onclick();
  assert.equal(groups.length,2);assert.equal(groups[0].executions.length,3);
  assert.ok(inventory.every(item=>item.location_id==='source'));
  assert.equal(posts.filter(item=>item.path.endsWith('/run')).length,3);
  await el('create').onclick();
  assert.equal(posts.at(-1).body.fault,'LOGICAL_ESTOP');assert.equal(orders.at(-1).status,'FAILED');
  el('delivery').value=groups[0].delivery_id;await el('delivery').onchange();
  assert.equal(player.data.jobs.length,3);assert.equal(el('replay-scope').value,'delivery');
  el('orders').value=orders[0].job_ids[0];await el('orders').onchange();
  assert.equal(el('replay-scope').value,'product');assert.equal(player.data.job_id,orders[0].job_ids[0]);
});

test('exhausted happy path starts an explicit new delivery before issuing a new order',async()=>{
  const {el,posts,groups}=await dashboard();
  for(let i=0;i<3;i++)await el('create').onclick();
  const start=posts.length;
  await el('create').onclick();
  assert.deepEqual(posts.slice(start).map(item=>item.path),['/fixtures/fresh-scene','/orders','/jobs/job-3/run']);
  assert.equal(groups.length,2);assert.equal(groups[0].executions.length,3);assert.equal(groups[1].executions.length,1);
});

test('scenario changes cannot dispatch or bypass an unresolved outcome',async()=>{
  const {el,posts,groups,block,refresh}=await dashboard();await el('create').onclick();
  block('SCENE_RESET_BLOCKED_UNRESOLVED_JOBS');await refresh();const start=posts.length;
  el('scenario').value='LOGICAL_ESTOP';await el('scenario').onchange();
  assert.equal(groups.length,1);assert.equal(el('create').disabled,true);
  assert.deepEqual(posts.slice(start),[]);
  assert.match(el('message').textContent,/Start new test/);
});

test('individual legacy execution without a saved delivery identity survives polling',async()=>{
  const {el,orders,groups,player,refresh}=await dashboard();
  await el('create').onclick();await el('create').onclick();
  groups[0].executions.shift();
  el('orders').value=orders[0].job_ids[0];await el('orders').onchange();
  await refresh();
  assert.equal(el('orders').value,orders[0].job_ids[0]);
  assert.equal(player.selected,orders[0].job_ids[0]);
});

for(const fault of ['DROP_ACK_AFTER_EFFECT','DROP_ACK_BEFORE_EFFECT'])test(fault+': explain the paused next pick, reconcile original once, then allow another product',async()=>{
  const {el,orders,posts}=await dashboard();
  el('scenario').value=fault;await el('scenario').onchange();await el('create').onclick();
  el('product').value='product-blue';el('product').onchange();
  assert.equal(el('create').disabled,true);assert.match(el('create').textContent,/reconcile first/);
  assert.equal(el('next-step').hidden,false);assert.match(el('next-step-title').textContent,/product-red: outcome uncertain/);
  assert.match(el('resolve-blocker').textContent,/Reconcile product-red/);
  const start=posts.length;await el('create').onclick();
  assert.equal(posts.length,start);assert.equal(orders.length,1);
  await el('resolve-blocker').onclick();
  assert.deepEqual(posts.slice(start),[{path:'/jobs/job-0/reconcile',body:{fault:null}}]);
  assert.equal(orders[0].status,fault==='DROP_ACK_BEFORE_EFFECT'?'FAILED':'COMPLETED');
  assert.equal(el('create').disabled,false);assert.equal(el('next-step').hidden,true);
  assert.equal(el('product').value,'product-blue');await el('create').onclick();
  assert.equal(orders.length,2);assert.equal(orders[1].lines[0].product_id,'product-blue');
  assert.equal(posts.filter(item=>item.path==='/jobs/job-0/run').length,1);
});

test('next-step button reconciles the blocker even when historical execution details are selected',async()=>{
  const {el,posts,orders,groups}=await dashboard();await el('create').onclick();
  await el('fresh-scene').onclick();
  el('scenario').value='DROP_ACK_AFTER_EFFECT';await el('scenario').onchange();await el('create').onclick();
  el('delivery').value=groups[0].delivery_id;await el('delivery').onchange();
  assert.equal(el('orders').value,orders[0].job_ids[0]);
  const start=posts.length;await el('resolve-blocker').onclick();
  assert.deepEqual(posts.slice(start),[{path:'/jobs/job-1/reconcile',body:{fault:null}}]);
  assert.equal(el('orders').value,orders[1].job_ids[0]);
});

test('contradictory fresh evidence keeps next pick blocked but allows another observation of the original pick',async()=>{
  const {el,posts,orders}=await dashboard();
  el('scenario').value='DROP_ACK_AFTER_EFFECT';await el('scenario').onchange();await el('create').onclick();
  el('observation').value='CONTRADICTORY_OBSERVATION';await el('resolve-blocker').onclick();
  assert.equal(orders[0].status,'REQUIRES_INTERVENTION');assert.equal(el('create').disabled,true);
  assert.match(el('next-step-title').textContent,/more evidence needed/);assert.match(el('resolve-blocker').textContent,/Observe again: product-red/);
  assert.equal(el('resolve-blocker').disabled,false);assert.equal(el('reconcile').disabled,false);
  const start=posts.length;await el('resolve-blocker').onclick();await el('create').onclick();
  assert.deepEqual(posts.slice(start),[{path:'/jobs/job-0/reconcile',body:{fault:'CONTRADICTORY_OBSERVATION'}}]);
  assert.equal(orders.length,1);assert.equal(orders[0].status,'REQUIRES_INTERVENTION');assert.equal(el('create').disabled,true);
  el('observation').value='';await el('resolve-blocker').onclick();
  assert.equal(orders[0].status,'COMPLETED');assert.equal(el('create').disabled,false);
  assert.equal(posts.filter(p=>p.path.endsWith('/run')).length,1);
});

const executions=['','DROP_ACK_AFTER_EFFECT','DROP_ACK_BEFORE_EFFECT','CONTRADICTORY_OBSERVATION','LOW_CONFIDENCE_OBSERVATION','STALE_OBSERVATION','LOGICAL_ESTOP','CELL_FAULT','BRAIN_INVALID_OUTPUT','BRAIN_TIMEOUT'];
const observations=['','CONTRADICTORY_OBSERVATION','LOW_CONFIDENCE_OBSERVATION','STALE_OBSERVATION','MISSING_OBSERVATION'];
for(const execution of ['DROP_ACK_AFTER_EFFECT','DROP_ACK_BEFORE_EFFECT'])for(const observation of observations.slice(1))test(`continue same test: ${execution} / ${observation}`,async()=>{
  const app=await dashboard(),{el,orders,posts,groups}=app;
  el('scenario').value=execution;await el('create').onclick();
  el('observation').value=observation;await el('reconcile').onclick();
  assert.equal(orders[0].status,'REQUIRES_INTERVENTION');assert.equal(el('reconcile').disabled,false);
  assert.match(el('reconcile').textContent,/Observe again/);
  await el('reconcile').onclick();
  assert.equal(orders[0].status,'REQUIRES_INTERVENTION');assert.equal(el('create').disabled,true);
  el('product').value='product-blue';el('observation').value='';await el('reconcile').onclick();
  assert.equal(orders[0].status,execution==='DROP_ACK_AFTER_EFFECT'?'COMPLETED':'FAILED');
  assert.equal(app.current().id,'original');assert.equal(groups.length,1);
  assert.equal(el('create').disabled,false);assert.equal(el('reconcile').disabled,true);
  el('scenario').value='';await el('create').onclick();
  assert.equal(orders[1].status,'COMPLETED');assert.equal(orders[1].lines[0].product_id,'product-blue');
  assert.equal(groups[0].executions.length,2);assert.equal(app.player.data.jobs.length,2);
  assert.equal(posts.filter(p=>p.path==='/jobs/job-0/run').length,1);
  assert.equal(posts.filter(p=>p.path.endsWith('/reconcile')).length,3);
  assert.ok(posts.every(p=>!p.path.includes('fresh-scene')&&p.path!=='/simulation-tests'));
});
for(const execution of executions)for(const observation of observations)test(`independent test: ${execution||'happy'} / ${observation||'normal'}`,async()=>{
  const app=await dashboard(),{el,posts,orders,inventory}=app;
  el('scenario').value=execution;el('observation').value=observation;
  await el('scenario').onchange();await el('create').onclick();
  if(orders[0].status==='UNKNOWN_OUTCOME')await el('reconcile').onclick();
  const saved=JSON.stringify({orders,inventory});
  assert.equal(el('new-test').disabled,false);
  const start=posts.length;await el('new-test').onclick();await el('create-test').onclick();
  assert.deepEqual(posts.slice(start).map(p=>p.path),['/simulation-tests']);
  assert.equal(el('scenario').value,execution);assert.equal(el('observation').value,observation);
  assert.equal(app.current().orders.length,0);assert.equal(app.current().inventory.length,6);
  assert.ok(app.current().inventory.every(p=>p.location_id===app.current().sources[p.product_id]));
  assert.equal(el('create').disabled,false);assert.equal(el('new-test').disabled,false);
  assert.equal(JSON.stringify({orders,inventory}),saved);
  await el('create').onclick();
  assert.equal(app.current().orders.length,1);assert.equal(app.current().orders[0].fault,execution||null);
  assert.ok(posts.at(-1).path.startsWith('/simulation-tests/'));
  el('test-history').value='original';await el('test-history').onchange();
  assert.match(el('test-status').textContent,/read-only/);assert.equal(el('create').disabled,true);
  assert.equal(el('reconcile').disabled,true);assert.equal(el('reset').disabled,true);assert.equal(el('fresh-scene').disabled,true);
  assert.equal(el('new-test').disabled,false);assert.equal(el('return-current').hidden,false);
  assert.equal(app.player.data.jobs.length,1);
  const reads=posts.length;await el('create').onclick();await el('reconcile').onclick();await el('reset').onclick();
  assert.equal(posts.length,reads);assert.equal(JSON.stringify({orders,inventory}),saved);
  await el('return-current').onclick();
  assert.equal(el('return-current').hidden,true);assert.match(el('test-status').textContent,/current test/);
});

test('unreconciled test can be archived without reconciliation, then reviewed unchanged',async()=>{
  const {el,orders,posts}=await dashboard();
  el('scenario').value='DROP_ACK_AFTER_EFFECT';await el('create').onclick();
  await el('new-test').onclick();await el('create-test').onclick();
  assert.equal(orders[0].status,'UNKNOWN_OUTCOME');
  assert.equal(posts.filter(p=>p.path.endsWith('/reconcile')).length,0);
  el('test-history').value='original';await el('test-history').onchange();
  assert.equal(el('job-state').textContent,'UNKNOWN_OUTCOME');assert.equal(el('resolve-blocker').disabled,true);
});

test('guide directs attention once; choosing evidence and inspecting it never submits a command',async()=>{
  const {el,posts,orders,refresh}=await dashboard();
  assert.match(el('guide-title').textContent,/first pick/);
  assert.equal(el('stage-0').getAttribute('aria-current'),'step');
  el('scenario').value='DROP_ACK_AFTER_EFFECT';await el('scenario').onchange();
  assert.match(el('scenario-help').textContent,/Expected: the product moves/);
  assert.equal(posts.length,0);
  await el('create').onclick();
  assert.match(el('guide-title').textContent,/product-red: outcome uncertain/);
  assert.equal(el('stage-2').getAttribute('aria-current'),'step');
  assert.equal(el('review-panel').open,true);assert.equal(el('setup-panel').open,false);
  assert.equal(el('review-heading').focusCount,1);
  assert.match(el('review-journal').textContent,/1 pick effect/);
  assert.match(el('review-observation').textContent,/No post-pick observation has been assessed/);
  const start=posts.length;
  el('observation').value='CONTRADICTORY_OBSERVATION';el('observation').onchange();
  assert.match(el('observation-help').textContent,/conflicting evidence/);
  await refresh();await refresh();assert.equal(el('review-heading').focusCount,1);
  await el('guide-action').onclick();assert.equal(el('review-heading').focusCount,2);
  await el('view-evidence').onclick();assert.equal(el('evidence-details').open,true);
  assert.equal(el('timeline-panel').focusCount,1);
  el('use-normal').onclick();assert.equal(el('observation').value,'');
  assert.equal(el('resolve-blocker').focusCount,1);assert.equal(posts.length,start);
  assert.equal(orders[0].status,'UNKNOWN_OUTCOME');
  await el('resolve-blocker').onclick();
  assert.match(el('guide-title').textContent,/Pick verified/);
  assert.equal(el('stage-3').getAttribute('aria-current'),'step');
  await el('guide-action').onclick();assert.equal(el('setup-panel').open,true);assert.equal(el('product').focusCount,1);
  assert.equal(posts.filter(p=>p.path.endsWith('/run')).length,1);
});

test('human review stays available for repeated bad observations without focus stealing',async()=>{
  const {el,posts,refresh}=await dashboard();el('scenario').value='DROP_ACK_AFTER_EFFECT';await el('create').onclick();
  el('observation').value='LOW_CONFIDENCE_OBSERVATION';await el('resolve-blocker').onclick();
  assert.match(el('guide-title').textContent,/your review is needed/);
  assert.equal(el('resolve-blocker').disabled,false);assert.equal(el('review-panel').open,true);
  const focus=el('review-heading').focusCount;await refresh();await el('resolve-blocker').onclick();
  assert.equal(el('review-heading').focusCount,focus);
  assert.equal(posts.filter(p=>p.path.endsWith('/run')).length,1);
});

test('guide review and full evidence target the active blocker while an earlier replay is selected',async()=>{
  const {el,posts,orders,groups}=await dashboard();await el('create').onclick();await el('fresh-scene').onclick();
  el('scenario').value='DROP_ACK_AFTER_EFFECT';await el('create').onclick();
  el('delivery').value=groups[0].delivery_id;await el('delivery').onchange();
  assert.equal(el('orders').value,orders[0].job_ids[0]);assert.match(el('review-identity').textContent,/Job job-1/);
  const start=posts.length;await el('guide-action').onclick();
  assert.equal(el('orders').value,orders[1].job_ids[0]);assert.equal(posts.length,start);
  el('delivery').value=groups[0].delivery_id;await el('delivery').onchange();
  await el('view-evidence').onclick();assert.equal(el('orders').value,orders[1].job_ids[0]);assert.equal(posts.length,start);
});

for(const fault of ['LOGICAL_ESTOP','CELL_FAULT'])test(fault+': guide resets the cell explicitly without rerunning',async()=>{
  const {el,posts,orders}=await dashboard();el('scenario').value=fault;await el('create').onclick();
  assert.match(el('guide-title').textContent,/Reset the stopped cell/);
  const start=posts.length;await el('guide-action').onclick();
  assert.deepEqual(posts.slice(start),[{path:'/cell/reset',body:{}}]);
  assert.equal(el('create').disabled,false);assert.equal(orders.length,1);
});

for(const fault of ['BRAIN_TIMEOUT','BRAIN_INVALID_OUTPUT'])test(fault+': guide explains rejection and focuses configuration without dispatch',async()=>{
  const {el,posts}=await dashboard();el('scenario').value=fault;await el('create').onclick();
  assert.match(el('guide-detail').textContent,/before a robot command was created/);
  const start=posts.length;await el('guide-action').onclick();
  assert.equal(el('scenario').focusCount,1);assert.equal(posts.length,start);
});

test('depleted delivery and saved test both have an explicit next action with history intact',async()=>{
  const {el,posts,orders}=await dashboard();for(let i=0;i<3;i++)await el('create').onclick();
  assert.match(el('guide-title').textContent,/Delivery finished/);
  const saved=JSON.stringify(orders),start=posts.length;await el('guide-action').onclick();await el('create-test').onclick();
  assert.deepEqual(posts.slice(start).map(p=>p.path),['/simulation-tests']);
  el('test-history').value='original';await el('test-history').onchange();
  assert.match(el('guide-title').textContent,/saved test/);
  assert.equal(el('test-history').value,'original');
  const historyStart=posts.length;await el('guide-action').onclick();
  assert.equal(posts.length,historyStart);assert.equal(JSON.stringify(orders),saved);
  assert.match(el('guide-title').textContent,/first pick/);
});

test('every selectable mode has a definition and comparison; browsing them cannot execute a test',async()=>{
  const {el,posts,refresh}=await dashboard();
  for(const [kind,values] of [['scenario',executions],['observation',observations]]){
    const table=el(kind+'-comparisons');
    assert.equal(table.children.length,values.length);
    const meanings=[];
    for(const value of values){
      el(kind).value=value;await el(kind).onchange();
      const row=table.children[values.indexOf(value)];
      // The selected definition and the comparison row describe the same mode.
      assert.equal(el(kind+'-meaning').textContent,row.children[1].children[1].textContent);
      assert.equal(el(kind+'-phase').textContent,row.children[1].children[0].textContent);
      assert.ok(el(kind+'-difference').textContent.length>0);
      meanings.push(el(kind+'-meaning').textContent);
    }
    assert.equal(new Set(meanings).size,values.length);
    el(kind+'-compare').open=true;await refresh();
    assert.equal(el(kind+'-compare').open,true);assert.equal(table.children.length,values.length);
  }
  assert.deepEqual(posts,[]);
});

test('execution and review help explain different stages without changing the uncertain outcome',async()=>{
  const {el,posts,orders}=await dashboard();
  el('scenario').value='DROP_ACK_AFTER_EFFECT';await el('create').onclick();
  const count=posts.length,job=orders[0].job_ids[0];
  el('scenario').value='STALE_OBSERVATION';el('scenario').onchange();
  assert.match(el('scenario-phase').textContent,/first check after movement/);
  assert.match(el('scenario-meaning').textContent,/old capture time/);
  assert.match(el('observation-phase').textContent,/Review capture/);
  el('observation').value='CONTRADICTORY_OBSERVATION';el('observation').onchange();
  assert.match(el('observation-meaning').textContent,/two different locations/);
  assert.match(el('scenario-meaning').textContent,/old capture time/);
  el('observation').value='MISSING_OBSERVATION';el('observation').onchange();
  assert.match(el('observation-meaning').textContent,/no detected products/);
  assert.match(el('observation-difference').textContent,/cannot prove/);
  el('use-normal').onclick();
  assert.match(el('observation-difference').textContent,/does not undo an execution fault or guarantee success/);
  assert.equal(orders[0].status,'UNKNOWN_OUTCOME');assert.equal(orders[0].job_ids[0],job);
  assert.equal(el('create').disabled,true);assert.equal(posts.length,count);
});


test('six source products use their own source IDs and remain available until individually picked',async()=>{
  const ui=await dashboard({hkm:true});
  for(const sku of ['A','B','C','D','E','F']){
    assert.equal(ui.el('product').value,'product-SKU-'+sku+'-01');
    assert.equal(ui.el('create').disabled,false);
    await ui.el('create').onclick();
  }
  const orders=ui.posts.filter(item=>item.path==='/orders');
  assert.deepEqual(orders.map(item=>item.body.lines[0].source_id),['SRC_A','SRC_B','SRC_C','SRC_D','SRC_E','SRC_F']);
  assert.equal(ui.groups[0].executions.length,6);
  assert.match(ui.el('create').textContent,/new delivery/);
  assert.equal(ui.el('tool-showcase').hidden,false);
});

test('tool and uncertainty inspector reads persisted decision and observation without dispatching',async()=>{
  const ui=await dashboard({hkm:true});const before=ui.posts.length;
  const command={command_id:'original-command',product_id:'product-SKU-B-01',tool_selection:{selected_tool_id:'EE_VAC_ARRAY',assessed_mass_kg:1.2,tool_change_required:true,candidate_tools:[{tool_id:'EE_VAC_ARRAY',eligible:true,score:110,reasons:['PREFERRED_FOR_PRODUCT_FAMILY','MASS_WITHIN_SIMULATED_LIMIT']},{tool_id:'EE_VAC_SINGLE',eligible:false,score:null,reasons:['SIMULATED_MASS_LIMIT_EXCEEDED']}]}};
  const evidence={job:{order_id:'original-order',job_id:'original-job',state:'UNKNOWN_OUTCOME',line:{product_id:command.product_id}},command,journal:{effect_count:1},observations:[{model_version:'synthetic-observer-2',calibration_version:'hkm-cal-1',machine_telemetry:{tool_state:{active_tool_id:'EE_VAC_ARRAY'}},objects:[{product_id:command.product_id,confidence:.35}]}],verifications:[{reason:'LOW_CONFIDENCE'}]};
  ui.evidence(evidence);
  assert.match(ui.el('tool-decision').textContent,/Multi-cup suction plate.*1.20 kg.*tool change/);
  assert.equal(ui.el('status-command').textContent,'original-command');assert.match(ui.el('status-job').textContent,/UNKNOWN_OUTCOME.*original-job/);
  assert.match(ui.el('status-observation').textContent,/35%.*LOW_CONFIDENCE.*synthetic-observer-2/);
  assert.equal(ui.el('status-calibration').textContent,'hkm-cal-1');
  assert.match(ui.el('knowledge-state').textContent,/uncertain.*do not retry.*one transfer recorded/);
  assert.equal(ui.posts.length,before);
  const rows=ui.el('tool-candidates').children;
  assert.equal(rows.length,2);assert.equal(rows[1].children[1].textContent,'Rejected');
  const html=fs.readFileSync('apps/erp_ui/index.html','utf8');
  for(const text of ['Simulation boundaries','Not Cognibotics CAD','Not validated robot dynamics','Not SICS AI proprietary software','camera images are not analyzed'])assert.ok(html.includes(text));
});


const worldRequests=items=>items.filter(({path})=>!['/cell-profiles','/simulation-tests','/simulation-tests/clear'].includes(path)&&!/^\/simulation-tests\/[^/]+\/delete$/.test(path));
async function createSelectedTest(ui,profile){
  await ui.el('new-test').onclick();
  if(profile){ui.el('cell-profile').value=profile;await ui.el('cell-profile').onchange();}
  await ui.el('create-test').onclick();
}

test('new-test dialog shows selectable registered cells and cancel preserves the current legacy test',async()=>{
  const ui=await dashboard(),before=JSON.stringify([...ui.worlds.values()]);
  assert.match(ui.el('test-history').options.find(option=>option.value==='original').text,/Legacy Cartesian cell/);
  await ui.el('new-test').onclick();
  assert.equal(ui.el('new-test-dialog').open,true);
  assert.deepEqual(ui.el('cell-profile').options.map(option=>option.value),['hkm_inspired_v1']);
  assert.equal(ui.el('cell-profile').value,'hkm_inspired_v1');
  assert.match(ui.el('cell-profile-description').textContent,/six|6/i);
  assert.deepEqual(ui.posts,[]);
  await ui.el('cancel-new-test').onclick();
  assert.equal(ui.el('new-test-dialog').open,false);
  assert.deepEqual(ui.posts,[]);assert.equal(JSON.stringify([...ui.worlds.values()]),before);
  assert.equal(ui.el('test-history').value,'original');
});

test('confirming a new test sends the selected cell explicitly and creates six products without changing legacy history',async()=>{
  const ui=await dashboard(),before=JSON.stringify(ui.worlds.get('original'));
  await createSelectedTest(ui);
  assert.equal(ui.posts.length,1);assert.equal(ui.posts[0].path,'/simulation-tests');
  assert.deepEqual(Object.keys(ui.posts[0].body).sort(),['cell_profile_id','request_id']);
  assert.equal(ui.posts[0].body.cell_profile_id,'hkm_inspired_v1');assert.ok(ui.posts[0].body.request_id);
  assert.equal(ui.current().cell_profile_id,'hkm_inspired_v1');assert.equal(ui.current().inventory.length,6);
  assert.equal(ui.el('product').options.length,6);assert.equal(ui.el('new-test-dialog').open,false);
  assert.equal(JSON.stringify(ui.worlds.get('original')),before);
  assert.match(ui.el('test-history').options.find(option=>option.value==='original').text,/Legacy Cartesian cell/);
});

test('a future available registry cell is selectable without hardcoded UI choices',async()=>{
  const profiles=[
    {cell_profile_id:'hkm_inspired_v1',display_name:'HKM cell',description:'Current six-tool cell.',selectable:true,product_count:6,tool_count:6},
    {cell_profile_id:'future_registered_cell',display_name:'Future registered cell',description:'Distinct future fixture description.',selectable:true,product_count:6,tool_count:2},
    {cell_profile_id:'legacy_cartesian_v1',display_name:'Legacy Cartesian cell',description:'History only.',selectable:false,product_count:3,tool_count:1}
  ];
  const ui=await dashboard({profiles});await ui.el('new-test').onclick();
  assert.deepEqual(ui.el('cell-profile').options.map(option=>option.value),['hkm_inspired_v1','future_registered_cell']);
  ui.el('cell-profile').value='future_registered_cell';await ui.el('cell-profile').onchange();
  assert.match(ui.el('cell-profile-description').textContent,/Distinct future fixture description/);
  assert.deepEqual(ui.posts,[]);await ui.el('create-test').onclick();
  assert.equal(ui.posts[0].body.cell_profile_id,'future_registered_cell');
  assert.equal(ui.current().cell_profile_id,'future_registered_cell');
  assert.match(ui.el('test-history').options.find(option=>option.value===ui.activeId()).text,/Future registered cell/);
});

test('deleting the current uncertain test requires confirmation and leaves an empty workspace without issuing a pick',async()=>{
  const ui=await dashboard();ui.el('scenario').value='DROP_ACK_AFTER_EFFECT';await ui.el('create').onclick();
  const before=JSON.stringify(ui.orders),start=ui.posts.length;
  await ui.el('delete-test').onclick();assert.equal(ui.el('delete-test-dialog').open,true);
  assert.match(ui.el('delete-test-detail').textContent,/Test 1/i);assert.equal(ui.posts.length,start);
  await ui.el('cancel-delete-test').onclick();assert.equal(ui.el('delete-test-dialog').open,false);
  assert.equal(JSON.stringify(ui.orders),before);assert.equal(ui.posts.length,start);
  await ui.el('delete-test').onclick();const reads=ui.requests.length;await ui.el('confirm-delete-test').onclick();
  assert.deepEqual(ui.posts.slice(start).map(item=>item.path),['/simulation-tests/original/delete']);
  assert.deepEqual(Object.keys(ui.posts.at(-1).body),['request_id']);
  assert.equal(ui.worlds.size,0);assert.equal(ui.activeId(),null);assert.equal(ui.el('delete-test-dialog').open,false);
  assert.equal(ui.el('empty-workspace').hidden,false);assert.equal(ui.el('test-workspace').hidden,true);
  assert.equal(ui.el('create').disabled,true);assert.equal(ui.player.selected,null);
  assert.deepEqual(worldRequests(ui.requests.slice(reads)),[]);
  assert.equal(ui.posts.filter(item=>item.path.endsWith('/run')).length,1);
  assert.equal(ui.posts.filter(item=>item.path.endsWith('/reconcile')).length,0);
});

test('deleting a selected archive preserves the active test and never silently selects another world',async()=>{
  const ui=await dashboard();await ui.el('create').onclick();await createSelectedTest(ui);
  const active=ui.activeId(),saved=JSON.stringify(ui.current());
  ui.el('test-history').value='original';await ui.el('test-history').onchange();
  assert.equal(ui.el('delete-test').disabled,false);await ui.el('delete-test').onclick();
  const reads=ui.requests.length;await ui.el('confirm-delete-test').onclick();
  assert.equal(ui.posts.at(-1).path,'/simulation-tests/original/delete');assert.equal(ui.activeId(),active);
  assert.equal(ui.worlds.size,1);assert.equal(JSON.stringify(ui.current()),saved);
  assert.equal(ui.el('test-workspace').hidden,true);assert.deepEqual(worldRequests(ui.requests.slice(reads)),[]);
  await ui.el('return-current').onclick();assert.equal(ui.el('test-history').value,active);
  assert.equal(ui.el('test-workspace').hidden,false);assert.equal(ui.el('create').disabled,false);
});

test('clear-all confirmation submits exactly the displayed test IDs and cancellation changes no data',async()=>{
  const ui=await dashboard();await createSelectedTest(ui);
  const ids=[...ui.worlds.keys()],saved=JSON.stringify([...ui.worlds.values()]),start=ui.posts.length;
  await ui.el('clear-tests').onclick();assert.equal(ui.el('delete-test-dialog').open,true);
  assert.match(ui.el('delete-test-detail').textContent,/2/);assert.equal(ui.posts.length,start);
  await ui.el('cancel-delete-test').onclick();assert.equal(JSON.stringify([...ui.worlds.values()]),saved);
  await ui.el('clear-tests').onclick();const reads=ui.requests.length;await ui.el('confirm-delete-test').onclick();
  assert.equal(ui.posts.at(-1).path,'/simulation-tests/clear');
  assert.deepEqual(ui.posts.at(-1).body.expected_test_ids,ids);assert.ok(ui.posts.at(-1).body.request_id);
  assert.equal(ui.posts.length,start+1);assert.equal(ui.worlds.size,0);assert.equal(ui.activeId(),null);
  assert.deepEqual(worldRequests(ui.requests.slice(reads)),[]);assert.equal(ui.el('empty-workspace').hidden,false);
});

test('empty startup performs no world reads or writes and only explicit cell confirmation creates a world',async()=>{
  const ui=await dashboard({empty:true});
  assert.equal(ui.el('empty-workspace').hidden,false);assert.equal(ui.el('test-workspace').hidden,true);
  assert.equal(ui.el('create').disabled,true);assert.equal(ui.el('delete-test').disabled,true);assert.equal(ui.el('clear-tests').disabled,true);
  assert.deepEqual(worldRequests(ui.requests),[]);assert.deepEqual(ui.posts,[]);
  await ui.poll();await ui.el('create').onclick();await ui.el('reconcile').onclick();await ui.el('reset').onclick();
  assert.deepEqual(worldRequests(ui.requests),[]);assert.deepEqual(ui.posts,[]);
  await ui.el('empty-new-test').onclick();assert.equal(ui.el('new-test-dialog').open,true);assert.deepEqual(ui.posts,[]);
  await ui.el('create-test').onclick();assert.equal(ui.current().inventory.length,6);
  assert.equal(ui.el('empty-workspace').hidden,true);assert.equal(ui.el('test-workspace').hidden,false);
  assert.equal(ui.posts.length,1);assert.equal(ui.posts[0].path,'/simulation-tests');
});

test('creation response loss keeps the dialog and freezes the original request identity for retry',async()=>{
  const ui=await dashboard();await ui.el('new-test').onclick();
  ui.failNext('/simulation-tests',{afterCommit:true});await ui.el('create-test').onclick();
  assert.equal(ui.el('new-test-dialog').open,true);assert.match(ui.el('new-test-error').textContent,/SIMULATED_RESPONSE_FAILURE/);
  assert.equal(ui.el('cell-profile').disabled,true);assert.equal(ui.worlds.size,2);
  const first=structuredClone(ui.posts.at(-1));await ui.el('create-test').onclick();
  assert.deepEqual(ui.posts.at(-1),first);assert.equal(ui.posts.length,2);assert.equal(ui.worlds.size,2);
  assert.equal(ui.el('new-test-dialog').open,false);assert.equal(ui.el('test-history').value,first.body.request_id);
});

test('deletion response loss retries the same original test identity after history becomes empty',async()=>{
  const ui=await dashboard();await ui.el('delete-test').onclick();
  ui.failNext('/simulation-tests/original/delete',{afterCommit:true});await ui.el('confirm-delete-test').onclick();
  assert.equal(ui.el('delete-test-dialog').open,true);assert.match(ui.el('delete-test-error').textContent,/SIMULATED_RESPONSE_FAILURE/);
  assert.equal(ui.worlds.size,0);const first=structuredClone(ui.posts.at(-1));
  await ui.el('confirm-delete-test').onclick();assert.deepEqual(ui.posts.at(-1),first);
  assert.equal(ui.posts.length,2);assert.equal(ui.el('delete-test-dialog').open,false);assert.equal(ui.activeId(),null);
  assert.deepEqual(worldRequests(ui.requests.slice(ui.requests.findIndex(r=>r.path===first.path))),[]);
});

test('retrying clear after a lost reply retains its request and expected IDs and cannot delete a later test',async()=>{
  const ui=await dashboard();await createSelectedTest(ui);await ui.el('clear-tests').onclick();
  ui.failNext('/simulation-tests/clear',{afterCommit:true});await ui.el('confirm-delete-test').onclick();
  assert.equal(ui.el('delete-test-dialog').open,true);assert.equal(ui.worlds.size,0);
  const first=structuredClone(ui.posts.at(-1)),later=ui.serverStart();await ui.poll();
  await ui.el('confirm-delete-test').onclick();assert.deepEqual(ui.posts.at(-1),first);
  assert.equal(ui.worlds.size,1);assert.equal(ui.activeId(),later);assert.ok(ui.worlds.has(later));
  assert.equal(ui.el('delete-test-dialog').open,false);
});

test('changed test history rejects stale clear confirmation until the user reviews the new scope',async()=>{
  const ui=await dashboard();await ui.el('clear-tests').onclick();const later=ui.serverStart();
  await ui.el('confirm-delete-test').onclick();assert.equal(ui.el('delete-test-dialog').open,true);
  assert.match(ui.el('delete-test-error').textContent,/test list changed.*Cancel and review/i);assert.equal(ui.worlds.size,2);
  const failed=structuredClone(ui.posts.at(-1));assert.deepEqual(failed.body.expected_test_ids,['original']);
  await ui.el('confirm-delete-test').onclick();assert.deepEqual(ui.posts.at(-1),failed);assert.equal(ui.worlds.size,2);
  await ui.el('cancel-delete-test').onclick();await ui.el('clear-tests').onclick();await ui.el('confirm-delete-test').onclick();
  assert.deepEqual(ui.posts.at(-1).body.expected_test_ids,['original',later]);
  assert.notEqual(ui.posts.at(-1).body.request_id,failed.body.request_id);assert.equal(ui.worlds.size,0);
});

test('polling after external deletion clears stale selection without activating an archived test',async()=>{
  const ui=await dashboard();await ui.el('create').onclick();await createSelectedTest(ui);
  const removed=ui.activeId();ui.serverDelete(removed);const reads=ui.requests.length,posts=ui.posts.length;
  await ui.poll();assert.equal(ui.activeId(),null);assert.equal(ui.worlds.size,1);assert.ok(ui.worlds.has('original'));
  assert.equal(ui.el('test-workspace').hidden,true);assert.equal(ui.el('empty-workspace').hidden,false);
  assert.equal(ui.el('create').disabled,true);assert.equal(ui.player.selected,null);assert.equal(ui.posts.length,posts);
  assert.deepEqual(worldRequests(ui.requests.slice(reads)),[]);
  ui.el('test-history').value='original';await ui.el('test-history').onchange();
  assert.equal(ui.el('test-workspace').hidden,false);assert.equal(ui.el('create').disabled,true);
  assert.match(ui.el('test-status').textContent,/read-only/);assert.equal(ui.activeId(),null);
});
