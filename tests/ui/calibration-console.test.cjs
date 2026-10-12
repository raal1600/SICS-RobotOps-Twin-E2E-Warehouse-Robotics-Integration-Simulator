const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('apps/erp_ui/calibration-console.js','utf8');

test('validation summary groups repeated limits while preserving the saved detailed failure list',()=>{
  const {instance}=consoleFixture();
  const failures=Array.from({length:24},(_,i)=>`REFERENCE_ERROR_MM:long-reference-id-${i}`);
  failures.push('CHAIN_RMS_PX:long-image-id-1');
  const original=JSON.stringify(failures);
  const groups=instance.failureGroups(failures);
  assert.equal(groups.length,2);
  assert.equal(groups[0][0],'Independent reference error');
  assert.equal(groups[0][1],'24 recorded failures');
  assert.equal(groups[1][0],'Robot-chain image error');
  assert.equal(JSON.stringify(failures),original);
  assert.doesNotMatch(JSON.stringify(groups),/long-reference-id/);
});

test('new record clears old source and protocol immediately and keeps the full-file mode',async()=>{
  const {instance,nodes}=consoleFixture();let resolve;let selectedMode;
  instance.selected='validation/new-report';instance.records=[];instance.fullSource=true;
  instance.renderInvestigation=()=>{};instance.renderGeometry=()=>{};instance.options=()=>{};
  instance.el('calibration-summary').replaceChildren=()=>{};
  instance.el('calibration-source-content').textContent='old function';
  instance.el('calibration-protocol').textContent='old operands';
  instance.request=()=>new Promise(done=>resolve=done);
  instance.summary=()=>{};instance.populateSources=()=>{};
  instance.showSource=async full=>{selectedMode=full;};
  const pending=instance.selectRecord();
  assert.equal(nodes['calibration-source-content'].textContent,'');
  assert.doesNotMatch(nodes['calibration-protocol'].textContent,/old operands/);
  resolve({report_id:'new-report'});await pending;
  assert.equal(selectedMode,true);
});

test('a missing receipt offers an explicit retry of the unchanged saved request only',async()=>{
  const {instance,nodes}=consoleFixture(),calls=[];
  const saved={camera:'camera-west',route:'/calibration/cameras/camera-west/acquisitions',body:{request_id:'same-id',dataset_id:'same-data',expected_revision:1}};
  instance.pending=saved;instance.render=()=>{};instance.readOnly=()=>false;
  instance.request=async(path,body)=>{calls.push({path,body});throw Object.assign(new Error('missing'),{status:404});};
  await instance.checkPending();
  assert.equal(calls.length,1);assert.equal(calls[0].body,undefined);
  assert.equal(instance.pending,saved);assert.equal(instance.pendingReceiptMissing,true);
  assert.match(nodes['calibration-error'].textContent,/may still be processing/);
  let sent=0;instance.sendPending=async()=>{assert.equal(instance.pending,saved);sent++;};
  instance.readOnly=()=>true;await instance.checkPending();assert.equal(sent,0);
  instance.readOnly=()=>false;await instance.checkPending();assert.equal(sent,1);
});

test('unavailable receipt service never offers or sends a retry',async()=>{
  const {instance}=consoleFixture();instance.pending={camera:'camera-west',body:{request_id:'original'}};
  instance.render=()=>{};instance.request=async()=>{throw new Error('offline');};
  instance.sendPending=async()=>{assert.fail('must inspect the receipt first');};
  await instance.checkPending();assert.equal(instance.pendingReceiptMissing,undefined);
});

function consoleFixture(){
  const context={URLSearchParams,Intl};vm.createContext(context);
  vm.runInContext(source+'\nglobalThis.ConsoleClass=CalibrationConsole;',context);
  const instance=Object.create(context.ConsoleClass.prototype),nodes={};
  const el=id=>nodes[id]??=( {value:'',textContent:'',hidden:false,reportValidity:()=>true} );
  const overlays=[];
  Object.assign(instance,{el,overlay:objects=>overlays.push(objects),saveSelection(){},
    test:'world-a',capture:'capture-a',camera:'camera-west',pixelGeneration:0,generation:0,
    selectionGeneration:0,sourceGeneration:0,geometryGeneration:0,workspace:{}});
  el('calibration-pixel-artifact').value='approved-a';el('calibration-pixel-u').value='120';
  el('calibration-pixel-v').value='240';el('calibration-pixel-mode').value='native';
  return {instance,nodes,overlays};
}

for(const changed of ['test','camera','capture'])test(`late depth range cannot relabel changed ${changed}`,async()=>{
  const {instance,nodes}=consoleFixture();let resolve;
  instance.request=()=>new Promise(done=>resolve=done);
  const pending=instance.renderDepthDisplay(instance.capture);instance[changed]='new-selection';
  resolve({low_raw:100,high_raw:200,invalid_pixels:3});await pending;
  assert.doesNotMatch(nodes['calibration-depth-display'].textContent,/100\.0/);
});

test('all missing depth display reports no positive finite returns',async()=>{
  const {instance,nodes}=consoleFixture();
  instance.request=async()=>({low_raw:null,high_raw:null,invalid_pixels:307200});
  await instance.renderDepthDisplay(instance.capture);
  assert.match(nodes['calibration-depth-display'].textContent,/no positive finite returns/);
  assert.match(nodes['calibration-depth-display'].textContent,/307200/);
});

for(const changed of ['test','camera','capture'])test(`late pixel response cannot replace the selected ${changed}`,async()=>{
  const {instance,nodes,overlays}=consoleFixture();let resolve;
  instance.request=()=>new Promise(done=>{resolve=done;});
  const pending=instance.inspectPixel();instance[changed]='new-selection';
  resolve({result:{point:[1,2,3]},overlay:[{name:'old-ray'}],rgb_preview:'old-image'});
  await pending;
  assert.equal(nodes['calibration-pixel-result'],undefined);
  assert.equal(overlays.length,0);
});

test('editing/clearing a pixel invalidates an outstanding calculation and its ray',async()=>{
  const {instance,nodes,overlays}=consoleFixture();let resolve;
  instance.request=()=>new Promise(done=>{resolve=done;});
  const pending=instance.inspectPixel();instance.clearPixel();
  resolve({result:{point:[1,2,3]},overlay:[{name:'stale-ray'}]});await pending;
  assert.equal(overlays.length,1);assert.equal(overlays[0].length,0);
  assert.equal(nodes['calibration-pixel-status'].textContent,'');
  assert.equal(nodes['calibration-pixel-clear'].hidden,true);
});

test('a rejected pixel is visible as an error result and never creates an invented point',async()=>{
  const {instance,nodes,overlays}=consoleFixture();
  instance.request=async()=>({scope:'READ_ONLY_RECOMPUTATION',artifact_id:'approved-a',
    result:{code:'NO_VALID_DEPTH',detail:'Missing depth'},overlay:[],rgb_preview:'rgb',depth_preview:'depth'});
  await instance.inspectPixel();
  assert.match(nodes['calibration-pixel-status'].textContent,/No point: NO_VALID_DEPTH/);
  assert.equal(overlays[0].length,0);
  assert.equal(JSON.parse(nodes['calibration-pixel-result'].textContent).result.point,undefined);
});

test('late world overview cannot replace a newer loaded selection',async()=>{
  const {instance}=consoleFixture();let resolve;
  instance.request=()=>new Promise(done=>{resolve=done;});
  const pending=instance.load();instance.generation++;instance.test='world-b';
  resolve({supported:true,cameras:[{camera_id:'old'}]});await pending;
  assert.equal(instance.overview,undefined);
  assert.equal(instance.workspace.calibrationAvailable,undefined);
});

test('opening calibration evidence refreshes saved records without mutating or changing camera selection',async()=>{
  const {instance,nodes}=consoleFixture();let focused=false;const reads=[];
  instance.el('calibration-evidence-title').focus=()=>{focused=true;};
  instance.workspace.show=(view,push)=>{assert.equal(view,'inspect');assert.equal(push,true);};
  instance.request=async(path,body)=>{reads.push(path);assert.equal(body,undefined);
    return path==='/calibration'?{supported:true,cameras:[{camera_id:'camera-west'}]}:[{kind:'measurement-quality',id:'fresh'}];};
  instance.render=()=>{};instance.renderRecords=()=>{};instance.options=()=>{};instance.changed=()=>{};
  await instance.inspect();
  assert.equal(focused,true);assert.equal(instance.camera,'camera-west');
  assert.deepEqual(reads,['/calibration','/calibration/records']);
  assert.equal(instance.records[0].id,'fresh');
  assert.match(nodes['calibration-record-status'].textContent,/Checking/);
});

for(const changed of ['test','camera','capture','selected'])test(`late saved geometry cannot replace changed ${changed}`,async()=>{
  const {instance}=consoleFixture();let resolve;const displayed=[];
  instance.geometryMode='capture';instance.selected='sample/capture-a';
  instance.geometry=value=>displayed.push(value);
  instance.request=()=>new Promise(done=>resolve=done);
  const pending=instance.renderGeometry();instance[changed]='changed';
  resolve({title:'Old capture',scope:'Saved',scene:{objects:[{name:'old'}]},numbers:{}});
  await pending;assert.deepEqual(displayed,[null]);
});

test('returning to cell view invalidates pending geometry without a mutation request',async()=>{
  const {instance}=consoleFixture();let resolve;const displayed=[];
  instance.geometryMode='capture';instance.geometry=value=>displayed.push(value);
  instance.request=(url,body)=>{assert.equal(body,undefined);assert.match(url,/^\/calibration\/geometry\?/);return new Promise(done=>resolve=done);};
  const pending=instance.renderGeometry();instance.clearGeometry();
  resolve({title:'stale',scope:'saved',numbers:{}});await pending;
  assert.deepEqual(displayed,[null,null]);assert.equal(instance.geometryMode,'cell');
});
