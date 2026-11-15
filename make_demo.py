#!/usr/bin/env python3
"""Build demo/pull_the_source_demo.html (self-contained, offline replay). Embeds recorded runs from runs/eval/log.jsonl."""
import json, os, base64
H = os.path.dirname(os.path.abspath(__file__))
scen = json.load(open(f"{H}/data/eval_scenarios.json")); keys = {k["id"]: k for k in json.load(open(f"{H}/keys/eval_keys.json"))}
runs = {}
for l in open(f"{H}/runs/eval/log.jsonl"):
    r = json.loads(l); runs[r["call_id"]] = dict(response=r["response"], decision=r["parsed_decision"], relies=r["parsed_relies_on"], t=r["response_written_utc"], model=r["model"])
scores = json.load(open(f"{H}/results/eval_scores.json"))
png = base64.b64encode(open(f"{H}/results/results_chart.png", "rb").read()).decode()
DATA = json.dumps(dict(scen=scen, keys=keys, runs=runs, cond=scores["conditions"])).replace("</", "<\\/")
html = r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pull the Source — replay demo</title><style>
:root{--bg:#f6f5f1;--card:#fff;--ink:#16181c;--mut:#5d6068;--line:#dedcd3;--acc:#1f4fa8;--ok:#1d6b3a;--bad:#a8321f;--warn:#8a5a00}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:22px 28px 14px;border-bottom:1px solid var(--line);background:var(--card)}h1{margin:0;font-size:22px;letter-spacing:-.01em}
header p{margin:4px 0 0;color:var(--mut);max-width:70ch}.bar{display:flex;gap:14px;flex-wrap:wrap;align-items:end;padding:14px 28px;background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}
label{font-size:12px;color:var(--mut);display:block;margin-bottom:3px}select,button{font:inherit;padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--ink)}button{cursor:pointer}button:hover{border-color:var(--acc)}
main{display:grid;grid-template-columns:minmax(300px,5fr) minmax(340px,7fr);gap:18px;padding:18px 28px;max-width:1400px}@media(max-width:860px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:18px}h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin:0 0 10px}
.src{display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:start;padding:9px 0;border-top:1px solid var(--line)}.src:first-of-type{border-top:0}.sid{font-weight:700;font-variant-numeric:tabular-nums}
.src.w .txt{text-decoration:line-through;color:var(--mut)}.src button{font-size:12.5px;padding:4px 9px;white-space:nowrap}.rec{font-size:11px;color:var(--acc);display:block}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:3px 8px;border-radius:99px;border:1.5px solid}
.b-rec{color:var(--ok);border-color:var(--ok)}.b-ill{color:var(--warn);border-color:var(--warn);border-style:dashed}.b-live{color:var(--mut);border-color:var(--line)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:7px 8px;border-top:1px solid var(--line);vertical-align:top}th{font-size:12px;color:var(--mut);font-weight:600;border-top:0}
.pill{font-weight:700}.ok{color:var(--ok)}.bad{color:var(--bad)}s{color:var(--mut)}
pre{white-space:pre-wrap;word-wrap:break-word;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;background:#faf9f6;border:1px solid var(--line);border-radius:8px;padding:12px;margin:10px 0 0;max-height:420px;overflow:auto}
.dec{font-size:19px;font-weight:700;margin:8px 0 2px}.meta{font-size:12px;color:var(--mut)}.note{font-size:13px;color:var(--mut);margin:8px 0 0}img{max-width:100%;border:1px solid var(--line);border-radius:8px}
.legend{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}
</style></head><body>
<header><h1>Pull the Source</h1><p>When a source behind an AI recommendation is withdrawn, does the model revise the recommendation exactly when it should? Pick a scenario, then withdraw a source. This page works offline and replays recorded runs.</p>
<div class="legend"><span class="badge b-rec">Recorded model run</span><span class="badge b-ill">Illustrative · answer key only, no model run</span><span class="badge b-live">Live calls: not included in this build</span></div></header>
<div class="bar"><div><label for="sc">Scenario (fictional product)</label><select id="sc"></select></div><div><label for="co">Prompt condition</label><select id="co"><option value="A">A · ordinary prompt</option><option value="B">B · dependency table</option></select></div><div><button id="reset">Restore all sources</button></div><div class="meta" id="summ"></div></div>
<main><div><div class="card"><h2>Recommendation and requirements</h2><div id="rec"></div></div><div class="card"><h2>Source documents</h2><div id="srcs"></div><p class="note">Three withdrawals per scenario were run on the model (marked "recorded"). Withdrawing any other source shows only the rule-based answer key.</p></div>
<div class="card"><h2>Dependency table <span class="badge b-ill" style="margin-left:6px">Answer key · rule-based, not model output</span></h2><div id="dep"></div></div></div>
<div><div class="card"><h2>Initial recommendation <span class="badge b-rec" style="margin-left:6px">Recorded model run</span></h2><div id="init"></div></div><div class="card"><h2>After withdrawal</h2><div id="upd"></div></div>
<div class="card"><h2>Recorded results, all 12 scenarios</h2><img alt="Bar chart of correct decisions by branch for conditions A and B" src="data:image/png;base64,__PNG__"><p class="note">Chart is generated from the recorded outputs only. Synthetic dataset, one model, one sample per cell.</p></div></div></main>
<script>
const D=__DATA__;let cur=D.scen[0],cond="A",wd=null;const $=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
function gold(k,valid){if(valid.some(s=>k.sources[s].contradicts))return"Contradicted";for(const r of cur.requirements){if(!valid.some(s=>k.sources[s].supports===r.id))return"Insufficient evidence"}return"Supported"}
function runBlock(id,g){const r=D.runs[id];if(!r)return"";const ok=r.decision===g;return `<div class="dec">${esc(r.decision)} <span class="pill ${ok?"ok":"bad"}" style="font-size:13px">${ok?"✓ matches answer key":"✗ answer key: "+esc(g)}</span></div><div class="meta">Model said it relies on: ${esc((r.relies||[]).join(", ")||"none")} · call ${id} · ${esc(r.model)} · written ${esc(r.t)}</div><pre>${esc(r.response)}</pre>`}
function draw(){const k=D.keys[cur.id],ids=cur.sources.map(s=>s.id),valid=ids.filter(s=>s!==wd);
$("rec").innerHTML=`<p style="margin:0 0 8px;font-size:17px"><b>${esc(cur.recommendation)}</b></p>`+cur.requirements.map(r=>`<div><b>${r.id}</b> ${esc(r.text)}</div>`).join("");
const br={};cur.branches.forEach(b=>br[b.withdraw]=b.branch);
$("srcs").innerHTML=cur.sources.map(s=>`<div class="src ${s.id===wd?"w":""}"><div class="sid">${s.id}</div><div class="txt">${esc(s.text)}${br[s.id]?'<span class="rec">withdrawal recorded on model</span>':""}</div><div>${s.id===wd?"<b>withdrawn</b>":`<button data-s="${s.id}">Withdraw</button>`}</div></div>`).join("");
document.querySelectorAll("#srcs button").forEach(b=>b.onclick=()=>{wd=b.dataset.s;draw()});
$("dep").innerHTML="<table><tr><th>Requirement</th><th>Supporting sources</th><th>Status</th></tr>"+cur.requirements.map(r=>{const sup=ids.filter(s=>k.sources[s].supports===r.id),v=sup.filter(s=>s!==wd);return `<tr><td><b>${r.id}</b></td><td>${sup.map(s=>s===wd?`<s>${s}</s> withdrawn`:`${s} valid`).join("<br>")}</td><td class="pill ${v.length?"ok":"bad"}">${v.length?"established":"not established"}</td></tr>`}).join("")+`</table><p class="note">Answer-key decision now: <b>${gold(k,valid)}</b>. Withdrawal removes support; it does not prove the opposite.</p>`;
$("init").innerHTML=runBlock(`${cur.id}_${cond}_init`,k.initial_gold);
if(!wd){$("upd").innerHTML='<p class="note">Withdraw a source on the left to see what happens.</p>'}else if(br[wd]){const b=br[wd];$("upd").innerHTML=`<span class="badge b-rec">Recorded model run</span> <span class="meta">source ${wd} withdrawn · branch type: ${k.branches[b].type} · replayed from the same initial exchange</span>`+runBlock(`${cur.id}_${cond}_br${b}`,k.branches[b].gold)}else{$("upd").innerHTML=`<span class="badge b-ill">Illustrative · no model run</span><div class="dec">${gold(k,valid)}</div><p class="note">This withdrawal was not part of the experiment. The label above is computed by the answer-key rule, not by a model.</p>`}
const c=D.cond[cond],a=c.all_cases;$("summ").textContent=`Condition ${cond}, all 12 scenarios: initial ${c.initial_correct}/${c.initial_total} · post-update ${a.post_correct}/${a.post_total}`}
D.scen.forEach(s=>{const o=document.createElement("option");o.value=s.id;o.textContent=`${s.id} · ${s.product}`;$("sc").appendChild(o)});
$("sc").onchange=e=>{cur=D.scen.find(s=>s.id===e.target.value);wd=null;draw()};$("co").onchange=e=>{cond=e.target.value;draw()};$("reset").onclick=()=>{wd=null;draw()};draw();
</script></body></html>'''
os.makedirs(f"{H}/demo", exist_ok=True)
open(f"{H}/demo/pull_the_source_demo.html", "w").write(html.replace("__PNG__", png).replace("__DATA__", DATA))
print("demo written", os.path.getsize(f"{H}/demo/pull_the_source_demo.html"))
