from flask import Flask, request, jsonify
import os
import requests as r
import re

app = Flask(__name__)
SU = os.environ.get('SUPABASE_URL', '')
SK = os.environ.get('SUPABASE_KEY', '')
H = {
    'apikey': SK,
    'Authorization': 'Bearer ' + SK,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

SMARTSOLAR_URL = "https://smartsolar.net.pk/D8BC38AD6637"

def scrape_smartsolar():
    try:
        res = r.get(SMARTSOLAR_URL, timeout=10)
        if not res.ok:
            return None
        html = res.text
        
        # 1. Parse Solar Power (Watts)
        solar_w = 0
        sol_match = re.search(r"(\d+)\s*W\s*<\/div>\s*<div[^>]*class=\"[^\"]*label[^\"]*\"[^>]*>\s*Solar\s*Power", html, re.IGNORECASE)
        if sol_match:
            solar_w = float(sol_match.group(1))
        else:
            sol_match2 = re.search(r"Solar\s*Power.*?(\d+)\s*W", html, re.DOTALL | re.IGNORECASE)
            if sol_match2: solar_w = float(sol_match2.group(1))

        # 2. Parse Home Load (Watts)
        load_w = 0
        load_match = re.search(r"(\d+)\s*W\s*<\/div>\s*<div[^>]*class=\"[^\"]*label[^\"]*\"[^>]*>\s*Load\s*Power", html, re.IGNORECASE)
        if load_match:
            load_w = float(load_match.group(1))
        else:
            load_match2 = re.search(r"Load\s*Power.*?(\d+)\s*W", html, re.DOTALL | re.IGNORECASE)
            if load_match2: load_w = float(load_match2.group(1))

        # 3. Parse Battery Percentage (%)
        batt_pct = 100.0
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*<\/div>\s*<div[^>]*class=\"[^\"]*label[^\"]*\"[^>]*>\s*Battery\s*Capacity", html, re.IGNORECASE)
        if pct_match:
            batt_pct = float(pct_match.group(1))
        else:
            pct_match2 = re.search(r"Battery\s*Capacity.*?(\d+(?:\.\d+)?)\s*%", html, re.DOTALL | re.IGNORECASE)
            if pct_match2: batt_pct = float(pct_match2.group(1))

        # 4. Parse Voltage (V)
        voltage = 48.0
        volt_match = re.search(r"(\d+(?:\.\d+)?)\s*V\s*<\/div>\s*<div[^>]*class=\"[^\"]*label[^\"]*\"[^>]*>\s*Battery\s*Voltage", html, re.IGNORECASE)
        if volt_match:
            voltage = float(volt_match.group(1))
        else:
            volt_match2 = re.search(r"Battery\s*Voltage.*?(\d+(?:\.\d+)?)\s*V", html, re.DOTALL | re.IGNORECASE)
            if volt_match2: voltage = float(volt_match2.group(1))

        # 5. Parse Temperatures and Fan (stored in notes JSON string)
        temp_match = re.findall(r"(\d+)\s*°C", html)
        fan_match = re.search(r"(\d+)\s*%\s*<\/div>\s*<div[^>]*class=\"[^\"]*label[^\"]*\"[^>]*>\s*Fan\s*Speed", html, re.IGNORECASE)
        if not fan_match:
            fan_match = re.search(r"Fan\s*Speed.*?(\d+)\s*%", html, re.DOTALL | re.IGNORECASE)
            
        t_val = temp_match[0] if temp_match else "36"
        f_val = fan_match.group(1) if fan_match else "30"
        notes_json = f'{{"temp":"{t_val}","fan":"{f_val}"}}'

        # Convert Watts to simulated generation metrics per log slice (roughly 30 sec updates)
        solar_kwh = (solar_w * 30) / 3600000
        utility_kwh = 0.0  # Assume 0 or update if mixed mode parsed
        battery_kwh = (load_w * 30) / 3600000 if solar_w == 0 else 0.0

        return {
            'battery_kwh': battery_kwh,
            'solar_kwh': solar_kwh,
            'utility_kwh': utility_kwh,
            'battery_pct': batt_pct,
            'load_w': load_w,
            'voltage': voltage,
            'notes': notes_json
        }
    except Exception as e:
        print("Scraper Error:", e)
        return None

@app.route('/health')
def health():
    return 'OK'

@app.route('/api/log', methods=['POST'])
def log():
    d = request.json or {}
    res = r.post(SU+'/rest/v1/readings', headers=H, json={
        'battery_kwh': d.get('battery_kwh', 0),
        'solar_kwh': d.get('solar_kwh', 0),
        'utility_kwh': d.get('utility_kwh', 0),
        'battery_pct': d.get('battery_pct', 0),
        'load_w': d.get('load_w', 0),
        'voltage': d.get('voltage', 48.0),
        'notes': d.get('notes', '')
    })
    return jsonify({'ok': res.ok})

@app.route('/api/history')
def history():
    # Force a live scrape on every dashboard reading request to update data stream
    d = scrape_smartsolar()
    if d:
        r.post(SU+'/rest/v1/readings', headers=H, json=d)
    res = r.get(SU+'/rest/v1/readings?order=id.desc&limit=50', headers=H)
    return jsonify(res.json() if res.ok else [])

@app.route('/api/summary')
def summary():
    res = r.get(SU+'/rest/v1/readings?order=id.desc&limit=1000', headers=H)
    rows = res.json() if res.ok else []
    if not rows:
        return jsonify({'total_solar':0,'total_battery':0,'total_utility':0,'avg_battery_pct':0,'peak_load':0,'record_count':0,'today':{'s':0,'b':0,'u':0}})
    return jsonify({
        'total_solar': sum(x.get('solar_kwh', 0) for x in rows),
        'total_battery': sum(x.get('battery_kwh', 0) for x in rows),
        'total_utility': sum(x.get('utility_kwh', 0) for x in rows),
        'avg_battery_pct': sum(x.get('battery_pct', 0) for x in rows)/len(rows),
        'peak_load': max((x.get('load_w', 0) for x in rows), default=0),
        'record_count': len(rows),
        'today': {'s': 0, 'b': 0, 'u': 0}
    })

@app.route('/dashboard')
def dashboard():
    return open('dashboard.html').read()

@app.route('/')
def index():
    return 'Solar Monitor API Running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
