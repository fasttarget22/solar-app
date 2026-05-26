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
@app.route('/')
def index():
    return 'Solar Monitor API Running! Go to /health to check status.'
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
