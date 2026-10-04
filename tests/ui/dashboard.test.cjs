const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

async function dashboard({hkm=false}={}){
  const catalogue=hkm?JSON.parse(fs.readFileSync('robotops/robotics/catalogue-v1.json','utf8')):null;
  const sources=catalogue?Object.fromEntries(catalogue.products.map(p=>['product-'+p.sku+'-01',catalogue.layout.sources[p.sku].location_id])):{};
  const elements=new Map(),posts=[],worlds=new Map();
  let active='original',sequence=0;
  const makeWorld=id=>({id,number:worlds.size+1,orders:[],groups:[{delivery_id:id+'-scene-1',started_at:'2026-10-03T14:00:00Z',current:true,executions:[]}],epoch:1,cellMode:'READY',blocked:null,
    inventory:hkm?catalogue.products.map(p=>({product_id:'product-'+p.sku+'-01',location_id:sources['product-'+p.sku+'-01']})):['red','blue','green'].map(color=>({product_id:'product-'+color,location_id:'source'}))});
  worlds.set(active,makeWorld(active));
  const initial=worlds.get(active);
  const el=id=>{
    if(!elements.has(id))elements.set(id,{value:id==='replay-scope'?'delivery':'',textContent:'',disabled:false,options:[],children:[],
      add(option){this.options.push(option);if(this.options.length===1)this.value=option.value;},
      replaceChildren(){this.options=[];this.value='';},addEventListener(event,fn){this['on'+event]=fn;},
      attributes:{},classList:{toggle(){}},focus(){this.focusCount=(this.focusCount||0)+1;},
      append(...nodes){this.children.push(...nodes);},setAttribute(key,value){this.attributes[key]=value;},getAttribute(key){return this.attributes[key]||'';},removeAttribute(key){delete this.attributes[key];},closest(){return this;},scrollIntoView(){this.scrolled=true;}});
    return elements.get(id);
  };
  const player={select(id){this.selected=id;},previewScene(){},update(data){this.data=data;},updateDelivery(data){this.data=data;}};
  async function fetch(path,options={}){
    const body=options.body?JSON.parse(options.body):null;
    if(options.method==='POST')posts.push({path,body});
    let data,status=200;
    const match=path.match(/^\/simulation-tests\/([^/]+)(\/.*)$/),id=match?match[1]:'original';
    if(match)path=match[2];
    if(path==='/simulation-tests'){
      if(body){active=body.request_id;worlds.set(active,makeWorld(active));}
      const tests=[...worlds.values()].map(w=>({test_id:w.id,number:w.number,active:w.id===active,order_count:w.orders.length,outcomes:w.orders.map(o=>o.status)}));
      data=body?tests.at(-1):{active_test_id:active,tests};
      return {ok:true,json:async()=>data};
    }
    const world=worlds.get(id),{orders,groups,inventory}=world;
    if(body&&id!==active)return {ok:false,json:async()=>({reason:'TEST_ARCHIVED_READ_ONLY'})};
    const scene=()=>({scene_epoch:id+'-scene-'+world.epoch,source:'CURRENT_WORLD_REFERENCE',objects:[]});
    const fixture=()=>({runtime:'headless',scene_epoch:scene().scene_epoch,source_id:'source',destination_id:'destination',
      products:inventory.map(item=>({product_id:item.product_id,sku:hkm?item.product_id.slice(8,-3):item.product_id})),catalogue,product_sources:sources,inventory,scene_reset_blocked_reason:world.blocked});
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
        else if(order.status!=='FAILED'&&body.fault!=='DROP_ACK_BEFORE_EFFECT')inventory.find(item=>item.product_id===order.lines[0].product_id).location_id='destination';
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
    if(data===undefined)throw Error('Unexpected request '+path);
    return {ok:status<400,status,json:async()=>JSON.parse(JSON.stringify(data))};
  }
  const context=vm.createContext({document:{getElementById:el,createElement:()=>({children:[],append(...nodes){this.children.push(...nodes);}})},
    Option:class{constructor(text,value){this.text=text;this.value=value;}},MotionPlayer:class{constructor(){return player;}},
    fetch,crypto:{randomUUID:()=>String(++sequence)},setInterval(){},console});
  vm.runInContext(fs.readFileSync('apps/erp_ui/workflow-guide.js','utf8'),context);
  vm.runInContext(fs.readFileSync('apps/erp_ui/app.js','utf8'),context);
  await new Promise(setImmediate);
  return {el,posts,...initial,player,worlds,evidence:data=>{context.evidence=data;vm.runInContext('roboticsEvidence(evidence)',context);},current:()=>worlds.get(active),refresh:()=>vm.runInContext('refresh()',context),block:reason=>{worlds.get(active).blocked=reason;}};
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
  const start=posts.length;await el('new-test').onclick();
  assert.deepEqual(posts.slice(start).map(p=>p.path),['/simulation-tests']);
  assert.equal(el('scenario').value,execution);assert.equal(el('observation').value,observation);
  assert.equal(app.current().orders.length,0);assert.equal(app.current().inventory.length,3);
  assert.ok(app.current().inventory.every(p=>p.location_id==='source'));
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
  await el('new-test').onclick();
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
  const saved=JSON.stringify(orders),start=posts.length;await el('guide-action').onclick();
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
