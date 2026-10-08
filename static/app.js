
let orgs=[], current=null;
const $=id=>document.getElementById(id);
document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));document.querySelectorAll(".tabpage").forEach(x=>x.classList.remove("active"));b.classList.add("active");$(b.dataset.tab).classList.add("active");if(b.dataset.tab==="saved")loadSaved();});
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
async function api(url,opt={}){let r=await fetch(url,opt),d=await r.json();if(!r.ok)throw Error(d.error||"خطا");return d}
async function loadAll(){orgs=await api("/api/organizations");renderOrgs();renderChecks();let a=await api("/api/analyses"),c=await api("/api/cards");$("mOrg").textContent=orgs.length;$("mAna").textContent=a.length;$("mCard").textContent=c.length;loadSettings()}
function renderOrgs(){
 $("orgList").innerHTML=orgs.map(o=>`<div class="orgcard"><span class="tag">${esc(o.role)}</span><h3>${esc(o.name)}</h3><p>${esc(o.description||"بدون توضیح")}</p><div class="actions"><button class="secondary danger" onclick="delOrg(${o.id})">حذف</button></div></div>`).join("")||`<div class="panel" style="padding:25px">هنوز مجموعه‌ای ثبت نشده است.</div>`;
 let axis=$("axis");axis.innerHTML=orgs.map(o=>`<option value="${o.id}">${esc(o.name)}</option>`).join("");
}
function renderChecks(){let axis=+$("axis").value;$("orgChecks").innerHTML=orgs.filter(o=>o.id!==axis).map(o=>`<label class="check"><input type="checkbox" value="${o.id}" checked> ${esc(o.name)} <small>(${esc(o.role)})</small></label>`).join("")}
$("axis").onchange=renderChecks;
function openOrg(){$("modal").classList.remove("hidden")}
function closeOrg(){$("modal").classList.add("hidden")}
async function saveOrg(){
 let data;try{data=JSON.parse($("odata").value)}catch(e){alert("JSON داده مجموعه معتبر نیست.");return}
 try{await api("/api/organizations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:$("oname").value,role:$("orole").value,description:$("odesc").value,data})});closeOrg();["oname","odesc"].forEach(x=>$(x).value="");await loadAll()}catch(e){alert(e.message)}
}
async function delOrg(id){if(confirm("این مجموعه حذف شود؟")){await api("/api/organizations/"+id,{method:"DELETE"});loadAll()}}
async function importFile(){
 let f=$("fileInput").files[0];if(!f)return alert("فایل را انتخاب کنید.");
 let fd=new FormData();fd.append("file",f);try{let d=await api("/api/import",{method:"POST",body:fd});$("importPreview").textContent=JSON.stringify(d.records,null,2);window.lastImport=d.records}catch(e){alert(e.message)}
}
async function loadSettings(){
 try{let s=await api("/api/settings");$("api_base").value=s.api_base;$("api_key").placeholder=s.api_key||"کلید API";$("model").value=s.model;$("temperature").value=s.temperature;$("max_tokens").value=s.max_tokens;$("extra_headers").value=s.extra_headers||"{}"}catch(e){}
}
async function saveSettings(){
 try{JSON.parse($("extra_headers").value);await api("/api/settings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({api_base:$("api_base").value,api_key:$("api_key").value,model:$("model").value,temperature:$("temperature").value,max_tokens:$("max_tokens").value,extra_headers:$("extra_headers").value})});alert("تنظیمات ذخیره شد.")}catch(e){alert(e.message)}
}
async function runAnalysis(){
 let axis=orgs.find(o=>o.id===+$("axis").value);let ids=[...document.querySelectorAll("#orgChecks input:checked")].map(x=>+x.value);let others=orgs.filter(o=>ids.includes(o.id));
 let imported=window.lastImport?{imported_file_data:window.lastImport}:{};
 setBusy(true);
 try{let r=await api("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title:$("title").value,axis,organizations:others.map(o=>({...o,data:{...JSON.parse(o.data||"{}"),...imported}})),context:$("context").value})});current=r;renderResult(r)}catch(e){alert(e.message)}finally{setBusy(false)}
}
function setBusy(x){$("statusText").textContent=x?"در حال تحلیل هوشمند...":"سیستم آماده است";$("dot").style.background=x?"#f4c96b":"#4de3c2"}
function renderResult(r){
 $("result").classList.remove("hidden");$("resultTitle").textContent=r.summary||"نتیجه تحلیل";$("summary").textContent=r.summary||"";$("strategy").textContent=r.network_strategy||"";
 $("exportBtn").href="/api/export/"+r._analysis_id;
 renderGraph(r.nodes||[],r.edges||[]);
 $("cards").innerHTML=(r.recommendations||[]).map((x,i)=>`<div class="card"><span class="priority">${esc(x.priority)}</span><h3>${esc(x.title)}</h3><div class="route">${esc(x.from)} → ${esc(x.to)}</div><p><b>پیشنهاد:</b> ${esc(x.offer)}</p><p><b>جریان مشتری:</b> ${esc(x.customer_flow)}</p><p><b>منطق تجاری:</b> ${esc(x.commercial_logic)}</p><p><b>اجرا:</b> ${esc(x.implementation)}</p><p><b>ریسک:</b> ${esc(x.risk)} | <b>اعتماد:</b> ${esc(x.confidence)}%</p><button class="secondary" onclick='saveCard(${JSON.stringify(x).replace(/'/g,"&#39;")})'>ذخیره کارت</button></div>`).join("");
 $("signals").innerHTML=[...(r.external_signals||[]).map(x=>`<div class="sidecard"><b>${esc(x.signal)}</b><br>${esc(x.source||"") }<br>${esc(x.impact||"")}</div>`),...(r.assumptions||[]).map(x=>`<div class="sidecard">فرض: ${esc(x)}</div>`)].join("")||"<div class=sidecard>موردی ثبت نشده است.</div>";
 $("campaigns").innerHTML=(r.campaigns||[]).map(c=>`<div class="campaign"><b>${esc(c.name)}</b><ol>${(c.sequence||[]).map(s=>`<li>${esc(s.action)} — ${esc(s.timing)}</li>`).join("")}</ol></div>`).join("");
}
function renderGraph(nodes,edges){
 if(window.cy)window.cy.destroy();
 window.cy=cytoscape({container:$("cy"),elements:{nodes:nodes.map(n=>({data:{id:n.id,label:n.label,score:n.score}})),edges:edges.map((e,i)=>({data:{id:"e"+i,source:e.source,target:e.target,weight:e.weight,relationship:e.relationship}}))},
 style:[{selector:"node",style:{label:"data(label)",color:"#edf5ff","background-color":"#1b5872","border-color":"#4de3c2","border-width":2,"text-valign":"center","text-halign":"center","font-size":12,"width":42,"height":42}},
 {selector:"edge",style:{"curve-style":"bezier","target-arrow-shape":"triangle","target-arrow-color":"#65a7ff","line-color":"#4d83ad","width":"mapData(weight,0,100,1,9)","opacity":.8,label:"data(weight)","color":"#9bb7d0","font-size":9}},
 {selector:"node:selected",style:{"background-color":"#4de3c2","color":"#061a17","width":55,height:55}}],
 layout:{name:"cose",animate:true,padding:50,idealEdgeLength:150,nodeRepulsion:8000}});
}
async function saveCard(card){await api("/api/cards",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({analysis_id:current?current._analysis_id:null,card})});alert("کارت ذخیره شد.");loadAll()}
async function loadSaved(){
 let a=await api("/api/analyses");$("savedList").innerHTML=a.map(x=>`<div class="saveditem"><div><b>${esc(x.title)}</b><div class="muted">${esc(x.created_at)}</div></div><div><button class="secondary" onclick="openSaved(${x.id})">مشاهده</button> <a class="secondary" href="/api/export/${x.id}">JSON</a></div></div>`).join("")||"<div class=panel style='padding:25px'>هنوز تحلیلی ذخیره نشده است.</div>";
}
async function openSaved(id){let x=await api("/api/analyses/"+id);current=x.payload;current._analysis_id=id;document.querySelector('[data-tab="analysis"]').click();renderResult(current)}
loadAll();
