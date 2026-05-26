<script>
const API = '';
const BATT_CAP = 4.8;
const SAFE_MIN = 20;
let popupShown = false;
let isUrdu = false;

// Particles
const pw = document.getElementById('particles');
for(let i=0;i<15;i++){
  const p = document.createElement('div');
  p.className = 'particle';
  p.style.cssText = `left:${Math.random()*100}%;width:${Math.random()*3+1}px;height:${Math.random()*3+1}px;animation-duration:${Math.random()*10+8}s;animation-delay:${Math.random()*12}s`;
  pw.appendChild(p);
}



let voiceOn=false;
function toggleVoice(){
  voiceOn=!voiceOn;
  const btn=document.getElementById('voiceBtn');
  if(voiceOn){btn.style.color='var(--green)';btn.style.borderColor='var(--green)';btn.textContent='\ud83d\udd0a Voice ON';speakUrdu('وائس الرٹ آن ہے');}
  else{btn.style.color='var(--muted)';btn.style.borderColor='var(--border)';btn.textContent='\ud83d\udd07 Voice';}
}

function shareFamily(){
  const url='https://solar-app-yrm6.onrender.com/dashboard';
  const solar=document.getElementById('sTsolar').textContent;
  const batt=document.getElementById('cBatt').textContent;
  const load=document.getElementById('cLoad').textContent;
  const saved=document.getElementById('sSaved').textContent;
  const msg='\u2600\ufe0f *Sufly Solar - Abbottabad Prime*\n\n\ud83d\udd0b Battery: '+batt+'\n\ud83c\udfe0 Load: '+load+'\n\u2600\ufe0f Total Solar: '+solar+' kWh\n\ud83d\udcb0 Saved: '+saved+'\n\n\ud83d\udcf1 Live: '+url;
  window.open('https://wa.me/?text='+encodeURIComponent(msg));
}


let prevLoad=0;
function analyzeLoad(load,solar,grid){
  const spike=load-prevLoad;
  const al=document.getElementById('alHigh');
  if(spike>300&&prevLoad>0){
    const el=document.getElementById('alHigh');
    el.style.display='block';
    el.querySelector('.al-ur').textContent='\u06a9\u0686\u06be \u0646\u06cc\u0627 \u0686\u0644\u0627 \u062f\u06cc\u0627 \u06af\u06cc\u0627! +'+spike.toFixed(0)+'W \u0627\u0636\u0627\u0641\u06c1';
    el.querySelector('.al-sub').textContent='LOAD SPIKE DETECTED: +'+spike.toFixed(0)+'W increase!';
    setTimeout(()=>{if(load<=1200)el.style.display='none';},10000);
  }
  prevLoad=load;
}


let lastVoiceAlert='';
function speakUrdu(text){
  if(!window.speechSynthesis)return;
  if(lastVoiceAlert===text)return;
  lastVoiceAlert=text;
  const u=new SpeechSynthesisUtterance(text);
  u.lang='ur-PK';u.rate=0.9;u.pitch=1;u.volume=1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
  setTimeout(()=>{lastVoiceAlert='';},60000);
}
function checkVoiceAlerts(solar,grid,load,batt){
  const battOnly=solar==0&&grid==0;
  if(battOnly&&batt<30){
    speakUrdu('خبردار! بیٹری تیس فیصد سے کم ہے۔ فوری واپڈا لگائیں۔');
  } else if(battOnly&&batt<50){
    speakUrdu('بیٹری پچاس فیصد سے کم ہے۔ بوجھ کم کریں۔');
  } else if(load>1200){
    speakUrdu('خبردار! گھر کا بوجھ بہت زیادہ ہے۔ کچھ آلات بند کریں۔');
  } else if(solar>0&&grid==0&&batt==100){
    speakUrdu('بہترین! سولر چل رہا ہے اور بیٹری مکمل چارج ہے۔');
  }
}


async function loadForecast(){
  try{
    const res=await fetch('https://api.open-meteo.com/v1/forecast?latitude=34.1688&longitude=73.2215&daily=weather_code,temperature_2m_max,cloud_cover_mean,sunshine_duration&timezone=Asia/Karachi&forecast_days=2');
    const d=await res.json();
    const icons={0:'☀️',1:'🌤️',2:'⛅',3:'☁️',45:'🌫️',51:'🌦️',61:'🌧️',71:'❄️',80:'🌦️',95:'⛈️'};
    const descs={0:'Clear Sky',1:'Mainly Clear',2:'Partly Cloudy',3:'Overcast',45:'Foggy',51:'Drizzle',61:'Rain',71:'Snow',80:'Showers',95:'Thunderstorm'};
    const wc=d.daily.weather_code[1];
    const temp=d.daily.temperature_2m_max[1];
    const cloud=d.daily.cloud_cover_mean[1];
    const sunshine=d.daily.sunshine_duration[1];
    const solarExp=cloud<20?'HIGH':cloud<50?'MEDIUM':cloud<70?'LOW':'POOR';
    const expColor=cloud<20?'var(--green)':cloud<50?'var(--amber)':cloud<70?'#ff6600':'var(--red)';
    document.getElementById('fcIcon').textContent=icons[wc]||'🌤️';
    document.getElementById('fcDesc').textContent=descs[wc]||'Clear';
    document.getElementById('fcTemp').textContent=temp+'°C';
    document.getElementById('fcCloud').textContent=cloud+'%';
    document.getElementById('fcExp').textContent=solarExp;
    document.getElementById('fcExp').style.color=expColor;
    const sunHrs=(sunshine/3600).toFixed(1);
    const msg=cloud<30?'✅ Excellent solar day tomorrow! Expected '+sunHrs+' hrs sunshine':cloud<60?'⚡ Good solar expected. '+sunHrs+' hrs sunshine':'⚠️ Cloudy tomorrow. Charge battery today!';
    const msgEl=document.getElementById('fcMsg');
    msgEl.textContent=msg;
    msgEl.style.background=cloud<30?'rgba(0,230,118,0.1)':cloud<60?'rgba(255,171,0,0.1)':'rgba(255,82,82,0.1)';
    msgEl.style.color=cloud<30?'var(--green)':cloud<60?'var(--amber)':'var(--red)';
  }catch(e){console.error('Forecast:',e);}
}


function updateApplianceTimes(){
  const now=new Date();
  const hr=now.getHours();
  const appliances=[
    {name:'&#129529; Washing Machine',best:'10:00-13:00',bestHr:[10,13],icon:'&#129529;'},
    {name:'&#9749; Iron',best:'11:00-14:00',bestHr:[11,14],icon:'&#9749;'},
    {name:'&#10052; AC',best:'12:00-15:00',bestHr:[12,15],icon:'&#10052;'},
    {name:'&#127861; Oven',best:'11:00-13:00',bestHr:[11,13],icon:'&#127861;'},
    {name:'&#128187; Computer',best:'09:00-16:00',bestHr:[9,16],icon:'&#128187;'},
    {name:'&#128268; Chargers',best:'09:00-17:00',bestHr:[9,17],icon:'&#128268;'}
  ];
  const list=document.getElementById('appList');
  list.innerHTML=appliances.map(a=>{
    const active=hr>=a.bestHr[0]&&hr<a.bestHr[1];
    const bg=active?'rgba(0,230,118,0.15)':'rgba(255,255,255,0.04)';
    const border=active?'1px solid var(--green)':'1px solid rgba(255,255,255,0.08)';
    const status=active?'&#9989; NOW':'&#128336; '+a.best;
    const color=active?'var(--green)':'var(--muted)';
    return '<div style="background:'+bg+';border:'+border+';border-radius:10px;padding:8px;text-align:center"><div style="font-size:16px">'+a.icon+'</div><div style="font-size:9px;color:var(--muted);letter-spacing:1px">'+a.name.replace(/&#\d+;/g,'')+'</div><div style="font-size:10px;font-weight:700;color:'+color+'">'+status+'</div></div>';
  }).join('');
}


function updatePowerFlow(solar,grid,load,batt){
  const solarW=(solar*1000).toFixed(0);
  const gridW=(grid*1000).toFixed(0);
  const battOnly=solar==0&&grid==0;

  document.getElementById('pfSolarVal').textContent=solarW+'W';
  document.getElementById('pfBattVal').textContent=batt.toFixed(0)+'%';
  document.getElementById('pfGridVal').textContent=gridW+'W';
  document.getElementById('pfHomeLoad').textContent=load.toFixed(0)+'W';

  // Solar line
  const sl=document.getElementById('pfLineSolar');
  const sd=document.getElementById('pfDotSolar');
  if(solar>0){sl.classList.remove('pf-line-off');sd.setAttribute('opacity','0.8');}
  else{sl.classList.add('pf-line-off');sd.setAttribute('opacity','0');}

  const solarExcess=Math.round(solar*1000)>load&&batt<100;
  const wapdaChargingBatt=grid>0&&batt<100&&solar==0;

  function setLine(lid,did,on){
    const l=document.getElementById(lid);const d=document.getElementById(did);
    if(!l||!d)return;
    if(on){l.classList.remove('pf-line-off');d.setAttribute('opacity','0.9');}
    else{l.classList.add('pf-line-off');d.setAttribute('opacity','0');}
  }

  setLine('pfLineBatt','pfDotBatt',battOnly);
  setLine('pfLineGrid','pfDotGrid',grid>0);
  setLine('pfLineSolarBatt','pfDotSolarBatt',solarExcess);
  setLine('pfLineGridBatt','pfDotGridBatt',wapdaChargingBatt);

  document.getElementById('pfBattVal').textContent=batt.toFixed(0)+'%'+(solarExcess||wapdaChargingBatt?' ↑':battOnly?' ↓':'');

  const homeEl=document.getElementById('pfHomeIcon');
  if(solar>0&&grid==0)homeEl.style.filter='drop-shadow(0 0 15px rgba(0,230,118,0.9))';
  else if(grid>0&&solar==0)homeEl.style.filter='drop-shadow(0 0 15px rgba(64,196,255,0.9))';
  else if(grid>0&&solar>0)homeEl.style.filter='drop-shadow(0 0 15px rgba(255,171,0,0.9))';
  else homeEl.style.filter='drop-shadow(0 0 15px rgba(255,82,82,0.9))';

  const battEl=document.getElementById('pfBattIcon');
  if(solarExcess||wapdaChargingBatt)battEl.style.filter='drop-shadow(0 0 12px rgba(0,230,118,0.9))';
  else if(battOnly)battEl.style.filter='drop-shadow(0 0 12px rgba(255,82,82,0.9))';
  else battEl.style.filter='drop-shadow(0 0 6px rgba(255,171,0,0.4))';
}


let PKR_RATE=parseFloat(localStorage.getItem('pkr')||22);
let BATT_CAP=parseFloat(localStorage.getItem('batt')||4.8);
let SAFE_MIN=parseFloat(localStorage.getItem('safe')||20);
let REFRESH_INT=parseInt(localStorage.getItem('refresh')||30);
let refreshTimer=null;

function toggleSettings(){
  const p=document.getElementById('settingsPanel');
  const show=p.style.display!=='flex';
  p.style.display=show?'flex':'none';
  if(show){
    document.getElementById('setPKR').value=PKR_RATE;
    document.getElementById('setBattCap').value=BATT_CAP;
    document.getElementById('setSafeMin').value=SAFE_MIN;
    document.getElementById('setRefresh').value=REFRESH_INT;
  }
}

function saveSettings(){
  PKR_RATE=parseFloat(document.getElementById('setPKR').value)||22;
  BATT_CAP=parseFloat(document.getElementById('setBattCap').value)||4.8;
  SAFE_MIN=parseFloat(document.getElementById('setSafeMin').value)||20;
  REFRESH_INT=parseInt(document.getElementById('setRefresh').value)||30;
  localStorage.setItem('pkr',PKR_RATE);
  localStorage.setItem('batt',BATT_CAP);
  localStorage.setItem('safe',SAFE_MIN);
  localStorage.setItem('refresh',REFRESH_INT);
  if(refreshTimer)clearInterval(refreshTimer);
  refreshTimer=setInterval(loadAll,REFRESH_INT*1000);
  toggleSettings();
  loadAll();
  alert('Settings saved!');
}

function toggleLang(){
  isUrdu = !isUrdu;
  document.body.classList.toggle('urdu-mode', isUrdu);
  document.getElementById('langBtn').textContent = isUrdu ? 'English' : 'اردو';
  document.querySelectorAll('.en').forEach(e => e.style.display = isUrdu ? 'none' : '');
  document.querySelectorAll('.ur').forEach(e => e.style.display = isUrdu ? 'block' : 'none');
}

function calcBattHours(bp, lw){
  if(lw <= 0) return {h:99, lvl:'safe'};
  const up = Math.max(0, bp - SAFE_MIN);
  const uk = (up/100) * BATT_CAP;
  const h = uk / (lw/1000);
  let lvl = 'safe';
  if(h < 1) lvl = 'critical';
  else if(h < 3) lvl = 'danger';
  else if(h < 8) lvl = 'caution';
  // Pakistan finish time PKT (UTC+5)
  const now = new Date();
  const pkt = new Date(now.getTime() + (5*60*60*1000) - (now.getTimezoneOffset()*60*1000));
  const finishMs = pkt.getTime() + (h * 3600 * 1000);
  const finish = new Date(finishMs);
  const fh = finish.getUTCHours().toString().padStart(2,'0');
  const fm = finish.getUTCMinutes().toString().padStart(2,'0');
  const finishTime = fh+':'+fm+' PKT';
  return {h, lvl, uk, up, finishTime};
}

function updateBattHours(bp, lw){
  const {h, lvl, uk, up, finishTime} = calcBattHours(bp, lw);
  const card = document.getElementById('bhCard');
  card.className = 'bh-card bh-' + lvl;
  const valEl = document.getElementById('bhVal');
  const iconEl = document.getElementById('bhIcon');
  const sugUr = document.getElementById('bhSugUr');
  const sugEn = document.getElementById('bhSugEn');
  const bar = document.getElementById('bhBar');
  const note = document.getElementById('bhNote');
  const unitEl = document.getElementById('bhUnit');
  if(finishTime && h<99) unitEl.textContent = h.toFixed(1)+' hrs — ends '+finishTime;
  else if(h>=99) unitEl.textContent = 'Solar/Grid active — battery protected';
  note.textContent = `محفوظ حد: ${SAFE_MIN}% لیتھیم — قابل استعمال: ${up.toFixed(0)}% = ${uk.toFixed(2)} kWh`;
  bar.style.width = Math.min(100, h>=99 ? 100 : (h/12)*100) + '%';
  if(lvl === 'safe'){
    valEl.style.color = 'var(--green)';
    valEl.textContent = h>=99 ? '∞' : h.toFixed(1);
    iconEl.textContent = '🟢';
    sugUr.textContent = h>=99 ? 'بیٹری بھری ہے — کوئی فکر نہیں ☀️' : 'بیٹری محفوظ ہے — بے فکر رہیں ✅';
    sugEn.textContent = h>=99 ? 'Battery full — enjoy solar' : 'Battery safe — no action needed';
  } else if(lvl === 'caution'){
    valEl.style.color = 'var(--amber)';
    valEl.textContent = h.toFixed(1);
    iconEl.textContent = '🟡';
    sugUr.textContent = `تقریباً ${h.toFixed(1)} گھنٹے باقی — غیر ضروری بوجھ بند کریں ⚡`;
    sugEn.textContent = `~${h.toFixed(1)} hrs left — reduce unnecessary load`;
  } else if(lvl === 'danger'){
    valEl.style.color = '#ff6600';
    valEl.textContent = h.toFixed(1);
    iconEl.textContent = '🟠';
    sugUr.textContent = `صرف ${h.toFixed(1)} گھنٹے باقی! واپڈا کے لیے تیار رہیں ⚠️`;
    sugEn.textContent = `Only ${h.toFixed(1)} hrs! Prepare to switch to grid`;
    if(!popupShown){
      document.getElementById('popTitle').textContent = `بیٹری ${h.toFixed(1)} گھنٹے میں ختم!`;
      document.getElementById('popHrs').textContent = h.toFixed(1) + ' HRS';
      document.getElementById('popMsg').textContent = 'ابھی بوجھ کم کریں یا واپڈا تیار رکھیں';
      document.getElementById('popup').classList.add('show');
      popupShown = true;
    }
  } else {
    const mins = Math.round(h*60);
    valEl.style.color = 'var(--red)';
    valEl.textContent = mins + 'm';
    iconEl.textContent = '🔴';
    sugUr.textContent = `فوری واپڈا لگائیں! صرف ${mins} منٹ باقی 🚨`;
    sugEn.textContent = `CRITICAL: Only ${mins} minutes left! Switch NOW`;
    document.getElementById('popTitle').textContent = '🚨 فوری اقدام کریں!';
    document.getElementById('popHrs').textContent = mins + ' MIN';
    document.getElementById('popMsg').textContent = 'بیٹری ختم ہونے والی ہے! ابھی واپڈا لگائیں';
    document.getElementById('popup').classList.add('show');
  }
}

function setSrc(solar, grid){
  const badge = document.getElementById('srcBadge');
  const val = document.getElementById('srcVal');
  const icon = document.getElementById('srcIcon');
  const battOnly = solar==0 && grid==0;
  if(battOnly){
    badge.className='src-badge b-batt'; badge.textContent='BATTERY ONLY';
    val.style.color='var(--red)'; val.textContent='صرف بیٹری 🔋'; icon.textContent='🔋';
    document.getElementById('mainBody').classList.add('bmode');
  } else if(solar>0 && grid==0){
    badge.className='src-badge b-solar'; badge.textContent='SOLAR ONLY';
    val.style.color='var(--green)'; val.textContent='Pure solar energy ☀'; icon.textContent='☀️';
    document.getElementById('mainBody').classList.remove('bmode');
  } else if(solar>0 && grid>0){
    badge.className='src-badge b-mixed'; badge.textContent='SOLAR+WAPDA';
    val.style.color='var(--amber)'; val.textContent='Solar & Wapda mixed ⚡'; icon.textContent='⚡';
    document.getElementById('mainBody').classList.remove('bmode');
  } else {
    badge.className='src-badge b-grid'; badge.textContent='WAPDA ONLY';
    val.style.color='var(--blue)'; val.textContent='Running on grid 🔌'; icon.textContent='🔌';
    document.getElementById('mainBody').classList.remove('bmode');
  }
}

function setAlerts(solar, grid, load){
  const battOnly = solar==0 && grid==0;
  document.getElementById('alBatt').style.display = battOnly ? 'block' : 'none';
  document.getElementById('alHigh').style.display = (load>1200 && !battOnly) ? 'block' : 'none';
  document.getElementById('alMed').style.display = (load>300 && load<=1200 && !battOnly) ? 'block' : 'none';
}


async function loadWeather(){
  try{
    const res=await fetch('https://wttr.in/Abbottabad?format=j1');
    const d=await res.json();
    const cc=d.current_condition[0];
    const temp=cc.temp_C;
    const hum=cc.humidity;
    const wind=cc.windspeedKmph;
    const cloud=cc.cloudcover;
    const desc=cc.weatherDesc[0].value;
    const wcode=parseInt(cc.weatherCode);
    const icons={113:'☀️',116:'⛅',119:'☁️',122:'☁️',143:'🌫️',176:'🌦️',179:'❄️',182:'🌧️',185:'🌧️',200:'⛈️',227:'❄️',230:'❄️',248:'🌫️',260:'🌫️',263:'🌦️',266:'🌦️',281:'🌧️',284:'🌧️',293:'🌧️',296:'🌧️',299:'🌧️',302:'🌧️',305:'🌧️',308:'🌧️',311:'🌧️',314:'🌧️',317:'🌨️',320:'🌨️',323:'❄️',326:'❄️',329:'❄️',332:'❄️',335:'❄️',338:'❄️',350:'🌧️',353:'🌦️',356:'🌧️',359:'🌧️',362:'🌨️',365:'🌨️',368:'🌨️',371:'❄️',374:'🌨️',377:'🌨️',386:'⛈️',389:'⛈️',392:'⛈️',395:'⛈️'};
    const icon=icons[wcode]||'🌤️';
    document.getElementById('wtBar').style.display='block';
    document.getElementById('wtIcon').textContent=icon;
    document.getElementById('wtDesc').textContent=desc;
    document.getElementById('wtTemp').textContent=temp+'°C';
    document.getElementById('wtHum').textContent=hum+'%';
    document.getElementById('wtCloud').textContent=cloud+'%';
    document.getElementById('wtWind').textContent=wind+' km/h';
    const ic=document.getElementById('wtIcon');
    if(wcode===113){ic.style.filter='drop-shadow(0 0 10px rgba(255,200,0,0.9))';}
    else{ic.style.filter='drop-shadow(0 0 6px rgba(100,150,255,0.5))';}
    if(parseInt(cloud)>70){document.getElementById('wtWarn').style.display='block';document.getElementById('wtGood').style.display='none';}
    else if(parseInt(cloud)<30&&wcode===113){document.getElementById('wtGood').style.display='block';document.getElementById('wtWarn').style.display='none';}
    else{document.getElementById('wtWarn').style.display='none';document.getElementById('wtGood').style.display='none';}
  }catch(e){console.error('Weather:',e);}
}


let pkrPerSec=0;let pkrTotal=0;let pkrInterval=null;
function updateMeter(solar,grid,load){
  const active=solar>0||grid>0;
  const solarW=solar*1000;
  const pkrPerHour=solarW/1000*22;
  pkrPerSec=pkrPerHour/3600;
  const el=document.getElementById('pkrVal');
  const sub=document.getElementById('pkrSub');
  const rate=document.getElementById('pkrRate');
  if(solar>0&&grid==0){
    el.className='pkr-val';
    rate.textContent='Solar: '+solarW.toFixed(0)+'W x PKR 22/kWh = PKR '+pkrPerHour.toFixed(2)+'/hr';
    sub.textContent='pure solar saving every second!';
    if(!pkrInterval){pkrInterval=setInterval(()=>{pkrTotal+=pkrPerSec;document.getElementById('pkrVal').textContent='PKR '+pkrTotal.toFixed(2);},1000);}
  } else if(solar>0&&grid>0){
    el.className='pkr-val';
    rate.textContent='Solar saving PKR '+pkrPerHour.toFixed(2)+'/hr';
    sub.textContent='solar + wapda mixed mode';
    if(!pkrInterval){pkrInterval=setInterval(()=>{pkrTotal+=pkrPerSec;document.getElementById('pkrVal').textContent='PKR '+pkrTotal.toFixed(2);},1000);}
  } else {
    if(pkrInterval){clearInterval(pkrInterval);pkrInterval=null;}
    el.className='pkr-val pkr-off';
    el.textContent='PKR 0.00';
    sub.textContent='no solar active right now';
    rate.textContent='waiting for solar...';
  }
}

async function loadAll(){
  try{
    const [sr, hr] = await Promise.all([
      fetch(API + '/api/summary').then(r=>r.json()),
      fetch(API + '/api/live').then(r=>r.json()).then(d=>[d])
    ]);
    document.getElementById('sTotalSolar').textContent = sr.total_solar.toFixed(2);
    document.getElementById('sTotalWapda').textContent = sr.total_utility.toFixed(2);
    document.getElementById('sPeak').textContent = sr.peak_load.toFixed(0) + 'W';
    document.getElementById('sCount').textContent = sr.record_count;
    document.getElementById('sSaved').textContent = 'PKR ' + Math.round(sr.total_solar*22).toLocaleString();
    const rt = sr.total_solar>0 ? Math.min(100, Math.round(sr.total_solar/(sr.total_solar+sr.total_utility)*100)) : 0;
    document.getElementById('sRatio').textContent = rt + '%';
    document.getElementById('ratioFill').style.width = rt + '%';
    if(hr.length){
      const l = hr[0];
      document.getElementById('cSolar').textContent = (l.solar_kwh||0).toFixed(3);
      const bp = l.battery_pct||0;
      document.getElementById('cBatt').textContent = bp.toFixed(1) + '%';
      document.getElementById('battProg').style.width = bp + '%';
      document.getElementById('cVolt').textContent = (l.voltage||48).toFixed(1) + 'V';
      const lw = l.load_w||0;
      document.getElementById('cLoad').textContent = lw.toFixed(0) + 'W';
      document.getElementById('cGrid').textContent = (l.utility_kwh||0).toFixed(3);
      const bk = (bp/100) * BATT_CAP;
      document.getElementById('cBkwh').textContent = bk.toFixed(2);
      document.getElementById('bkwhProg').style.width = (bk/BATT_CAP*100) + '%';
      setSrc(l.solar_kwh||0, l.utility_kwh||0);updateMeter(l.solar_kwh||0,l.utility_kwh||0,lw);analyzeLoad(lw,l.solar_kwh||0,l.utility_kwh||0);checkVoiceAlerts(l.solar_kwh||0,l.utility_kwh||0,lw,bp);updatePowerFlow(l.solar_kwh||0,l.utility_kwh||0,lw,bp);
      setAlerts(l.solar_kwh||0, l.utility_kwh||0, lw);
      updateBattHours(bp, lw);
      document.getElementById('tempVal').textContent = '49°C';
      document.getElementById('fanVal').textContent = '1%';
      document.getElementById('modeBadge').textContent = (l.solar_kwh||0)>0 ? '☀️ SOLAR' : '🔌 GRID';
    }
    document.getElementById('updTime').textContent = 'Updated: ' + new Date().toLocaleTimeString();
  } catch(e){ console.error(e); }
}

loadAll();
setInterval(loadAll, 30000);loadWeather();setInterval(loadWeather,600000);loadForecast();setInterval(loadForecast,1800000);updateApplianceTimes();setInterval(updateApplianceTimes,60000);
</script>