"use strict";
// Read-only scenario playback. Event pacing is presentation time, not measured latency.
const scenarioNames = {
  DROP_ACK_AFTER_EFFECT: "Acknowledgement lost after effect",
  DROP_ACK_BEFORE_EFFECT: "Acknowledgement lost before effect",
  CONTRADICTORY_OBSERVATION: "Contradictory observation",
  LOW_CONFIDENCE_OBSERVATION: "Low-confidence observation",
  STALE_OBSERVATION: "Stale observation", MISSING_OBSERVATION: "Missing observation",
  POSE_UNCERTAINTY: "Pose uncertainty", LOGICAL_ESTOP: "Logical E-stop",
  CELL_FAULT: "Cell fault", BRAIN_INVALID_OUTPUT: "Invalid Brain output",
  BRAIN_TIMEOUT: "Brain timeout", ROBOT_COMMAND_FAILURE: "Robot command failure"
};
function interpolateQuaternion(a,b,t){
  let dot=a.reduce((sum,v,i)=>sum+v*b[i],0);
  if(dot<0){b=b.map(v=>-v);dot=-dot;}
  const angle=Math.acos(Math.min(1,dot));
  const q=angle<0.001?a.map((v,i)=>v+(b[i]-v)*t):a.map((v,i)=>(v*Math.sin((1-t)*angle)+b[i]*Math.sin(t*angle))/Math.sin(angle));
  const norm=Math.hypot(...q);return q.map(v=>v/norm);
}
class MotionPlayer {
  constructor() {
    this.view=new SceneView(document.getElementById("motion-canvas"));
    this.byId=id=>document.getElementById(id);
    this.job=null;this.scene=null;this.preview=null;this.recording=null;this.data=null;this.delivery=null;
    this.cursor=0;this.track=[];this.playing=false;this.manualPause=false;this.speed=1;this.last=null;
    this.byId("motion-play").onclick=()=>{
      if(!this.playing&&this.atEnd())this.cursor=0;
      this.playing=!this.playing;this.manualPause=!this.playing;this.controls();
    };
    this.byId("motion-replay").onclick=()=>{this.cursor=0;this.playing=true;this.manualPause=false;this.controls();};
    this.byId("motion-scrub").oninput=e=>{this.cursor=Math.max(0,Math.min(Number(e.target.value),this.limit()));this.playing=false;this.manualPause=true;this.controls();this.draw();};
    this.byId("motion-speed").onchange=e=>{this.speed=Number(e.target.value);};
    this.byId("motion-rotate").onclick=()=>this.view.rotate();
    this.byId("motion-home").onclick=()=>this.view.reset();
    this.byId("motion-zoom-in").onclick=()=>this.view.zoom(0.8);
    this.byId("motion-zoom-out").onclick=()=>this.view.zoom(1.25);
    for(const [id,name] of [["camera-operator","OperatorOverview"],["camera-overhead","OverheadObservation"],["camera-side","SideInspection"],["camera-follow","FollowTCP"]]){
      this.byId(id).onclick=()=>this.view.viewpoint(name);
    }
    for(const [id,delta] of [["motion-step-back",-1],["motion-step-forward",1]]){
      this.byId(id).onclick=()=>{this.cursor=Math.max(0,Math.min(this.limit(),Math.floor(this.cursor)+delta));this.playing=false;this.manualPause=true;this.controls();this.draw();};
    }
    requestAnimationFrame(time=>this.tick(time));this.controls();
  }
  previewScene(scene){this.preview=scene;if(!this.job){this.scene=scene;this.byId("motion-state").textContent="3D cell ready";this.controls();this.draw();}}
  pause(){this.playing=false;this.manualPause=true;this.controls();}
  select(job){
    if(this.job===job)return;
    this.job=job;this.recording=null;this.scene=this.preview;this.data=null;this.delivery=null;this.track=[];
    this.cursor=0;this.playing=false;this.manualPause=false;
    this.byId("motion-state").textContent="Loading selected scenario";
    if(!job){
      this.byId("motion-state").textContent="3D cell ready";
      this.byId("motion-outcome").textContent="Current cell";
      this.byId("motion-outcome").classList.toggle("uncertain",false);
      this.byId("motion-scenario").textContent="Choose an execution scenario on the left.";
      this.byId("motion-detail").textContent="Current scene. Saved orders retain their original replay.";
    }
    this.byId("motion-import").hidden=true;this.controls();this.draw();
  }
  buildTrack(data){
    const track=[],events=(data.events||[]).filter(e=>e.state_after||["FAULT_INJECTED","PLAN_VALIDATED","PICK_EFFECT","OBSERVATION_CAPTURED","COMMAND_REJECTED","COMMAND_FAILED"].includes(e.event_type));
    let inserted=false;
    const motion=()=>{if(inserted||!data.recording)return;inserted=true;data.recording.frames.forEach((frame,i)=>track.push({kind:"motion",frame:i}));};
    for(const event of events){
      for(let i=0;i<12;i++)track.push({kind:"event",event,afterMotion:inserted});
      if(event.state_after==="EXECUTING"){
        motion();
        // A partial recording stops here: later events must not suggest a completed trajectory.
        if(data.recording&&!data.recording.complete)return track;
      }
    }
    motion();return track;
  }
  update(data){
    if(data.job_id!==this.job)return;
    this.acceptClips([data],null,data.scene);
  }
  updateDelivery(delivery){
    if(this.job!=="delivery:"+delivery.delivery_id)return;
    this.acceptClips(delivery.jobs,delivery,delivery.scene);
  }
  acceptClips(clips,delivery,scene){
    const wasEnd=this.atEnd(),first=!this.data,oldLength=this.track.length;
    const previousStep=this.track[Math.floor(this.cursor)],fraction=this.cursor-Math.floor(this.cursor);
    const oldClipOffset=previousStep?this.track.filter((step,i)=>i<Math.floor(this.cursor)&&step.clip.job_id===previousStep.clip.job_id).length:0;
    const data=clips.at(-1);
    this.delivery=delivery;this.data=data;this.scene=scene;this.recording=data?.recording||null;this.track=[];
    for(const [index,clip] of clips.entries()){
      this.track.push(...this.buildTrack(clip).map(step=>({...step,clip,index})));
      if(clip.recording&&!clip.recording.complete)break;
    }
    // New events on an earlier pick must not move a paused cursor to another product.
    if(previousStep){
      const start=this.track.findIndex(step=>step.clip.job_id===previousStep.clip.job_id);
      if(start>=0)this.cursor=start+oldClipOffset+fraction;
    }
    if((first||this.track.length>oldLength&&wasEnd)&&!this.manualPause)this.playing=true;
    if(!this.track.length)this.playing=false;
    this.cursor=Math.min(this.cursor,this.limit());
    this.byId("motion-state").textContent=delivery?(clips.length?"Full delivery replay · "+clips.length+" product executions":"3D cell ready") :data.recording
      ? ({RECORDING:"Live Blender motion",RECORDED:"Recorded 3D scenario",PARTIAL:"Partial motion - outcome uncertain"}[data.status]||data.status)
      : "Scenario events - stationary scene";
    const uncertain=clips.some(clip=>["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(clip.job_state));
    const completed=clips.filter(clip=>clip.job_state==="COMPLETED").length;
    this.byId("motion-outcome").textContent=delivery?(clips.length?`${completed}/${clips.length} completed${uncertain?" · uncertain outcome":""}`:"Ready for a new delivery"):"Job: "+data.job_state;
    const fault=clips.flatMap(clip=>clip.events||[]).find(e=>e.event_type==="FAULT_INJECTED");
    this.byId("motion-scenario").textContent=delivery&&!clips.length?"New delivery · ready for the selected scenario.":(delivery?"Delivery scenario: ":"Execution: ")+(scenarioNames[fault?.reason]||"Happy path");
    this.byId("motion-outcome").classList.toggle("uncertain",uncertain);
    const provenance=data?.recording?"Original Blender poses":scene.source==="SAVED_START_SCENE"?"Saved starting scene":"Current cell reference - historical starting scene unavailable";
    const missing=clips.filter(clip=>!clip.recording).length;
    this.byId("motion-detail").textContent=delivery
      ? (clips.length?`${delivery.reason}${missing?` ${missing} executions have no motion recording; their events and scene provenance remain explicit.`:""}`:"Create an order to start this delivery. Previous deliveries remain available above.")
      : `${provenance}. ${data.reason}`;
    this.byId("motion-import").hidden=!!delivery||!data?.can_import;
    this.controls();this.draw();
  }
  limit(){return Math.max(0,this.track.length-1);}
  atEnd(){return this.cursor>=this.limit();}
  controls(){
    for(const id of ["motion-play","motion-replay","motion-scrub","motion-speed","motion-step-back","motion-step-forward"])this.byId(id).disabled=!this.track.length;
    for(const id of ["motion-rotate","motion-home","motion-zoom-in","motion-zoom-out"])this.byId(id).disabled=!this.scene&&!this.recording;
    this.byId("motion-play").textContent=this.playing?"Pause":"Play";
    this.byId("motion-scrub").max=this.limit();this.byId("motion-scrub").value=Math.round(this.cursor);
  }
  tick(time){
    const delta=this.last===null?0:Math.min((time-this.last)/1000,0.1);this.last=time;
    if(this.playing&&this.track.length){
      this.cursor=Math.min(this.cursor+delta*24*this.speed,this.limit());
      if(this.atEnd()&&!['WAITING','RECORDING'].includes(this.track.at(-1)?.clip.status))this.playing=false;
      this.controls();
    }
    // Draw at the recording rate. A CPU WebGL renderer must share the host
    // with Blender; display refresh (60/144 Hz) is not a simulation clock.
    const interval=1000/24;
    if(this.lastDraw===undefined||time-this.lastDraw>=interval){
      this.lastDraw=this.lastDraw===undefined?time:time-(time-this.lastDraw)%interval;
      this.draw();
    }
    requestAnimationFrame(next=>this.tick(next));
  }
  pose(){
    const step=this.track[Math.floor(this.cursor)],data=step?.clip||this.data,rec=data?.recording;
    const objects=rec?.objects||data?.scene?.objects||this.scene?.objects||[];
    let positions={},transforms={},phase="Cell ready",event=null;
    if(step?.kind==="motion"){
      const frame=rec.frames[step.frame],next=rec.frames[Math.min(step.frame+1,rec.frames.length-1)],fraction=this.cursor-Math.floor(this.cursor);
      for(const obj of objects){const a=frame.positions[obj.name]||obj.position,b=next.positions[obj.name]||a;positions[obj.name]=a.map((v,i)=>v+(b[i]-v)*fraction);}
      if(frame.transforms){
        for(const obj of objects){
          const a=frame.transforms[obj.name]||obj,b=next.transforms?.[obj.name]||a;
          transforms[obj.name]={
            position:a.position.map((v,i)=>v+(b.position[i]-v)*fraction),
            quaternion_xyzw:interpolateQuaternion(a.quaternion_xyzw,b.quaternion_xyzw,fraction),
            scale:(a.scale||[1,1,1]).map((v,i)=>v+((b.scale||[1,1,1])[i]-v)*fraction),
            visible:a.visible!==false,
          };
        }
      }
      phase=`${frame.phase} - Blender frame ${step.frame+1}/${rec.total_frames||100} - ${(frame.sim_time_s??step.frame/(rec.fps||24)).toFixed(1)} s simulated`;
    }else if(step){
      event=step.event;phase=event.state_after||event.event_type;
      if(step.afterMotion&&rec){positions=rec.frames.at(-1).positions;transforms=rec.frames.at(-1).transforms||{};}
    }
    if(this.delivery&&step)phase=`${step.index+1}/${this.delivery.jobs.length} · ${data.product_id} · ${phase}`;
    return {objects,positions,transforms,phase,event,data};
  }
  draw(){
    const {objects,positions,transforms,phase,event,data}=this.pose();
    this.view.configure?.((data?.scene||this.scene)?.cameras);
    this.view.render(objects,positions,data?.product_id,transforms);
    let message=this.job?"Waiting for persisted execution events":"Environment ready. Create and run an order to begin.";
    let tone="normal";
    if(event){
      message=event.event_type==="FAULT_INJECTED"?"Scenario configured: "+(scenarioNames[event.reason]||event.reason):event.reason;
      if(event.reason.startsWith("PLANNING_REJECTED:")){
        const reason=event.reason.slice("PLANNING_REJECTED:".length);
        message=reason==="SOURCE_NOT_OBSERVED"?"The product was not observed at the source. If it was already picked, use Start fresh scene before creating a new order."
          :reason==="CELL_NOT_READY"?"The cell is stopped or faulted. Reset logical cell state before creating another order."
          :reason==="BRAIN_TIMEOUT"?"Brain timed out. No action plan was accepted."
          :"Action planning or validation rejected: "+reason;
      }
      if(event.state_after==="UNKNOWN_OUTCOME")message="Outcome uncertain. Reconcile the original command; do not issue another pick. "+event.reason;
      if(event.state_after==="REQUIRES_INTERVENTION")message="Evidence was inconclusive. Request another observation to continue investigating the original pick. "+event.reason;
      if(["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(event.state_after))tone="uncertain";
      if(event.state_after==="FAILED"||/ESTOP|CELL_FAULT/.test(event.reason))tone="blocked";
      if(event.state_after==="COMPLETED")tone="success";
    }else if(data?.recording&&this.track.length)message="Machine and product follow evaluated Blender poses.";
    if(data&&!data.recording){
      const dispatched=(data.events||[]).some(e=>e.state_after==="EXECUTING");
      const rejected=(data.events||[]).some(e=>["COMMAND_REJECTED","COMMAND_FAILED"].includes(e.event_type));
      message+=" "+(!dispatched?"No pick dispatched at this stage.":rejected?"Controller recorded no pick effect. Machine and product stay still.":"No motion recording is available; a stationary view is not proof of no effect.");
      if(data.scene.source==="CURRENT_WORLD_REFERENCE")message+=" Current cell reference; historical starting scene unavailable.";
    }
    const banner=this.byId("motion-event");
    if(banner.textContent!==message)banner.textContent=message;
    if(banner.dataset.tone!==tone)banner.dataset.tone=tone;
    if(this.byId("motion-phase").textContent!==phase)this.byId("motion-phase").textContent=phase;
    const step=this.track[Math.floor(this.cursor)];
    const frame=step?.kind==="motion"?data.recording.frames[step.frame]:step?.afterMotion?data?.recording?.frames.at(-1):null;
    this.byId("motion-tool").textContent=frame?.schema_version==="2.0"?`Replay tool: ${frame.active_tool_id||"empty flange"} · ${frame.rack_tool_ids?.length??0} tools in rack`:"";
    const description=`3D warehouse cell. ${phase}. ${message}`;
    if(this.view.canvas.getAttribute("aria-label")!==description)this.view.canvas.setAttribute("aria-label",description);
  }
}
