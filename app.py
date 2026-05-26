from flask import Flask,request,jsonify
import os,requests as r,re
app=Flask(__name__)
SU=os.environ.get('SUPABASE_URL','')
SK=os.environ.get('SUPABASE_KEY','')
H={'apikey':SK,'Authorization':'Bearer '+SK,'Content-Type':'application/json','Prefer':'return=representation'}
DATA_URL="https://smartsolar.net.pk/index-data.php?dev_id=D8BC38AD6637&dev_dm=0&msp=4680"

def gv(t,field):
    m=re.search(field+r'.*?data_value[^>]*>(.*?)</div>',t,re.IGNORECASE|re.DOTALL)
    if m:
        nums=re.findall(r'[\d.]+',m.group(1))
        return float(nums[0]) if nums else 0.0
    return 0.0

def gs(t,field):
    m=re.search(field+r'.*?data_value[^>]*>(.*?)</div>',t,re.IGNORECASE|re.DOTALL)
    return m.group(1).strip() if m else ''

def scrape():
    try:
        res=r.get(DATA_URL,headers={'User-Agent':'Mozilla/5.0'},timeout=10)
        if not res.ok:return None
        t=re.sub(r'\s+',' ',res.text)
        solar_w=gv(t,r'PV Watt')
        load_w=gv(t,r'Output Load \(W\)')
        voltage=gv(t,r'Battery Volt')
        batt_pct=gv(t,r'Battery Status')
        grid_w=gv(t,r'Grid Load \(W\)')
        mode=gs(t,r'Inverter Mode')
        temp=gs(t,r'Inverter Temperature')
        fan=gs(t,r'Inverter Fan')
        return {
            'solar_kwh':round(solar_w/1000,3),
            'utility_kwh':round(grid_w/1000,3),
            'battery_kwh':round(batt_pct/100*4.8,3),
            'battery_pct':batt_pct,
            'load_w':load_w,
            'voltage':voltage,
            'notes':mode,
            'temp':temp,
            'fan':fan
        }
    except Exception as e:
        return None

@app.route('/health')
def health():return 'OK'

@app.route('/api/live')
def live():
    d=scrape()
    if not d:return jsonify({'error':'scrape failed'}),500
    r.post(SU+'/rest/v1/readings',headers=H,json={k:d[k] for k in ['solar_kwh','utility_kwh','battery_kwh','battery_pct','load_w','voltage','notes']})
    return jsonify(d)

@app.route('/api/log',methods=['POST'])
def log():
    d=request.json or {}
    res=r.post(SU+'/rest/v1/readings',headers=H,json={'battery_kwh':d.get('battery_kwh',0),'solar_kwh':d.get('solar_kwh',0),'utility_kwh':d.get('utility_kwh',0),'battery_pct':d.get('battery_pct',0),'load_w':d.get('load_w',0),'voltage':d.get('voltage',48.0),'notes':d.get('notes','')})
    return jsonify({'ok':res.ok})

@app.route('/api/history')
def history():
    res=r.get(SU+'/rest/v1/readings?order=id.desc&limit=50',headers=H)
    return jsonify(res.json() if res.ok else [])

@app.route('/api/summary')
def summary():
    res=r.get(SU+'/rest/v1/readings?order=id.desc&limit=1000',headers=H)
    rows=res.json() if res.ok else []
    if not rows:return jsonify({'total_solar':0,'total_battery':0,'total_utility':0,'avg_battery_pct':0,'peak_load':0,'record_count':0})
    return jsonify({'total_solar':sum(x.get('solar_kwh',0)for x in rows),'total_battery':sum(x.get('battery_kwh',0)for x in rows),'total_utility':sum(x.get('utility_kwh',0)for x in rows),'avg_battery_pct':sum(x.get('battery_pct',0)for x in rows)/len(rows),'peak_load':max((x.get('load_w',0)for x in rows),default=0),'record_count':len(rows)})

@app.route('/dashboard')
def dashboard():
    return open('dashboard.html',encoding='utf-8').read()


@app.route('/analytics')
def analytics_page():
    return open('analytics.html',encoding='utf-8').read()

@app.route('/')
def index():return 'Sufly Solar Running!'

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))

@app.route('/api/analytics')
def analytics():
    from datetime import datetime,timedelta
    period=request.args.get('period','24h')
    if period=='today':hrs=24
    elif period=='24h':hrs=24
    elif period=='7d':hrs=168
    elif period=='1m':hrs=720
    elif period=='6m':hrs=4320
    else:hrs=24
    since=(datetime.utcnow()-timedelta(hours=hrs)).strftime('%Y-%m-%dT%H:%M:%S')
    res=r.get(SU+f'/rest/v1/readings?order=ts.asc&ts=gte.{since}&limit=2000',headers=H)
    rows=res.json() if res.ok else []
    return jsonify(rows)
