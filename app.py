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

# Direct endpoint to pull the raw text stream safely without browser scripts
DATA_URL = "https://smartsolar.net.pk/index-data.php?dev_id=D8BC38AD6637&dev_dm=0"

def scrape_smartsolar():
    try:
        res = r.get(DATA_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if not res.ok:
            return None
        html = res.text
        
        # Strip code formatting down to single-line spaces for seamless text-matching
        clean = re.sub(r'\s+', ' ', html)

        # 1. Parse PV Watt (Solar Power)
        solar_w = 0.0
        sol_match = re.search(r'PV Watt.*?class="data_value[^"]*".*?>\s*(\d+)\s*W', clean, re.IGNORECASE)
        if sol_match:
            solar_w = float(sol_match.group(1))

        # 2. Parse Output Load (W) (Home Load)
        load_w = 0.0
        load_match = re.search(r'Output Load \(W\).*?class="data_value[^"]*".*?>\s*(\d+)\s*W', clean, re.IGNORECASE)
        if load_match:
            load_w = float(load_match.group(1))

        # 3. Parse Battery Volt
        voltage = 48.0
        volt_match = re.search(r'Battery Volt.*?class="data_value[^"]*".*?>\s*([\d.]+)\s*V', clean, re.IGNORECASE)
        if volt_match:
            voltage = float(volt_match.group(1))

        # 4. Parse Battery Capacity Percentage (%)
        batt_pct = 100.0
        # Finds the first percentage value inside a data_value container directly following the Battery Volt block
        pct_match = re.search(r'Battery Volt.*?class="data_value[^"]*".*?>.*?class="data_value[^"]*".*?>\s*(\d+)\s*%', clean, re.IGNORECASE)
        if pct_match:
            batt_pct = float(pct_match.group(1))

        # 5. Parse Temperatures and Fan Speed
        temp_matches = re.findall(r"(\d+)\s*°C", clean)
        fan_match = re.search(r"(\d+)\s*%.*?Fan", clean, re.IGNORECASE) or re.search(r"Fan.*?(\d+)\s*%", clean, re.IGNORECASE)
            
        t_val = temp_matches[0] if temp_matches else "36"
        f_val = fan_match.group(1) if fan_match else "30"
        notes_json = f'{{"temp":"{t_val}","fan":"{f_val}"}}'

        # Convert continuous raw watts to simulated data-slice logs
        solar_kwh = solar_w / 1000.0 if solar_w > 0 else 0.0
        utility_kwh = 0.0
        battery_kwh = 0.0

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
        print("Data extraction process hit a snag:", e)
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
