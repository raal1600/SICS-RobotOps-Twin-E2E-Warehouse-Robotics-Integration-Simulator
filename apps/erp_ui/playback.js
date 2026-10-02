"use strict";
// Presentation only: all motion comes from evaluated Blender frames. No command writes.
class MotionPlayer {
  constructor() {
    this.canvas = document.getElementById("motion-canvas");
    this.ctx = this.canvas.getContext("2d");
    this.job = null; this.recording = null; this.cursor = 0;
    this.playing = false; this.speed = 1; this.yaw = -0.35; this.last = null;
    this.byId = id => document.getElementById(id);
    this.byId("motion-play").onclick = () => {
      if (!this.playing && this.atEnd() && this.recording.complete) this.cursor = 0;
      this.playing = !this.playing; this.controls();
    };
    this.byId("motion-replay").onclick = () => {this.cursor = 0; this.playing = true; this.controls();};
    this.byId("motion-scrub").oninput = event => {
      this.cursor = Math.min(Number(event.target.value), this.recording.frames.length - 1);
      this.playing = false; this.controls(); this.draw();
    };
    this.byId("motion-speed").onchange = event => {this.speed = Number(event.target.value);};
    this.byId("motion-rotate").onclick = () => {this.yaw += Math.PI / 6; this.draw();};
    requestAnimationFrame(time => this.tick(time));
    this.draw();
  }
  select(job) {
    if (this.job === job) return;
    this.job = job; this.recording = null; this.cursor = 0; this.playing = false;
    this.byId("motion-state").textContent = "Waiting for recorded motion";
    this.byId("motion-detail").textContent = "The scene appears when Blender supplies evaluated poses.";
    this.byId("motion-import").hidden = true;
    this.controls(); this.draw();
  }
  update(data) {
    if (data.job_id !== this.job) return;
    const first = !this.recording;
    this.recording = data.recording;
    if (first && this.recording) {this.cursor = 0; this.playing = true;}
    if (!this.recording) this.playing = false;
    this.byId("motion-state").textContent = {
      WAITING: "Waiting for Blender", RECORDING: "Live recording", RECORDED: "Recorded motion",
      PARTIAL: "Partial recording · outcome uncertain", UNAVAILABLE: "No motion available"
    }[data.status];
    this.byId("motion-outcome").textContent = "Job: " + data.job_state;
    this.byId("motion-outcome").classList.toggle("uncertain", ["UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION"].includes(data.job_state));
    this.byId("motion-detail").textContent = data.recording
      ? `${data.recording.product_id} · ${data.command_id} · ${data.recording.frames.length}/100 frames received`
      : data.reason;
    this.byId("motion-import").hidden = !data.can_import;
    this.controls(); this.draw();
  }
  atEnd() { return this.recording && this.cursor >= this.recording.frames.length - 1; }
  controls() {
    for (const id of ["motion-play", "motion-replay", "motion-scrub", "motion-speed", "motion-rotate"]) {
      this.byId(id).disabled = !this.recording;
    }
    this.byId("motion-play").textContent = this.playing ? "Pause" : "Play";
    this.byId("motion-scrub").value = Math.round(this.cursor);
  }
  tick(time) {
    const delta = this.last === null ? 0 : Math.min((time - this.last) / 1000, 0.1);
    this.last = time;
    if (this.playing && this.recording) {
      this.cursor = Math.min(this.cursor + delta * 24 * this.speed, this.recording.frames.length - 1);
      if (this.atEnd() && this.recording.complete) this.playing = false;
      this.controls(); this.draw();
    }
    requestAnimationFrame(next => this.tick(next));
  }
  draw() {
    const c = this.ctx, w = this.canvas.width, h = this.canvas.height;
    c.clearRect(0, 0, w, h);
    const background = c.createLinearGradient(0, 0, 0, h);
    background.addColorStop(0, "#101f2d"); background.addColorStop(1, "#203b4b");
    c.fillStyle = background; c.fillRect(0, 0, w, h);
    const scale = 210, cos = Math.cos(this.yaw), sin = Math.sin(this.yaw);
    const camera = ([x, y, z]) => [cos*x-sin*y, sin*x+cos*y, z];
    const project = point => {const [x,y,z] = camera(point); return [w/2+x*scale, h*0.70+y*scale*0.5-z*scale];};
    const line = (a,b,color) => {c.beginPath();c.moveTo(...project(a));c.lineTo(...project(b));c.strokeStyle=color;c.stroke();};
    c.lineWidth = 1;
    for (let n=-8;n<=8;n++) {
      line([n/4,-2,-0.12],[n/4,2,-0.12],"#345260");
      line([-2,n/4,-0.12],[2,n/4,-0.12],"#345260");
    }
    if (!this.recording) {
      c.fillStyle="#c1d9e2";c.font="20px system-ui";c.textAlign="center";
      c.fillText("Select an order to see its recorded motion",w/2,h/2-40);
      this.byId("motion-phase").textContent="No frames recorded";
      return;
    }
    const rec = this.recording, index = Math.min(Math.floor(this.cursor),rec.frames.length-1);
    const frame = rec.frames[index], next = rec.frames[Math.min(index+1,rec.frames.length-1)];
    const fraction = this.cursor-index;
    const position = obj => {
      const a=frame.positions[obj.name] || obj.position, b=next.positions[obj.name] || a;
      return a.map((v,i) => v+(b[i]-v)*fraction);
    };
    const faces=[];
    for (const obj of rec.objects) {
      const center=position(obj), s=obj.size.map(v=>v/2);
      const vertices=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]
        .map(corner=>corner.map((v,i)=>center[i]+v*s[i]));
      [[0,1,2,3],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0],[4,7,6,5]].forEach((indices,i)=>{
        const points=indices.map(v=>vertices[v]);
        const depth=points.reduce((sum,p)=>{const q=camera(p);return sum+q[1]-q[2]*2;},0)/4;
        faces.push({points,depth,color:obj.color,shade:[0.5,0.72,0.85,0.67,0.8,1.12][i],selected:obj.product_id===rec.product_id});
      });
    }
    faces.sort((a,b)=>b.depth-a.depth);
    for (const face of faces) {
      c.beginPath();face.points.forEach((p,i)=>i ? c.lineTo(...project(p)) : c.moveTo(...project(p)));c.closePath();
      c.fillStyle=`rgb(${face.color.map(v=>Math.min(255,Math.round(v*255*face.shade))).join(",")})`;c.fill();
      c.lineWidth=face.selected?1.8:0.6;c.strokeStyle=face.selected?"#ffdc87":"#24424c";c.stroke();
    }
    const label=(value,p,color)=>{const [x,y]=project(p);c.font="bold 13px system-ui";c.textAlign="center";
      const width=c.measureText(value).width+18;c.fillStyle="#101f2de8";c.fillRect(x-width/2,y-17,width,25);
      c.fillStyle=color;c.fillText(value,x,y);};
    rec.objects.filter(o=>["SourceTote","DestinationTote"].includes(o.name)).forEach(o=>{
      label(o.name==="SourceTote"?"SOURCE":"DESTINATION",[o.position[0],o.position[1]-0.48,0.01],"#b4d9e6");
    });
    const product=rec.objects.find(o=>o.product_id===rec.product_id);
    if(product){const p=position(product);label(rec.product_id.replace("product-","").toUpperCase(),[p[0],p[1],p[2]+0.18],"#ffdc87");}
    this.byId("motion-phase").textContent=`${frame.phase} · Frame ${index+1}/100 · ${(this.cursor/24).toFixed(1)} s simulated`;
    this.canvas.setAttribute("aria-label",`Recorded Blender motion: ${frame.phase}, frame ${index+1}. Product ${rec.product_id}.`);
  }
}
