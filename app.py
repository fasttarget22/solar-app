from flask import Flask,request,jsonify
import os,requests as r
app=Flask(__name__)
SU=os.environ.get('SUPABASE_URL','')
SK=os.environ.get('SUPABASE_KEY','')
H={'apikey':SK,'Authorization':'Bearer '+SK,'Content-Type':'application/json','Prefer':'return=representation'}
@app.route('/health')
def health():
    return 'OK'
@app.route('/api/log',methods=['POST'])
def log():
    d=request.json or {}
    res=r.post(SU+'/rest/v1/readings',headers=H,json={'battery_kwh':d.get('battery_kwh',0),'solar_kwh':d.get('solar_kwh',0),'utility_kwh':d.get('utility_kwh',0),'battery_pct':d.get('battery_pct',0),'load_w':d.get('load_w',0),'notes':d.get('notes','')})
    return jsonify({'ok':res.ok})
@app.route('/api/history')
def history():
    res=r.get(SU+'/rest/v1/readings?order=id.desc&limit=50',headers=H)
    return jsonify(res.json() if res.ok else [])
@app.route('/api/summary')
def summary():
    res=r.get(SU+'/rest/v1/readings?order=id.desc&limit=1000',headers=H)
    rows=res.json() if res.ok else []
    if not rows:return jsonify({'total_solar':0,'total_battery':0,'total_utility':0,'avg_battery_pct':0,'peak_load':0,'record_count':0,'today':{'s':0,'b':0,'u':0}})
    return jsonify({'total_solar':sum(x.get('solar_kwh',0)for x in rows),'total_battery':sum(x.get('battery_kwh',0)for x in rows),'total_utility':sum(x.get('utility_kwh',0)for x in rows),'avg_battery_pct':sum(x.get('battery_pct',0)for x in rows)/len(rows),'peak_load':max((x.get('load_w',0)for x in rows),default=0),'record_count':len(rows),'today':{'s':0,'b':0,'u':0}})

@app.route('/dashboard')
def dashboard():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Solar Monitor</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#080c10;color:#c8e6c9;font-family:monospace}header{padding:16px 24px;border-bottom:1px solid #1a2a1a;display:flex;justify-content:space-between;align-items:center}.logo{color:#00ff88;font-size:18px;letter-spacing:4px}.dot{width:8px;height:8px;border-radius:50%;background:#00ff88;box-shadow:0 0 8px #00ff88;animation:p 2s infinite}@keyframes p{0%,100%{opacity:1}50%{opacity:.3}}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding:16px}.card{background:#0d1318;border:1px solid #1a2a1a;padding:16px;border-top:2px solid #00ff88}.card.a{border-top-color:#ffaa00}.card.b{border-top-color:#00aaff}.label{font-size:10px;letter-spacing:2px;color:#4a6a4a;margin-bottom:8px}.value{font-size:28px;font-weight:700;color:#00ff88}.card.a .value{color:#ffaa00}.card.b .value{color:#00aaff}.unit{font-size:11px;color:#4a6a4a;margin-top:4px}.bar{margin-top:10px;height:5px;background:#003322;border-radius:3px}.fill{height:100%;background:#00ff88;border-radius:3px;transition:width 1s}.table-wrap{padding:0 16px 16px;overflow-x:auto}.thead{font-size:10px;letter-spacing:2px;color:#4a6a4a;padding:8px 0;border-bottom:1px solid #1a2a1a;margin-bottom:8px}table{width:100%;border-collapse:collapse;font-size:11px}th{text-align:left;color:#4a6a4a;padding:6px 8px;border-bottom:1px solid #1a2a1a}td{padding:6px 8px;border-bottom:1px solid rgba(26,42,26,.4)}.g{color:#00ff88}.am{color:#ffaa00}.bl{color:#00aaff}.btn{margin:0 16px 16px;background:none;border:1px solid #1a2a1a;color:#4a6a4a;font-family:monospace;font-size:11px;padding:8px 16px;cursor:pointer;letter-spacing:2px}.ts{font-size:10px;color:#4a6a4a;padding:0 16px 8px}</style></head><body><header><div class="logo">SOLAR MONITOR</div><div class="dot"></div></header><div class="grid"><div class="card"><div class="label">TOTAL SOLAR</div><div class="value" id="ts">--</div><div class="unit">kWh generated</div></div><div class="card a"><div class="label">BATTERY</div><div class="value" id="tb">--</div><div class="unit">kWh stored</div></div><div class="card b"><div class="label">GRID USAGE</div><div class="value" id="tu">--</div><div class="unit">kWh from grid</div></div><div class="card a"><div class="label">AVG BATTERY</div><div class="value" id="ab">--</div><div class="unit">% charge</div><div class="bar"><div class="fill" id="bf" style="width:0"></div></div></div><div class="card"><div class="label">PEAK LOAD</div><div class="value" id="pl">--</div><div class="unit">watts</div></div><div class="card b"><div class="label">READINGS</div><div class="value" id="rc">--</div><div class="unit">logged</div></div></div><div class="ts" id="lu"></div><button class="btn" onclick="load()">⟳ REFRESH</button><div class="table-wrap"><div class="thead">// RECENT READINGS</div><table><thead><tr><th>#</th><th>Solar</th><th>Battery</th><th>Grid</th><th>Batt%</th><th>Load W</th></tr></thead><tbody id="tb2"></tbody></table></div><script>const A='';async function load(){try{const s=await fetch(A+'/api/summary'),d=await s.json();document.getElementById('ts').textContent=d.total_solar.toFixed(2);document.getElementById('tb').textContent=d.total_battery.toFixed(2);document.getElementById('tu').textContent=d.total_utility.toFixed(2);const p=d.avg_battery_pct.toFixed(1);document.getElementById('ab').textContent=p;document.getElementById('bf').style.width=p+'%';document.getElementById('pl').textContent=d.peak_load.toFixed(0);document.getElementById('rc').textContent=d.record_count;const h=await fetch(A+'/api/history'),r=await h.json();document.getElementById('tb2').innerHTML=r.slice(0,15).map((x,i)=>'<tr><td style="color:#4a6a4a">'+(r.length-i)+'</td><td class="g">'+x.solar_kwh.toFixed(2)+'</td><td class="am">'+x.battery_kwh.toFixed(2)+'</td><td class="bl">'+x.utility_kwh.toFixed(2)+'</td><td>'+x.battery_pct.toFixed(1)+'%</td><td>'+x.load_w.toFixed(0)+'W</td></tr>').join('');document.getElementById('lu').textContent='// Updated: '+new Date().toLocaleTimeString()}catch(e){}}load();setInterval(load,30000);</script></body></html>"""

@app.route('/')
def index():
    return 'Solar Monitor API Running! Go to /health to check status.'
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
