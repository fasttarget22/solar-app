from flask import Flask,request,jsonify
import os,requests as r,re
app=Flask(__name__)
SU=os.environ.get('SUPABASE_URL','')
SK=os.environ.get('SUPABASE_KEY','')
H={'apikey':SK,'Authorization':'Bearer '+SK,'Content-Type':'application/json','Prefer':'return=representation'}
SS_KEY='6637103e47ce38c4f5b4f2fad69474642b67d8bc-0'
SS_URL='https://smartsolar.net.pk/api/inverter/status.php'

def gn(val):
    m=re.findall(r'[\d.]+',str(val))
    return float(m[0]) if m else 0.0

def scrape():
    try:
        res=r.get(SS_URL,headers={'X-API-KEY':SS_KEY},timeout=10)
        if not res.ok:return None
        d=res.json().get('data',{})
        solar_w=gn(d.get('PV_Watt',0))
        load_w=gn(d.get('Output_Load_W',0))
        voltage=gn(d.get('Batt_Volt',48))
        batt_pct=gn(d.get('Batt_Status',0))
        grid_w=gn(d.get('AC_Watt',0))
        mode=d.get('In_Mode','')
        temp=d.get('Inv_Temp','').replace('temp=d.get('Inv_Temp','')#8451;','°C')
        fan=d.get('Inv_Fan','')
        batt_charge_w=gn(d.get('Batt_Charge_W',0))
        batt_discharge_w=gn(d.get('Batt_Discharge_W',0))
        return {
            'solar_kwh':round(solar_w/1000,3),
            'utility_kwh':round(grid_w/1000,3),
            'battery_kwh':round(batt_pct/100*4.8,3),
            'battery_pct':batt_pct,
            'load_w':load_w,
            'voltage':voltage,
            'notes':mode,
            'temp':temp,
            'fan':fan,
            'solar_w':solar_w,
            'grid_w':grid_w,
            'batt_charge_w':batt_charge_w,
            'batt_discharge_w':batt_discharge_w
        }
    except Exception as e:
        return None
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

@app.route('/api/savetotals', methods=['POST'])
def savetotals():
    d = request.json or {}
    date = d.get('date','')
    saved = d.get('saved_pkr', 0)
    consumed = d.get('consumed_pkr', 0)
    existing = r.get(SU+'/rest/v1/totals?date=eq.'+date, headers=H)
    if existing.ok and len(existing.json()) > 0:
        r.patch(SU+'/rest/v1/totals?date=eq.'+date, headers=H, json={'saved_pkr':saved,'consumed_pkr':consumed})
    else:
        r.post(SU+'/rest/v1/totals', headers=H, json={'date':date,'saved_pkr':saved,'consumed_pkr':consumed})
    return jsonify({'ok':True})

@app.route('/api/gettotals')
def gettotals():
    date = request.args.get('date','')
    res = r.get(SU+'/rest/v1/totals?date=eq.'+date, headers=H)
    rows = res.json() if res.ok else []
    if rows:
        return jsonify(rows[0])
    return jsonify({'saved_pkr':0,'consumed_pkr':0})

@app.route('/api/usage')
def usage():
    res=r.get('https://smartsolar.net.pk/api/inverter/usage.php?period=today',headers={'X-API-KEY':'6637103e47ce38c4f5b4f2fad69474642b67d8bc-0'},timeout=10)
    return jsonify(res.json().get('data',{}) if res.ok else {})

@app.route('/api/faults')
def faults():
    res=r.get('https://smartsolar.net.pk/api/inverter/faults.php?period=this_month&hide_grid=true',headers={'X-API-KEY':'6637103e47ce38c4f5b4f2fad69474642b67d8bc-0'},timeout=10)
    return jsonify(res.json().get('data',{}) if res.ok else {})

@app.route('/api/chart')
def chart():
    res=r.get('https://smartsolar.net.pk/api/inverter/chart.php?duration=60',headers={'X-API-KEY':'6637103e47ce38c4f5b4f2fad69474642b67d8bc-0'},timeout=10)
    return jsonify(res.json().get('data',[]) if res.ok else [])
