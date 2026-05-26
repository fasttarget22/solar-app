from flask import Flask, request, jsonify
import os
import requests as r
import re

app = Flask(__name__)
SU = os.environ.get('SUPABASE_URL', '')
SK = os.environ.get('SUPABASE_KEY', '')
H = {'apikey': SK, 'Authorization': 'Bearer ' + SK, 'Content-Type': 'application/json'}

DATA_URL = "https://smartsolar.net.pk/index-data.php?dev_id=D8BC38AD6637&dev_dm=0"

def scrape_smartsolar():
    try:
        res = r.get(DATA_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if not res.ok: return None
        clean = re.sub(r'\s+', ' ', res.text)
        
        solar_w = 0.0
        sol_match = re.search(r'PV Watt.*?data_value[^>]*>\s*(\d+)\s*W', clean, re.IGNORECASE)
        if sol_match: solar_w = float(sol_match.group(1))

        load_w = 0.0
        load_match = re.search(r'Output Load \(W\).*?data_value[^>]*>\s*(\d+)\s*W', clean, re.IGNORECASE)
        if load_match: load_w = float(load_match.group(1))

        voltage = 48.0
        volt_match = re.search(r'Battery Volt.*?data_value[^>]*>\s*([\d.]+)\s*V', clean, re.IGNORECASE)
        if volt_match: voltage = float(volt_match.group(1))

        batt_pct = 100.0
        pct_match = re.search(r'Battery Volt.*?data_value[^>]*>.*?data_value[^>]*>\s*(\d+)\s*%', clean, re.IGNORECASE)
        if pct_match: batt_pct = float(pct_match.group(1))

        return {'battery_kwh': 0.0, 'solar_kwh': solar_w/1000.0, 'utility_kwh': 0.0, 'battery_pct': batt_pct, 'load_w': load_w, 'voltage': voltage, 'notes': ''}
    except:
        return None

@app.route('/api/history')
def history():
    d = scrape_smartsolar()
    if d: r.post(SU+'/rest/v1/readings', headers=H, json=d)
    res = r.get(SU+'/rest/v1/readings?order=id.desc&limit=10', headers=H)
    return jsonify(res.json() if res.ok else [])

@app.route('/dashboard')
def dashboard():
    # یہاں ہم نے فائل کا نام تبدیل کر دیا تاکہ پرانا کیشے ختم ہو جائے
    return open('panel.html', encoding='utf-8').read()

@app.route('/')
def index():
    return 'Running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
