import http from 'node:http';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { buildDashboard } from './aggregator.js';
import { readStatus } from './db.js';
import { config } from './config.js';

const imageCache = new Map();
const PYTHON = process.env.PYTHON_BIN
  || (process.platform === 'win32'
    ? 'C:/Users/Shen/.workbuddy/binaries/python/versions/3.13.12/python.exe'
    : 'python3');

function renderScreenPng(language = 'zh', port = 8787) {
  return new Promise((resolve, reject) => {
    const script = path.join(import.meta.dirname, '..', 'tools', 'render_screen.py');
    const child = spawn(PYTHON, [script, '--lang', language, '--url', 'http://127.0.0.1:' + port + '/api/dashboard'], { stdio: ['ignore', 'pipe', 'pipe'], timeout: 90000 });
    const chunks = [];
    child.stdout.on('data', d => chunks.push(d));
    child.stderr.on('data', d => process.stderr.write('[render] ' + d));
    child.on('error', reject);
    child.on('close', code => {
      if (code === 0) resolve(Buffer.concat(chunks));
      else reject(new Error('render exit code ' + code));
    });
  });
}

function sendJson(res, obj) {
  res.writeHead(200, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': '*'
  });
  res.end(JSON.stringify(obj, null, 2));
}

// --- HTML dashboard (client-rendered, self-refreshing, one-screen layout) ---
function renderHtml(initial) {
  const initJson = JSON.stringify(initial ?? {})
    .replace(/</g, '\\u003c')
    .replace(/-->/g, '--\\u003e');
  return `<!doctype html><html lang="zh"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shawn Kanban</title>
<style>
:root{color-scheme:dark;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  min-height:100vh;padding:18px;font-size:14px;}
.wrap{max-width:1180px;margin:0 auto;}
header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #21262d;}
header h1{font-size:20px;letter-spacing:1px;}
header h1 span{color:#58a6ff;}
header .meta{font-size:12px;color:#8b949e;}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;margin-left:6px;}
.badge.ok{background:#122;color:#3fb950;border:1px solid #238636;}
.badge.err{background:#221;color:#f85149;border:1px solid #da3633;}
.grid{display:grid;gap:12px;margin-bottom:12px;}
.grid.quotas{grid-template-columns:repeat(3,1fr);}
.grid.main{grid-template-columns:1.1fr .9fr;}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:14px 16px;}
.card h2{font-size:12px;color:#8b949e;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;display:flex;align-items:center;gap:6px;}
.card h2 .ico{font-size:14px;}
.quota-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;}
.quota-row:last-child{margin-bottom:0;}
.qname{color:#e6edf3;font-size:13px;}
.qval{font-size:15px;font-weight:700;}
.qbar{height:4px;background:#21262d;border-radius:2px;margin-top:4px;overflow:hidden;}
.qbar i{display:block;height:100%;border-radius:2px;}
.qsub{font-size:11px;color:#8b949e;margin-top:4px;}
.weather-main{display:flex;align-items:center;gap:14px;}
.weather-ico{font-size:44px;line-height:1;}
.weather-temp{font-size:40px;font-weight:800;}
.weather-temp small{font-size:18px;color:#8b949e;}
.weather-detail{margin-top:10px;font-size:13px;color:#c9d1d9;}
.weather-detail b{color:#e6edf3;}
.stocks-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px;}
.stock{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;}
.stock .sh{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:2px;}
.stock .nm{font-size:14px;font-weight:700;}
.stock .nm small{color:#8b949e;font-weight:500;margin-left:5px;font-size:11px;}
.stock .pr{font-size:19px;font-weight:800;margin-top:4px;}
.stock .pct{font-size:12px;font-weight:600;margin-top:2px;}
.stock .spark{height:56px;margin-top:8px;}
.stock .spark svg{width:100%;height:100%;}
.stock .ft{font-size:10px;color:#6e7681;margin-top:6px;}
.up{color:#f6465d;} .down{color:#0ecb81;} .flat{color:#8b949e;}
.fx-cards{display:flex;gap:12px;}
.fx-card{flex:1;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:12px 14px;text-align:center;}
.fx-card .fc{font-size:12px;color:#8b949e;margin-bottom:4px;}
.fx-card .fv{font-size:22px;font-weight:800;}
.clocks-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.clock{display:grid;grid-template-columns:4.5em 1fr auto;align-items:baseline;background:#161b22;border:1px solid #30363d;border-radius:10px;padding:8px 12px;}
.clock .cc{font-size:12px;color:#8b949e;}
.clock .ct{font-size:16px;font-weight:700;text-align:center;font-variant-numeric:tabular-nums;}
.clock .cd{font-size:11px;color:#6e7681;text-align:right;}
.loading{color:#8b949e;text-align:center;padding:40px;font-size:15px;}
@media(max-width:900px){
  .grid.quotas{grid-template-columns:1fr;}
  .grid.main{grid-template-columns:1fr;}
  .stocks-grid{grid-template-columns:repeat(2,1fr);}
}
</style></head><body>
<div class="wrap">
<header>
  <h1>SHAWN <span>KANBAN</span></h1>
  <div class="meta">
    <span id="clock" style="font-size:19px;font-weight:700;font-variant-numeric:tabular-nums;margin-right:14px;color:#e6edf3">--:--:--</span>
    <span id="meta">加载中…</span>
  </div>
</header>
<div id="app"><div class="loading">加载中…</div></div>
</div>
<script>
const INIT = ${initJson};
const W_ICONS = {晴:'☀️',晴转多云:'🌤️',多云:'⛅',阴:'☁️',小雨:'🌦️',中雨:'🌧️',大雨:'⛈️',雷阵雨:'⛈️',雪:'🌨️',雾:'🌫️',霾:'🌫️'};
function esc(s){return String(s ?? '').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function wIco(text){for(const k in W_ICONS){if((text||'').includes(k))return W_ICONS[k];}return '🌡️';}
function sparkSvg(closes){
  if(!closes||closes.length<2)return '';
  const w=100,h=50;let min=Math.min(...closes),max=Math.max(...closes);
  const span=max-min||1,n=closes.length;const pts=[];
  for(let i=0;i<n;i++){const x=(i/(n-1))*w;const y=h-3-((closes[i]-min)/span)*(h-6);pts.push(x.toFixed(1)+','+y.toFixed(1));}
  const up=closes[n-1]>=closes[0];
  const stroke=up?'#f6465d':'#0ecb81';
  const fill=up?'rgba(246,70,93,.14)':'rgba(14,203,129,.14)';
  const line=pts.join(' ');
  return '<svg viewBox="0 0 '+w+' '+h+'" preserveAspectRatio="none">'
    +'<polygon points="0,'+h+' '+line+' '+w+','+h+'" fill="'+fill+'"/>'
    +'<polyline points="'+line+'" fill="none" stroke="'+stroke+'" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>'
    +'</svg>';
}
function render(d){
  const q=d.quotas||{},w=d.weather||{},fx=d.fx||{};
  const st=(d.stocks&&d.stocks.items)||[];
  const cl=(d.clocks&&d.clocks.items)||[];
  const qbar=(used,total,color)=>{const p=total?Math.min(100,(used/total)*100):0;
    return '<div class="qbar"><i style="width:'+p+'%;background:'+color+'"></i></div>';};
  let wbHtml='<div class="qsub">不可用 ('+esc(wbError(q.workbuddy))+')</div>';
  function wbError(v){return v&&v.error?v.error:'未知';}
  if(q.workbuddy&&q.workbuddy.ok){
    const t=q.workbuddy.token||{};
    const used=t.size-t.remaining;const p=Math.round(t.percent||0);
    wbHtml='<div class="qval" style="font-size:14px">'+esc(q.workbuddy.model||'?')+'</div>'
      +'<div class="qval">'+fmtNum(t.remaining)+' <small style="font-size:11px;color:#8b949e">/ '+fmtNum(t.size)+'</small></div>'
      +qbar(used,t.size,p>80?'#f6465d':'#3fb950')
      +'<div class="qsub">已用 '+p+'%</div>';
  }
  function fmtNum(v){if(v==null)return 'n/a';return v.toLocaleString('zh');}
  const cc=q.claudecode||{};
  const cx=q.codex||{};
  const wd=w.ok
    ?'<div class="weather-main"><div class="weather-ico">'+wIco(w.text)+'</div>'
      +'<div><div class="weather-temp">'+esc(w.temp)+'<small>°C</small></div>'
      +'<div style="font-size:13px;color:#8b949e">'+esc(w.text||'')+'</div></div></div>'
      +'<div class="weather-detail">最高 <b>'+esc(w.high)+'</b>°C · 最低 <b>'+esc(w.low)+'</b>°C · 湿度 <b>'+esc(w.humidity)+'</b>%</div>'
    :'<div class="qsub">不可用 ('+esc(w.error||'')+')</div>';
  const stocks=st.map(s=>{
    const pct=s.changePct==null?'':(s.changePct>0?'+':'')+s.changePct.toFixed(2)+'%';
    const cls=s.changePct==null?'flat':(s.changePct>=0?'up':'down');
    const arrow=s.changePct==null?'':(s.changePct>=0?'▲':'▼');
    return '<div class="stock"><div class="sh"><span class="nm">'+esc(s.label)+'<small>'+esc(s.sym)+'</small></span></div>'
      +'<div class="pr '+cls+'">'+esc(s.price)+' <small style="font-size:11px;color:#8b949e">'+esc(s.currency)+'</small></div>'
      +'<div class="pct '+cls+'">'+arrow+' '+pct+'</div>'
      +'<div class="spark">'+sparkSvg(s.spark&&s.spark.closes)+'</div>'
      +'<div class="ft">'+(s.spark?s.spark.closes.length+'日走势':'无走势数据')+'</div></div>';
  }).join('');
  const fxCards=fx.cny!=null||fx.inr!=null
    ?'<div class="fx-cards"><div class="fx-card"><div class="fc">USD → CNY 人民币</div><div class="fv up">'+esc(fx.cny)+'</div></div>'
     +'<div class="fx-card"><div class="fc">USD → INR 卢比</div><div class="fv">'+esc(fx.inr)+'</div></div></div>'
    :'<div class="qsub">不可用 ('+esc(fx.error||'')+')</div>';
  const clocks=cl.map(c=>'<div class="clock"><span class="cc">'+esc(c.city)+'</span><span class="ct">'+esc(c.time)+'</span><span class="cd">'+esc(c.date)+'</span></div>').join('');
  return '<div class="grid quotas">'
    +'<div class="card"><h2><span class="ico">🤖</span>WorkBuddy 限额</h2>'+wbHtml+'</div>'
    +'<div class="card"><h2><span class="ico">💻</span>Claude Code 本周</h2>'
      +'<div class="qval">'+esc(cc.used7d)+' <small style="font-size:11px;color:#8b949e">/ '+esc(cc.cap)+'</small></div>'
      +qbar(Number(cc.used7d)||0,Number(cc.cap)||0,'#58a6ff')
      +'<div class="qsub">'+ (cc.ok?'':'本地估算')+'</div></div>'
    +'<div class="card"><h2><span class="ico">⚡</span>Codex 本周</h2>'
      +'<div class="qval">'+esc(cx.used7d)+' <small style="font-size:11px;color:#8b949e">/ '+esc(cx.cap)+'</small></div>'
      +qbar(Number(cx.used7d)||0,Number(cx.cap)||0,'#d29922')
      +'<div class="qsub">'+ (cx.ok?'':'本地估算')+'</div></div>'
    +'</div>'
    +'<div class="stocks-grid">'+stocks+'</div>'
    +'<div class="grid main">'
      +'<div class="card"><h2><span class="ico">🌤️</span>天气 · '+esc(w.city||'')+'</h2>'+wd+'</div>'
      +'<div class="card"><h2><span class="ico">💰</span>汇率 (1 '+esc(fx.base||'USD')+')</h2>'+fxCards+'</div>'
      +'</div>'
    +'<div class="grid"><div class="card"><h2><span class="ico">🕐</span>世界时钟</h2><div class="clocks-grid">'+clocks+'</div></div></div>';
}
function paint(){
  document.getElementById('meta').innerHTML=
    '<span>更新 '+new Date((INIT&&INIT.serverTime)||Date.now()).toLocaleTimeString()+'</span>';
  document.getElementById('app').innerHTML=render(INIT||{});
}
function tickClock(){
  const el=document.getElementById('clock');
  if(el)el.textContent=new Date().toLocaleTimeString('zh-CN',{hour12:false});
}
async function refresh(){
  try{const r=await fetch('/api/dashboard',{cache:'no-store'});INIT=await r.json();paint();}
  catch(e){document.getElementById('meta').innerHTML+='<span class="badge err">刷新失败</span>';}
}
let refreshTimer=null;
function scheduleRefresh(){
  const n=new Date();
  const nowMs=n.getMinutes()*60000+n.getSeconds()*1000+n.getMilliseconds();
  const slot=nowMs<1800000?1800000:3600000; // 对齐到下一个 :30 / :00
  clearTimeout(refreshTimer);
  refreshTimer=setTimeout(()=>{refresh();scheduleRefresh();},slot-nowMs);
}
tickClock();setInterval(tickClock,1000);
paint();
scheduleRefresh();
</script>
</body></html>`;
}

export function createServer({ db = null, cfg = config, renderImage = renderScreenPng } = {}) {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const remote = req.socket.remoteAddress || '?';
    const t = new Date().toISOString().slice(11, 23);
    console.log(`[dash] ${t} ${remote} ${req.method} ${url.pathname}`);

    if (url.pathname === '/api/dashboard') {
      try {
        const d = await buildDashboard(db);
        sendJson(res, d);
      } catch (e) {
        sendJson(res, { ok: false, error: e.message });
      }
      return;
    }

    if (url.pathname === '/api/status') {
      const status = db ? readStatus(db, { cwdFilter: cfg.cwdFilter }) : null;
      sendJson(res, { ok: true, data: status, serverTime: Date.now() });
      return;
    }

    if (url.pathname.startsWith('/api/image/')) {
      const key = url.pathname.slice('/api/image/'.length).replace(/\.png$/, '');
      const image = imageCache.get(key);
      if (!image) { res.writeHead(404); res.end('Image expired; request a new manifest'); return; }
      res.writeHead(200, { 'Content-Type': 'image/png', 'Content-Length': image.length });
      res.end(image); return;
    }
    if (url.pathname === '/api/display') {
      try {
        const language = url.searchParams.get('lang') === 'en' ? 'en' : 'zh';
        const png = await renderImage(language, req.socket.localPort);
        const sha256 = createHash('sha256').update(png).digest('hex');
        imageCache.set(sha256, png);
        while (imageCache.size > 8) imageCache.delete(imageCache.keys().next().value);
        sendJson(res, { schemaVersion: 1, image_url: '/api/image/' + sha256 + '.png', sha256,
          generatedAt: Date.now(), width: png.readUInt32BE(16), height: png.readUInt32BE(20),
          state: 'ready', language, staleAfterSeconds: 2700, refreshAfterSeconds: 1800 });
      } catch { res.writeHead(503); res.end('Image generation failed'); }
      return;
    }
    if (url.pathname === '/api/screen') {
      try {
        const png = await renderImage(url.searchParams.get('lang') === 'en' ? 'en' : 'zh', req.socket.localPort);
        res.writeHead(200, {
          'Content-Type': 'image/png',
          'Content-Length': png.length,
          'Cache-Control': 'no-store'
        });
        res.end(png);
      } catch (e) {
        process.stderr.write('[dash] screen render failed: ' + e.message + '\n');
        res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('render failed: ' + e.message);
      }
      return;
    }

    if (url.pathname === '/' || url.pathname === '/index.html') {
      try {
        const d = await buildDashboard(db);
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(renderHtml(d));
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('error: ' + e.message);
      }
      return;
    }

    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Not Found');
  });
}
