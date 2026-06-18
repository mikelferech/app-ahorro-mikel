import base64
import calendar
import io
import re
import json
import zipfile
import html
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
try:
    from streamlit_js_eval import streamlit_js_eval
except Exception:
    streamlit_js_eval = None
try:
    from PIL import Image
except Exception:
    Image = None

APP_TITLE = "Ahorro Mikel"
APP_VERSION = "0.8.11"
APP_UPDATED = "18/06/2026"
DATA = Path(".")
ASSETS = Path(".")
MFE_LOGO = Path("mfe_cabecera.png")
MFE_FAVICON = Path("mfe_favicon.png")
VADILLO_LOGO = Path("vadillo.svg")
MONTHS_ES = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
VACACIONES_ANUALES = 23

def get_page_icon():
    if Image is not None and MFE_FAVICON.exists():
        try:
            return Image.open(MFE_FAVICON)
        except Exception:
            return "💰"
    return "💰"

st.set_page_config(page_title=APP_TITLE, page_icon=get_page_icon(), layout="wide", initial_sidebar_state="collapsed")

# Intenta forzar nombre, favicon y manifiesto PWA en navegadores compatibles.
# En Streamlit Cloud no siempre se respeta al 100%, pero ayuda en Chrome/Android.
components.html("""
<script>
(function(){
  const d = window.parent.document;
  d.title = 'Ahorro Mikel';
  function upsert(tag, attrs){
    let q = tag;
    if(attrs.rel) q += '[rel="'+attrs.rel+'"]';
    let el = d.querySelector(q);
    if(!el){ el = d.createElement(tag); d.head.appendChild(el); }
    Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k,v));
  }
  upsert('link', {rel:'icon', href:'mfe_favicon.png?v=083', type:'image/png'});
  upsert('link', {rel:'apple-touch-icon', href:'mfe_icon_192.png?v=083'});
  upsert('link', {rel:'manifest', href:'manifest.json?v=083'});
  upsert('meta', {name:'theme-color', content:'#00a2eb'});
  upsert('meta', {name:'apple-mobile-web-app-title', content:'Ahorro Mikel'});
  upsert('meta', {name:'application-name', content:'Ahorro Mikel'});
})();
</script>
""", height=0, width=0)

st.markdown("""
<style>
.main .block-container {padding-top: .25rem; max-width: 1780px; font-size: 1.05rem;}
html, body, .stApp {font-size:16px!important;}
label, input, textarea, button, [data-testid="stWidgetLabel"] {font-size:1.00rem!important;}
h1 {font-size: 2.65rem !important;}
h2 {font-size: 2.05rem !important;} h3 {font-size: 1.55rem !important;}
[data-testid="stHeader"] {height:0rem!important;}
[data-testid="stMetricLabel"] {font-size: 1.06rem !important; font-weight: 900 !important;}
[data-testid="stMetricValue"] {font-size: 2.35rem !important; line-height:1.05!important;}
[data-testid="stMetricDelta"] {font-size: 1.00rem !important;}
.stTabs [data-baseweb="tab"] {height:2.75rem!important; padding-left:.75rem!important; padding-right:.75rem!important;}

.stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] {color:#00a2eb!important;}
.stTabs [data-baseweb="tab-highlight"] {background-color:#00a2eb!important;}
.stTabs [data-baseweb="tab"]:hover p, .stTabs [role="tab"]:hover p {color:#00a2eb!important;}
.stTabs [data-baseweb="tab"]:hover {border-color:#00a2eb!important;}
[data-testid="stDecoration"] {background:#00a2eb!important;}
.stTabs [data-baseweb="tab"] p, .stTabs [role="tab"] p {font-size: 1.05rem !important; font-weight: 900 !important;}
[data-testid="stExpander"] summary p {font-size:1.08rem!important; font-weight:900!important;}
.stDataFrame, [data-testid="stDataFrame"] {font-size: 1.05rem !important;}
[data-testid="stDataFrame"] [role="columnheader"], [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {background:#2F3B4F!important;color:#fff!important;font-weight:900!important;font-size:1.05rem!important;border-bottom:2px solid #00a2eb!important;}
[data-testid="stDataFrame"] div[role="columnheader"] {background:#2F3B4F!important;color:#fff!important;}
thead tr th {background:#2F3B4F!important;color:#fff!important;font-size:1.05rem!important;border-bottom:2px solid #00a2eb!important;}
[data-testid="stDataFrame"] [role="gridcell"] {font-size:1.00rem!important;}
.login-card {max-width:560px;margin:3.5rem auto 1rem auto;padding:1.8rem;border:1px solid rgba(128,128,128,.25);border-radius:24px;background:rgba(128,128,128,.06);text-align:center;}
.login-card img {max-width:360px;width:88%;margin-bottom:.6rem;}
.login-wrap {max-width:620px;margin:0 auto;}
.header-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:.25rem;min-height:0;}
.brand{display:flex;align-items:flex-start;gap:10px;}
.brand img{height:64px;max-width:280px;object-fit:contain;}
.brand h1{display:none!important;}
.userbox{text-align:right;min-width:150px;margin-top:.1rem;}
.logout-inline{display:flex;align-items:center;justify-content:flex-end;gap:10px;}
.logout-inline .user{font-weight:800;opacity:.85;font-size:1rem;}
.logout-icon button{font-size:1.25rem!important;padding:.25rem .58rem!important;min-height:34px!important;}
.bank-chip{border-radius:10px;padding:10px 12px;color:white;font-weight:900;text-align:center;margin-bottom:10px;font-size:1.05rem;}
.bank-icon{height:1.18em;width:1.18em;object-fit:contain;vertical-align:-0.20em;margin-right:.38em;display:inline-block;}
.account-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:1rem 0 1.2rem;}
.account-card{border-radius:18px;padding:1rem 1.15rem;color:#fff;font-weight:800;box-shadow:0 8px 24px rgba(0,0,0,.16);}
.account-card .bank{font-size:1.05rem;opacity:.92;display:flex;align-items:center;gap:.35rem;}
.account-card .amount{font-size:1.55rem;font-weight:950;margin-top:.35rem;}
.account-total{border:1px solid rgba(128,128,128,.22);border-radius:18px;padding:1rem 1.15rem;margin:1rem 0;background:rgba(47,59,79,.14);}
.monthly-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:10px;margin:.7rem 0 1rem;}
.month-card{border-radius:16px;padding:.8rem .55rem;text-align:center;font-weight:900;}
.month-card .m{opacity:.9;font-size:1rem}.month-card .v{font-size:1.15rem;margin-top:.18rem}.month-pos{background:rgba(22,163,74,.26);color:#86efac}.month-neg{background:rgba(220,38,38,.24);color:#fecaca}.month-zero{background:rgba(107,114,128,.22);color:#e5e7eb}
.backup-card{border:1px solid rgba(128,128,128,.25);border-radius:16px;padding:1rem;background:rgba(47,59,79,.13);margin:.8rem 0;}
.bank-name-cell{font-weight:900;display:inline-flex;align-items:center;gap:.35rem;}

.saldo-table-wrap{width:100%;overflow-x:auto;border:1px solid rgba(0,162,235,.85);border-radius:10px;margin-top:.35rem;}
.saldo-table{width:100%;border-collapse:collapse;font-size:1.00rem;min-width:760px;}
.saldo-table th{background:#1f2530!important;color:#cbd5e1!important;text-align:left;padding:9px 10px;border-bottom:1px solid rgba(148,163,184,.25);font-weight:850;}
.saldo-table td{padding:8px 10px;border-bottom:1px solid rgba(148,163,184,.15);border-right:1px solid rgba(148,163,184,.14);font-variant-numeric:tabular-nums;white-space:nowrap;}
.saldo-table tr:last-child td{border-bottom:none;}
.saldo-table .month-cell{color:#f8fafc;font-weight:800;}
.saldo-table .bank-amount{font-weight:950;}
.saldo-table .total-cell{color:#f8fafc;font-weight:900;}
.saldo-table .diff-pos{color:#22c55e;font-weight:950;}
.saldo-table .diff-neg{color:#ef4444;font-weight:950;}
.saldo-table .diff-zero{color:#94a3b8;font-weight:850;}
@media (max-width: 760px){.saldo-table{font-size:.92rem;min-width:680px}.saldo-table th,.saldo-table td{padding:7px 8px}}


.row-card{border-bottom:1px solid rgba(128,128,128,.15);padding:.35rem 0;}
.footer{margin-top:2rem;border-top:1px solid rgba(128,128,128,.22);padding:1rem 0 .2rem;display:flex;align-items:center;justify-content:center;gap:14px;opacity:.8;font-size:.86rem;}
.footer img{height:24px;width:auto;}
.app-footer-wrap{margin-top:1.8rem;border-top:1px solid rgba(128,128,128,.22);padding:.65rem 0 .25rem;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;}
.app-footer{display:flex;align-items:center;justify-content:center;gap:10px;opacity:.88;font-size:.88rem;white-space:nowrap;}
.app-footer img{height:30px;width:auto;object-fit:contain;}
.footer-right{display:flex;align-items:center;justify-content:flex-end;gap:10px;opacity:.9;}
.footer-meta{font-weight:750;opacity:.9}.footer-user{font-weight:850;opacity:.9}.footer-dot{opacity:.45}.footer-logout button{font-size:.95rem!important;padding:.2rem .52rem!important;min-height:30px!important;border-color:rgba(128,128,128,.35)!important;}
.irpf-desktop{display:block}.irpf-mobile{display:none}
.irpf-block{border:1px solid rgba(128,128,128,.22);border-radius:12px;overflow:hidden;margin-bottom:1rem}.irpf-block-title{background:#2F3B4F;color:#fff;font-weight:900;font-size:1.15rem;padding:.75rem;border-bottom:2px solid #c3005e}.irpf-row{display:grid;grid-template-columns:1fr auto;gap:.75rem;padding:.7rem .75rem;border-bottom:1px solid rgba(128,128,128,.18);align-items:center}.irpf-row:last-child{border-bottom:none}.irpf-row .num{font-weight:900;white-space:nowrap;font-variant-numeric:tabular-nums}.irpf-final{padding:.75rem;font-weight:900;text-align:center;border-radius:10px;margin-top:.6rem}
.company-card{border:1px solid rgba(128,128,128,.22);border-radius:14px;padding:1rem;background:rgba(47,59,79,.18);}
.company-preview{display:flex;align-items:center;justify-content:center;border-radius:14px;padding:1rem;margin:.5rem 0;border:1px solid rgba(128,128,128,.25);min-height:92px}.company-preview img{max-height:78px;max-width:95%;object-fit:contain;}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:18px;}
.cal-head{text-align:center;font-weight:900;opacity:.8;font-size:.78rem;}
.cal-month-title{text-align:center;font-weight:900;margin:.6rem 0 .3rem;font-size:1.12rem}.cal-day{min-height:38px;border-radius:7px;text-align:center;padding:6px;border:1px solid rgba(128,128,128,.18);font-size:.96rem;}
.cal-empty{opacity:.1}.cal-normal{background:rgba(128,128,128,.08)}.cal-red{background:#b91c1c;color:#fff}.cal-maroon{background:#5b1720;color:#fff}.cal-grey{background:#6b7280;color:#fff}.cal-green{background:#15803d;color:#fff;font-weight:900}
.vadillo-box{background:#fff;border-radius:16px;padding:12px;border:1px solid rgba(128,128,128,.2);display:flex;align-items:center;justify-content:center;margin-bottom:1rem;}
.vadillo-box img{max-height:78px;max-width:95%;object-fit:contain;}
@media (prefers-color-scheme: dark){.vadillo-box{background:#111827}.vadillo-box img{filter: grayscale(1) brightness(0) invert(1);}}
.payroll-table{width:100%;border-collapse:collapse;font-size:1.00rem;table-layout:fixed}.payroll-table th{background:#2F3B4F;color:#fff;padding:6px 6px;border-bottom:2px solid #00a2eb;text-align:right}.payroll-table th:first-child,.payroll-table td:first-child{text-align:left}.payroll-table td{padding:5px 6px;border:1px solid rgba(128,128,128,.22);text-align:right;font-variant-numeric:tabular-nums}.payroll-ok{background:rgba(16,185,129,.18)}.payroll-warn{background:rgba(245,158,11,.16)}.payroll-bad{background:rgba(220,38,38,.20)}.payroll-income{background:rgba(59,130,246,.18)!important;color:#dbeafe!important;font-weight:900}.compact-editor [data-testid="stDataFrame"]{font-size:.98rem!important}.irpf-table{width:100%;border-collapse:collapse;font-size:1.05rem}.irpf-table th{background:#c3005e!important;color:white!important;padding:9px;border-bottom:2px solid #c3005e!important}.irpf-table td{padding:6px 8px;border:1px solid rgba(128,128,128,.22)}.irpf-sec{background:#5f5f5f;color:white;font-weight:800}.irpf-pink{background:#ffd0d0;color:#111}.irpf-result-ok{background:#00c800!important;color:white!important;font-weight:900}.irpf-result-bad{background:#dc2626!important;color:white!important;font-weight:900}.irpf-num{text-align:right;font-variant-numeric:tabular-nums}.muted{opacity:.7}
.interest-summary{padding:.48rem .65rem;border:1px solid rgba(128,128,128,.25);border-radius:10px;line-height:1.35;display:grid;grid-template-rows:auto auto;gap:.22rem;}
.interest-summary .is-row{display:flex;align-items:center;justify-content:space-between;gap:.8rem;white-space:nowrap;}
.interest-summary b{font-weight:900}.interest-summary span{font-weight:850;font-variant-numeric:tabular-nums;}


/* Tablas Ahorro: importes por banco en color y diferencia positivo/negativo */
[data-testid="stDataFrame"] .bank-colored {font-weight:900!important;}

/* Azul MFE también en hover/focus de formularios y botones */
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color:#00a2eb!important;
  color:#00a2eb!important;
}
.stButton > button:focus, .stDownloadButton > button:focus {
  border-color:#00a2eb!important;
  box-shadow:0 0 0 0.12rem rgba(0,162,235,.35)!important;
}
input:focus, textarea:focus, [data-baseweb="input"]:focus-within, [data-baseweb="select"]:focus-within {
  border-color:#00a2eb!important;
  box-shadow:0 0 0 1px #00a2eb!important;
}
[data-baseweb="input"]:hover, [data-baseweb="select"]:hover {
  border-color:#00a2eb!important;
}


/* Vista móvil: tablas complejas convertidas en tarjetas */
.mobile-payroll {display:none;}
.desktop-payroll {display:block;}
@media (max-width: 760px){
  .main .block-container {padding-left:.65rem!important; padding-right:.65rem!important; font-size:1rem!important;}
  .desktop-payroll {display:none!important;}
  .mobile-payroll {display:block!important;}
  .irpf-desktop{display:none!important}.irpf-mobile{display:block!important}
  .app-footer-wrap{grid-template-columns:1fr;gap:.45rem;justify-items:center}.footer-right{justify-content:center}.app-footer{white-space:normal;flex-wrap:wrap;gap:.45rem;font-size:.82rem}.app-footer img{height:24px}.footer-meta{font-size:.82rem}.footer-user{font-size:.84rem}
  .irpf-row{font-size:1rem;}
  .pay-card{border:1px solid rgba(128,128,128,.30); border-radius:14px; padding:.8rem; margin:.7rem 0; background:rgba(47,59,79,.22);} 
  .pay-card.ok{background:rgba(16,185,129,.16);} .pay-card.warn{background:rgba(245,158,11,.16);} .pay-card.bad{background:rgba(220,38,38,.18);} 
  .pay-head{display:flex;justify-content:space-between;align-items:center;font-weight:900;font-size:1.1rem;margin-bottom:.45rem;}
  .pay-grid{display:grid;grid-template-columns:1fr 1fr;gap:.35rem .65rem;font-size:.95rem;}
  .pay-grid div:nth-child(even){text-align:right;font-weight:800;}
  .brand img{height:54px!important;max-width:240px!important;}
  [data-testid="stMetricValue"] {font-size:1.9rem!important;}
  h1 {font-size:2.1rem!important;} h2{font-size:1.65rem!important;} h3{font-size:1.28rem!important;}
}
/* Quitar últimos restos rojos de foco/hover */
* { --primary-color:#00a2eb; }
[data-baseweb="tab"]:hover, [data-baseweb="tab"][aria-selected="true"] {color:#00a2eb!important;}
.st-emotion-cache-10trblm, .st-emotion-cache-16idsys p {caret-color:#00a2eb!important;}

/* Modernización visual v0.8.3 */
:root{--mfe-blue:#00a2eb;--mfe-purple:#8b5cf6;--mfe-green:#22c55e;--mfe-red:#ef4444;}
.stButton > button, .stDownloadButton > button{border-radius:12px!important;font-weight:900!important;}
.modern-pill{display:inline-flex;align-items:center;gap:.35rem;padding:.22rem .62rem;border-radius:999px;background:rgba(0,162,235,.16);color:#7dd3fc;font-weight:900;font-size:.82rem;margin-top:.45rem;}
.metric-card{border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:1.0rem 1.15rem;background:linear-gradient(135deg,rgba(0,162,235,.20),rgba(15,23,42,.55));box-shadow:0 10px 28px rgba(0,0,0,.20);min-height:132px;}
.metric-card .mc-title{font-weight:850;opacity:.95;font-size:1.00rem;display:flex;align-items:center;gap:.5rem;}
.metric-card .mc-value{font-size:1.75rem;line-height:1.10;font-weight:950;margin-top:.6rem;}
.metric-card .mc-sub{margin-top:.45rem;opacity:.78;font-weight:750;font-size:.88rem;}
.metric-card.bad{background:linear-gradient(135deg,rgba(127,29,29,.40),rgba(15,23,42,.58));}
.metric-card.good{background:linear-gradient(135deg,rgba(20,83,45,.42),rgba(15,23,42,.58));}
.metric-card.purple{background:linear-gradient(135deg,rgba(88,28,135,.42),rgba(15,23,42,.58));}
.account-card{background-image:linear-gradient(135deg,rgba(255,255,255,.08),rgba(0,0,0,.18));}
.account-card .account-chip{display:inline-block;border-radius:999px;padding:.20rem .55rem;background:rgba(255,255,255,.15);font-size:.78rem;font-weight:900;margin-top:.45rem;}
.account-total{background:linear-gradient(135deg,rgba(15,23,42,.88),rgba(0,162,235,.12))!important;box-shadow:0 8px 26px rgba(0,0,0,.18);}
.bank-chip{box-shadow:0 8px 22px rgba(0,0,0,.18);}
.irpf-table td,.irpf-table th{white-space:nowrap;}
@media (max-width: 760px){
  .metric-card{min-height:110px;margin-bottom:.65rem;}
  .metric-card .mc-value{font-size:1.55rem;}
  .irpf-table{font-size:.92rem!important;}
  .irpf-table td,.irpf-table th{padding:5px 6px!important;white-space:nowrap;}
  .bank-name-cell{gap:.25rem;}
  .bank-icon{height:1.0em!important;width:1.0em!important;}
}


/* Ajustes v0.8.4 */

/* Ajuste específico Dashboard v0.8.11: quitar hueco superior real sin comprimir el resto */
.stTabs [data-baseweb="tab-panel"]{padding-top:.70rem!important;}
.stTabs [data-testid="stVerticalBlock"]{gap:1rem!important;}
.dashboard-kpi-start{height:0!important;min-height:0!important;margin:0!important;padding:0!important;line-height:0!important;overflow:hidden!important;}
.element-container:has(.dashboard-kpi-start){height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
.account-grid{margin-top:.75rem!important;}
.account-card{background-size:120% 120%;}
.bank-chip{background-image:linear-gradient(135deg,rgba(255,255,255,.14),rgba(0,0,0,.16));}
.irpf-table th{background:#c3005e!important;border-bottom:2px solid #c3005e!important;}
.irpf-block-title{background:#c3005e!important;border-bottom:2px solid #c3005e!important;}
</style>
""", unsafe_allow_html=True)

# ---------- util ----------
def b64(path: Path):
    try: return base64.b64encode(path.read_bytes()).decode()
    except Exception: return ""

def img_src(path: Path):
    s=b64(path); ext=path.suffix.lower().replace('.','') or 'png'
    if ext=='jpg': ext='jpeg'
    if ext=='svg': ext='svg+xml'
    return f"data:image/{ext};base64,{s}" if s else ""

def money(x):
    if pd.isna(x) if not isinstance(x, (list, dict, tuple)) else False: return 0.0
    if x is None or x=='': return 0.0
    if isinstance(x,(int,float)): return float(x)
    s=str(x).replace('€','').replace(' ','').strip()
    if ',' in s and '.' in s: s=s.replace('.','').replace(',','.')
    elif ',' in s: s=s.replace(',','.')
    try: return float(s)
    except Exception: return 0.0

def euro(x):
    s=f"{money(x):,.2f} €"
    return s.replace(',', 'X').replace('.', ',').replace('X','.')

def pct(x): return f"{money(x):.2f}%".replace('.', ',')
def euro_input_text(x):
    return f"{money(x):.2f}".replace('.', ',')


def month_label(d):
    d=pd.to_datetime(d, errors='coerce')
    if pd.isna(d): return ''
    return f"{MONTHS_ES[d.month-1]}{str(d.year)[-2:]}"

def date_label(d):
    d=pd.to_datetime(d, errors='coerce')
    if pd.isna(d): return ''
    return f"{d.day:02d}-{MONTHS_ES[d.month-1]}-{str(d.year)[-2:]}"

def month_date(label):
    label=str(label).strip().upper()
    m=MONTHS_ES.index(label[:3])+1; y=2000+int(label[3:])
    return date(y,m,1)

def month_options(start=2012, end=None):
    end=end or date.today().year+8
    return [date(y,m,1) for y in range(start,end+1) for m in range(1,13)]

def safe_key(s):
    return re.sub(r'[^A-Za-z0-9]+','_',str(s).strip()).strip('_') or 'Banco'


def hex_to_rgb(h):
    h=str(h or '').strip().lstrip('#')
    if len(h)==3:
        h=''.join(ch*2 for ch in h)
    try:
        return tuple(int(h[i:i+2],16) for i in (0,2,4))
    except Exception:
        return (107,114,128)

def is_dark_color(h):
    r,g,b=hex_to_rgb(h)
    return (0.299*r + 0.587*g + 0.114*b) < 140

def readable_text_color(bg):
    return '#FFFFFF' if is_dark_color(bg) else '#111827'

def lighten_hex(h, amount=0.14):
    r,g,b=hex_to_rgb(h)
    r=int(r+(255-r)*amount); g=int(g+(255-g)*amount); b=int(b+(255-b)*amount)
    return f'#{r:02x}{g:02x}{b:02x}'

def darken_hex(h, amount=0.16):
    r,g,b=hex_to_rgb(h)
    r=int(r*(1-amount)); g=int(g*(1-amount)); b=int(b*(1-amount))
    return f'#{r:02x}{g:02x}{b:02x}'

def bank_gradient(k):
    base=bank_color(k)
    if is_dark_color(base):
        return f"linear-gradient(135deg,{base},{lighten_hex(base,.18)})"
    return f"linear-gradient(135deg,{base},{darken_hex(base,.12)})"

def bank_text_color(k):
    color=bank_color(k)
    return '#FFFFFF' if is_dark_color(color) else color

def bank_cell_text_color(k):
    # Para tablas en modo oscuro: mantener el color corporativo, pero hacerlo legible.
    # Negro/Revolut -> blanco; colores muy oscuros -> versión aclarada del color; blanco -> blanco.
    color=bank_color(k)
    rgb=hex_to_rgb(color)
    if rgb == (0,0,0) or color.lower() in ['#000', '#000000']:
        return '#FFFFFF'
    if color.lower() in ['#fff', '#ffffff']:
        return '#FFFFFF'
    if is_dark_color(color):
        return lighten_hex(color, .55)
    return color

def rerun(): st.rerun()

# ---------- lightweight persistent store ----------
@st.cache_resource
def memory_store():
    # Persiste datos entre reruns/refresh mientras el servidor Streamlit siga activo.
    # También se escribe a CSV para poder descargar copia.
    return {}

def cookie_manager_resource():
    """CookieManager no debe ir cacheado: Streamlit lanza CachedWidgetWarning si un componente/widget se crea dentro de cache.
    Se instancia en cada rerun de forma ligera para poder usar cookies como respaldo de nóminas/vacaciones.
    """
    if stx is None:
        return None
    try:
        return stx.CookieManager(key="ahorro_mikel_cookie_manager")
    except Exception:
        return None

BROWSER_BACKUP_FILES = {"nominas.csv", "vacaciones.csv", "intereses.csv", "empresa_config.csv", "bancos.csv"}

# ---------- browser/local persistence ----------
def _df_to_json_payload(df):
    try:
        d = df.copy()
        return d.to_json(orient="records", date_format="iso", force_ascii=False)
    except Exception:
        return "[]"

def _df_from_json_payload(payload, columns=None):
    if not payload:
        return pd.DataFrame(columns=columns or [])
    try:
        data = json.loads(payload)
        df = pd.DataFrame(data)
        if columns:
            for c in columns:
                if c not in df:
                    df[c] = None
            df = df[columns]
        return df
    except Exception:
        return pd.DataFrame(columns=columns or [])

def _browser_key(name):
    return "ahorro_mikel_" + name.replace(".", "_")

def read_browser_df(name, columns=None):
    """Lee copia del navegador (localStorage). Esto sí sobrevive a F5/redeploys en el mismo móvil/PC."""
    if streamlit_js_eval is None:
        return pd.DataFrame(columns=columns or [])
    try:
        key = _browser_key(name)
        payload = streamlit_js_eval(
            js_expressions=f"localStorage.getItem({json.dumps(key)})",
            key=f"get_{key}"
        )
        return _df_from_json_payload(payload, columns)
    except Exception:
        return pd.DataFrame(columns=columns or [])

def write_browser_df(name, df):
    """Guarda copia en localStorage. La app sigue escribiendo CSV para exportar, pero localStorage evita pérdidas al recargar."""
    if streamlit_js_eval is None:
        return
    try:
        key = _browser_key(name)
        payload = _df_to_json_payload(df)
        js = f"localStorage.setItem({json.dumps(key)}, {json.dumps(payload)})"
        streamlit_js_eval(js_expressions=js, key=f"set_{key}_{abs(hash(payload))}", want_output=False)
    except Exception:
        pass

# ---------- csv storage ----------
def path(name): DATA.mkdir(exist_ok=True); return DATA/name

def read_csv(name, columns=None):
    """Lee datos de forma estable.

    Cambio v0.7.0:
    - Primero lee SIEMPRE el CSV real del servidor.
    - Solo usa memoria/localStorage si el CSV está vacío.
    - Esto evita que una copia vacía del navegador o de memoria tape los datos ya guardados.
    """
    p = path(name)
    df = pd.DataFrame(columns=columns or [])

    if p.exists():
        try:
            df = pd.read_csv(p)
        except Exception:
            df = pd.DataFrame(columns=columns or [])

    if columns:
        for c in columns:
            if c not in df:
                df[c] = None
        df = df[columns]

    # Si hay CSV con datos, normalmente es la fuente principal. Pero tras un redeploy
    # Streamlit Cloud puede volver al CSV del repositorio y tapar cambios hechos desde la app
    # (bancos nuevos, logo de empresa). Si el navegador tiene una copia más rica, la priorizamos
    # y rehidratamos el CSV del servidor.
    if not df.empty:
        if name in BROWSER_BACKUP_FILES:
            try:
                browser_df = read_browser_df(name, columns)
                use_browser = False
                if isinstance(browser_df, pd.DataFrame) and not browser_df.empty:
                    if name == 'empresa_config.csv':
                        csv_b64 = ''
                        br_b64 = ''
                        if 'LogoBase64' in df.columns:
                            csv_b64 = str(df.iloc[0].get('LogoBase64') or '')
                        if 'LogoBase64' in browser_df.columns:
                            br_b64 = str(browser_df.iloc[0].get('LogoBase64') or '')
                        use_browser = bool(br_b64 and br_b64.lower() not in ('nan','none') and (not csv_b64 or csv_b64.lower() in ('nan','none')))
                    elif name == 'bancos.csv':
                        use_browser = len(browser_df) > len(df)
                    else:
                        use_browser = len(browser_df) >= len(df) and len(browser_df) > 0
                if use_browser:
                    df = browser_df.copy()
                    try:
                        tmp = path(name + '.tmp')
                        df.to_csv(tmp, index=False)
                        tmp.replace(path(name))
                    except Exception:
                        pass
            except Exception:
                pass
            write_browser_df(name, df)
        memory_store()[name] = df.copy()
        return df.copy()

    # Si el CSV está vacío, probamos memoria del servidor.
    mem = memory_store().get(name)
    if isinstance(mem, pd.DataFrame) and not mem.empty:
        mdf = mem.copy()
        if columns:
            for c in columns:
                if c not in mdf:
                    mdf[c] = None
            mdf = mdf[columns]
        return mdf.copy()

    # Último recurso: copia del navegador.
    if name in BROWSER_BACKUP_FILES:
        browser_df = read_browser_df(name, columns)
        if isinstance(browser_df, pd.DataFrame) and not browser_df.empty:
            memory_store()[name] = browser_df.copy()
            # Rehidrata el CSV del servidor para siguientes cargas/exportación.
            try:
                tmp = path(name + '.tmp')
                browser_df.to_csv(tmp, index=False)
                tmp.replace(path(name))
            except Exception:
                pass
            return browser_df.copy()

    return df.copy()

def save_csv(name, df):
    DATA.mkdir(exist_ok=True)
    df = df.copy()
    tmp = path(name + '.tmp')
    final = path(name)
    df.to_csv(tmp, index=False)
    tmp.replace(final)
    memory_store()[name] = df.copy()
    if name in BROWSER_BACKUP_FILES:
        write_browser_df(name, df)

def build_ahorro_from_saldos():
    """Carga el histórico bueno desde saldos.xlsx si el CSV no existe o está vacío."""
    sx = Path("saldos.xlsx")
    cols = ['Fecha','BBVA','Openbank','Cajamar','Otros','Total','Diferencia']
    if not sx.exists():
        return pd.DataFrame(columns=cols)
    try:
        raw = pd.read_excel(sx, sheet_name='Ahorro BBVA', header=None)
        header_idx = None
        for i in range(min(len(raw), 25)):
            row = [str(x).strip().lower() for x in raw.iloc[i].tolist()]
            if 'mes' in row and ('cuenta' in row or 'bbva' in row):
                header_idx = i
                break
        if header_idx is None:
            return pd.DataFrame(columns=cols)
        df = pd.read_excel(sx, sheet_name='Ahorro BBVA', header=header_idx)
        df = df.rename(columns={'Mes':'Fecha','Cuenta':'BBVA','Openbank':'Openbank','Cajamar':'Cajamar','Otros':'Otros'})
        for c in ['Fecha','BBVA','Openbank','Cajamar','Otros']:
            if c not in df: df[c] = 0 if c != 'Fecha' else None
        df = df[['Fecha','BBVA','Openbank','Cajamar','Otros']].copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        for c in ['BBVA','Openbank','Cajamar','Otros']:
            df[c] = df[c].apply(money)
        df = df.drop_duplicates('Fecha', keep='first').sort_values('Fecha')
        df['Total'] = df[['BBVA','Openbank','Cajamar','Otros']].sum(axis=1)
        df['Diferencia'] = df['Total'].diff().fillna(0)
        return df[cols]
    except Exception:
        return pd.DataFrame(columns=cols)


# ---------- auth ----------
def secrets_auth():
    try: return str(st.secrets['auth']['username']), str(st.secrets['auth']['password'])
    except Exception: return None, None

def login_gate():
    u_ok,p_ok=secrets_auth()
    if 'auth_ok' not in st.session_state: st.session_state.auth_ok=False
    if st.session_state.auth_ok: return
    st.markdown(f"<div class='login-card'><img src='{img_src(MFE_LOGO)}'><p style='font-size:1.4rem;font-weight:900;margin:.2rem 0'>🔒 Acceso privado</p></div>", unsafe_allow_html=True)
    if not u_ok or not p_ok:
        st.error('Faltan credenciales en Streamlit Secrets.'); st.code('[auth]\nusername = "mikelferech"\npassword = "TU_CONTRASEÑA"'); st.stop()
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    c_left, c_mid, c_right = st.columns([1, 1.25, 1])
    with c_mid:
        with st.form('login_form'):
            u=st.text_input('Usuario')
            p=st.text_input('Contraseña', type='password')
            ok=st.form_submit_button('Entrar', use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if ok:
        if str(u).strip()==u_ok.strip() and str(p)==p_ok:
            st.session_state.auth_ok=True; st.rerun()
        else: st.error('Usuario o contraseña incorrectos')
    st.stop()

def logout_button():
    c1,c2=st.columns([7.5,1.5])
    with c2:
        a,b=st.columns([3,1])
        a.markdown("<div class='logout-inline'><span class='user'>👤 mikelferech</span></div>", unsafe_allow_html=True)
        if b.button('🚪', help='Cerrar sesión', key='logout_icon'):
            st.session_state.auth_ok=False; st.rerun()

# ---------- data ----------
def load_banks():
    """Carga bancos de forma robusta.

    v0.8.2: evita que una fila nueva/incompleta (por ejemplo al crear Revolut)
    rompa toda la app. Normaliza columnas antiguas y nuevas, rellena nulos y
    reconstruye el DataFrame desde diccionarios para evitar errores de dtype de pandas.
    """
    cols=['Clave','Nombre','Color','Activo','Orden','IconColor','IconWhite','IconColorBase64','IconWhiteBase64','IconColorExt','IconWhiteExt']
    defaults_rows=[
        {'Clave':'BBVA','Nombre':'BBVA','Color':'#072146','Activo':True,'Orden':1,'IconColor':'bbva_color.png','IconWhite':'bbva_white.png','IconColorBase64':'','IconWhiteBase64':'','IconColorExt':'png','IconWhiteExt':'png'},
        {'Clave':'Openbank','Nombre':'Openbank','Color':'#e40046','Activo':True,'Orden':2,'IconColor':'openbank_color.png','IconWhite':'openbank_white.png','IconColorBase64':'','IconWhiteBase64':'','IconColorExt':'png','IconWhiteExt':'png'},
        {'Clave':'Cajamar','Nombre':'Cajamar','Color':'#008c95','Activo':True,'Orden':3,'IconColor':'cajamar_color.png','IconWhite':'cajamar_white.png','IconColorBase64':'','IconWhiteBase64':'','IconColorExt':'png','IconWhiteExt':'png'},
        {'Clave':'Otros','Nombre':'Otros','Color':'#6b7280','Activo':True,'Orden':4,'IconColor':'','IconWhite':'','IconColorBase64':'','IconWhiteBase64':'','IconColorExt':'png','IconWhiteExt':'png'},
    ]
    defaults={r['Clave']:(r['IconColor'],r['IconWhite'],r['Color'],r['Orden'],r['Nombre']) for r in defaults_rows}

    df=read_csv('bancos.csv')
    if df is None or df.empty:
        out=pd.DataFrame(defaults_rows, columns=cols)
        save_csv('bancos.csv', out)
        return out

    # Acepta columnas antiguas/nuevas y elimina columnas totalmente sin nombre.
    df=df.copy()
    df.columns=[str(c).strip() for c in df.columns]
    df=df[[c for c in df.columns if c and not c.lower().startswith('unnamed')]]
    for c in cols:
        if c not in df.columns:
            df[c]=''

    rows=[]
    used=set()
    for pos, raw in enumerate(df.to_dict('records'), start=1):
        clave=safe_key(raw.get('Clave') or raw.get('Nombre') or '')
        if not clave or clave.lower() in ('nan','none'):
            continue
        nombre=str(raw.get('Nombre') or clave).strip()
        if not nombre or nombre.lower() in ('nan','none'):
            nombre=clave
        color=str(raw.get('Color') or '').strip()
        if not color or color.lower() in ('nan','none') or not color.startswith('#'):
            color=defaults.get(clave, ('','', '#6b7280', 99, clave))[2]
        activo_raw=raw.get('Activo', True)
        activo=str(activo_raw).strip().lower() in ['true','1','sí','si','yes','x','activo'] if activo_raw is not True else True
        try:
            orden=int(float(raw.get('Orden') if str(raw.get('Orden')).strip() not in ('','nan','None') else pos))
        except Exception:
            orden=defaults.get(clave, ('','', '#6b7280', pos, clave))[3] if clave in defaults else pos

        icon_color=str(raw.get('IconColor') or '').strip()
        icon_white=str(raw.get('IconWhite') or '').strip()
        icon_color_b64=str(raw.get('IconColorBase64') or '').strip()
        icon_white_b64=str(raw.get('IconWhiteBase64') or '').strip()
        icon_color_ext=str(raw.get('IconColorExt') or 'png').strip().replace('.','') or 'png'
        icon_white_ext=str(raw.get('IconWhiteExt') or 'png').strip().replace('.','') or 'png'
        if clave in defaults:
            if not icon_color or icon_color.lower() in ('nan','none'):
                icon_color=defaults[clave][0]
            if not icon_white or icon_white.lower() in ('nan','none'):
                icon_white=defaults[clave][1]
        # En bancos nuevos se permiten iconos vacíos.
        if icon_color.lower() in ('nan','none'): icon_color=''
        if icon_white.lower() in ('nan','none'): icon_white=''
        if icon_color_b64.lower() in ('nan','none'): icon_color_b64=''
        if icon_white_b64.lower() in ('nan','none'): icon_white_b64=''

        rows.append({'Clave':clave,'Nombre':nombre,'Color':color,'Activo':activo,'Orden':orden,
                     'IconColor':icon_color,'IconWhite':icon_white,
                     'IconColorBase64':icon_color_b64,'IconWhiteBase64':icon_white_b64,
                     'IconColorExt':icon_color_ext,'IconWhiteExt':icon_white_ext})
        used.add(clave)

    if not rows:
        rows=defaults_rows
    out=pd.DataFrame(rows, columns=cols).drop_duplicates('Clave', keep='last').sort_values(['Orden','Nombre'])

    # Si la versión antigua de bancos.csv no tenía columnas de iconos, persistimos la migración.
    try:
        save_csv('bancos.csv', out)
    except Exception:
        pass
    return out

def _bank_row(k):
    df=load_banks(); r=df[df['Clave']==k]
    return None if r.empty else r.iloc[0].to_dict()

def bank_icon_src(k, white=False):
    r=_bank_row(k)
    if not r: return ''
    b64_key='IconWhiteBase64' if white else 'IconColorBase64'
    ext_key='IconWhiteExt' if white else 'IconColorExt'
    file_key='IconWhite' if white else 'IconColor'
    raw=str(r.get(b64_key) or '')
    if raw and raw.lower() not in ('nan','none'):
        ext=str(r.get(ext_key) or 'png').replace('.','')
        if ext=='jpg': ext='jpeg'
        if ext=='svg': ext='svg+xml'
        return f"data:image/{ext};base64,{raw}"
    f=str(r.get(file_key) or '')
    if f and f.lower() not in ('nan','none') and Path(f).exists():
        return img_src(Path(f))
    return ''

def bank_icon_html(k, white=False, size=None):
    src=bank_icon_src(k, white=white)
    if not src: return ''
    style=f"height:{size}px;width:{size}px;" if size else ''
    alt=html.escape(bank_name(k))
    return f"<img class='bank-icon' style='{style}' src='{src}' alt='{alt}'>"

def bank_keys(active_only=False):
    df=load_banks();
    if active_only: df=df[df['Activo']]
    return df['Clave'].tolist()

def bank_name(k):
    df=load_banks(); r=df[df['Clave']==k]
    return k if r.empty else r.iloc[0]['Nombre']

def bank_color(k):
    df=load_banks(); r=df[df['Clave']==k]
    return '#6b7280' if r.empty else r.iloc[0]['Color']

def load_ahorro():
    keys=bank_keys(False)
    df = read_csv('ahorro.csv')

    def _needs_seed(d):
        if d.empty or 'Fecha' not in d.columns:
            return True
        tmp=d.copy()
        tmp['Fecha']=pd.to_datetime(tmp['Fecha'], errors='coerce')
        tmp=tmp.dropna(subset=['Fecha'])
        if tmp.empty:
            return True
        # Si no hay importes válidos, reconstruimos desde saldos.xlsx.
        total_cols=[c for c in keys if c in tmp.columns]
        if total_cols:
            total=tmp[total_cols].map(money).sum(axis=1).sum()
            if total <= 0:
                return True
        return False

    if _needs_seed(df):
        seeded = build_ahorro_from_saldos()
        if not seeded.empty:
            save_csv('ahorro.csv', seeded)
            df = seeded
    if df.empty:
        return pd.DataFrame(columns=['Fecha']+keys+['Total','Diferencia'])
    df['Fecha']=pd.to_datetime(df['Fecha'], errors='coerce').dt.date
    df=df.dropna(subset=['Fecha'])
    for k in keys:
        if k not in df: df[k]=0.0
        df[k]=df[k].apply(money)
    df=df.drop_duplicates('Fecha', keep='last').sort_values('Fecha')
    df['Total']=df[keys].sum(axis=1)
    df['Diferencia']=df['Total'].diff().fillna(0)
    return df[['Fecha']+keys+['Total','Diferencia']]

def save_ahorro(df):
    keys=bank_keys(False)
    for k in keys:
        if k not in df: df[k]=0.0
        df[k]=df[k].apply(money)
    df['Fecha']=pd.to_datetime(df['Fecha'], errors='coerce').dt.date
    df=df.dropna(subset=['Fecha']).drop_duplicates('Fecha', keep='last').sort_values('Fecha')
    df['Total']=df[keys].sum(axis=1); df['Diferencia']=df['Total'].diff().fillna(0)
    save_csv('ahorro.csv', df[['Fecha']+keys+['Total','Diferencia']])

def load_nominas():
    cols=['Anio','Mes','Bruto','SS','Desempleo','IRPF','Otros','NetoCalculado','Ingresado','Diferencia']
    df=read_csv('nominas.csv', cols)
    for c in cols:
        if c not in df: df[c]=None
    for c in ['Bruto','SS','Desempleo','IRPF','Otros','Ingresado']:
        df[c]=df[c].apply(money)
    if 'Anio' in df: df['Anio']=pd.to_numeric(df['Anio'], errors='coerce').fillna(date.today().year).astype(int)
    return calc_nominas(df)

def calc_nominas(df):
    if df.empty: return df
    df=df.copy()
    df['NetoCalculado']=df['Bruto']-df['SS']-df['Desempleo']-df['IRPF']-df['Otros']
    df['Diferencia']=df['Ingresado']-df['NetoCalculado']
    return df

def save_nominas(df):
    cols=['Anio','Mes','Bruto','SS','Desempleo','IRPF','Otros','NetoCalculado','Ingresado','Diferencia']
    out=calc_nominas(df)
    for c in cols:
        if c not in out:
            out[c]=None
    save_csv('nominas.csv', out[cols])

def load_vacaciones():
    cols=['Anio','Inicio','Fin','Dias','Nota']
    df=read_csv('vacaciones.csv', cols)
    for c in cols:
        if c not in df:
            df[c]=None
    return df

def save_vacaciones(df):
    cols=['Anio','Inicio','Fin','Dias','Nota']
    out=df.copy()
    for c in cols:
        if c not in out:
            out[c]=None
    save_csv('vacaciones.csv', out[cols])


def nomina_status(diff):
    diff=money(diff)
    if abs(diff) <= 0.01:
        return '✅ Correcto'
    if abs(diff) <= 1.00:
        return '🟡 Revisar'
    return '🔴 Diferencia'

def style_nominas(row):
    diff=money(row.get('Diferencia',0))
    if abs(diff) <= 0.01:
        color='background-color: rgba(22, 163, 74, .18); color: inherit;'
    elif abs(diff) <= 1.00:
        color='background-color: rgba(234, 179, 8, .18); color: inherit;'
    else:
        color='background-color: rgba(220, 38, 38, .18); color: inherit;'
    return [color for _ in row]

def payroll_status_class(diff):
    diff = money(diff)
    if abs(diff) <= 0.01:
        return 'payroll-ok'
    if abs(diff) <= 1:
        return 'payroll-warn'
    return 'payroll-bad'

def payroll_html(df):
    cols = ['Mes','Bruto','SS','Desempleo','IRPF','Otros','NetoCalculado','Ingresado','Diferencia','Estado']
    headers = ['Mes','Bruto','SS','Desempleo','IRPF','Otros','Neto','Ingresado','Dif.','Estado']
    html = "<table class='payroll-table'><thead><tr>" + ''.join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>"
    for _, r in df[cols].iterrows():
        cls = payroll_status_class(r.get('Diferencia',0))
        html += f"<tr class='{cls}'>"
        for c in cols:
            val = r.get(c, '')
            cell_cls = ' class="payroll-income"' if c == 'Ingresado' else ''
            if c in ['Bruto','SS','Desempleo','IRPF','Otros','NetoCalculado','Ingresado','Diferencia']:
                val = euro(val)
            html += f"<td{cell_cls}>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def payroll_mobile_html(df):
    cols = ['Mes','Bruto','SS','Desempleo','IRPF','Otros','NetoCalculado','Ingresado','Diferencia','Estado']
    html = "<div class='mobile-payroll'>"
    for _, r in df[cols].iterrows():
        diff = money(r.get('Diferencia', 0))
        cls = 'ok' if abs(diff) <= 0.01 else ('warn' if abs(diff) <= 1 else 'bad')
        html += f"<div class='pay-card {cls}'>"
        html += f"<div class='pay-head'><span>{r.get('Mes','')}</span><span>{r.get('Estado','')}</span></div>"
        html += "<div class='pay-grid'>"
        for label, col in [('Neto', 'NetoCalculado'), ('Ingresado', 'Ingresado'), ('Diferencia', 'Diferencia'), ('Bruto', 'Bruto'), ('SS', 'SS'), ('Desempleo', 'Desempleo'), ('IRPF', 'IRPF'), ('Otros', 'Otros')]:
            html += f"<div>{label}</div><div>{euro(r.get(col,0))}</div>"
        html += "</div></div>"
    html += "</div>"
    return html

def ordered_nominas(df):
    order={m:i+1 for i,m in enumerate(MONTHS_ES)}
    # Soporte futuro para 14 pagas: colocamos extras junto a verano/navidad.
    order.update({'EXTRA VERANO':6.5, 'EXTRA JUL':6.5, 'PAGA VERANO':6.5, 'EXTRA NAVIDAD':12.5, 'EXTRA DIC':12.5, 'PAGA NAVIDAD':12.5})
    if df.empty: return df
    out=df.copy(); out['_m']=out['Mes'].map(order).fillna(99)
    return out.sort_values(['Anio','_m']).drop(columns=['_m'])

def load_intereses():
    cols=['Anio','Mes','Banco','InteresBruto','Saldo','Retencion','NetoEsperado','Ingresado','Diferencia']
    df=read_csv('intereses.csv', cols)
    for c in cols:
        if c not in df: df[c]=None
    for c in ['InteresBruto','Saldo','Ingresado']:
        df[c]=df[c].apply(money)
    if not df.empty: df['Anio']=pd.to_numeric(df['Anio'], errors='coerce').fillna(date.today().year).astype(int)
    return calc_intereses(df)

def calc_intereses(df):
    df=df.copy()
    if df.empty: return df
    df['Retencion']=df['InteresBruto']*0.19
    df['NetoEsperado']=df['InteresBruto']-df['Retencion']
    df['Diferencia']=df['Ingresado']-df['NetoEsperado']
    return df

def save_intereses(df): save_csv('intereses.csv', calc_intereses(df))

# ---------- views ----------
def header():
    st.markdown(f"""
    <div class='header-row'><div class='brand'><img src='{img_src(MFE_LOGO)}'></div><div></div></div>
    """, unsafe_allow_html=True)

def footer():
    logo_src = img_src(MFE_FAVICON) or img_src(MFE_LOGO)
    img_html = f"<img src='{logo_src}'>" if logo_src else ""
    st.markdown(
        f"<div class='app-footer-wrap'><div></div><div class='app-footer'>{img_html}<span class='footer-meta'>Ahorro Mikel v{APP_VERSION} · {APP_UPDATED}</span></div><div class='footer-right'><span class='footer-user'>👤 mikelferech</span><span class='footer-logout-slot'></span></div></div>",
        unsafe_allow_html=True,
    )
    # El botón real se coloca a la derecha del footer usando columnas, para mantener la acción de logout nativa de Streamlit.
    l, m, r1, r2 = st.columns([7.2, 1.2, 1.1, .5])
    with r2:
        st.markdown("<div class='footer-logout'>", unsafe_allow_html=True)
        if st.button('🚪', help='Cerrar sesión', key='logout_footer_compact'):
            st.session_state.auth_ok = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def export_excel_bytes():
    bio=io.BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        load_ahorro().to_excel(writer, sheet_name='Ahorro', index=False)
        load_banks().to_excel(writer, sheet_name='Bancos', index=False)
        pd.DataFrame([load_empresa_config()]).to_excel(writer, sheet_name='Empresa', index=False)
        load_nominas().to_excel(writer, sheet_name='Nominas', index=False)
        load_intereses().to_excel(writer, sheet_name='Intereses', index=False)
        load_vacaciones().to_excel(writer, sheet_name='Vacaciones', index=False)
        read_csv('festivos.csv').to_excel(writer, sheet_name='Festivos', index=False)
    bio.seek(0); return bio.getvalue()

def _save_uploaded_icon(uploaded, clave, kind, existing_path='', existing_b64='', existing_ext='png'):
    if uploaded is None:
        return existing_path or '', existing_b64 or '', existing_ext or 'png'
    data=uploaded.getvalue()
    suffix=Path(uploaded.name).suffix.lower() or '.png'
    ext=suffix.replace('.','') or 'png'
    filename=f"bank_{safe_key(clave).lower()}_{kind}{suffix}"
    try:
        Path(filename).write_bytes(data)
    except Exception:
        pass
    return filename, base64.b64encode(data).decode(), ext

def render_bank_config(prefix='bank_config'):
    with st.expander('⚙️ Configuración de bancos', expanded=False):
        cfg=load_banks().reset_index(drop=True)
        st.caption('Edita nombres, colores, iconos, orden, activa/oculta o añade bancos. Recomendado: PNG 128×128 transparente. Sube logo color y logo blanco.')
        rows=[]
        for i,r in cfg.iterrows():
            st.markdown(f"<div class='row-card'>{bank_icon_html(r['Clave'], white=False, size=22)}<b>{html.escape(str(r['Nombre']))}</b></div>", unsafe_allow_html=True)
            c=st.columns([1.0,1.45,1.0,.65,.65,.55])
            clave=c[0].text_input('Clave', value=r['Clave'], key=f'{prefix}_clave_{i}')
            nombre=c[1].text_input('Nombre', value=r['Nombre'], key=f'{prefix}_nombre_{i}')
            color=c[2].color_picker('Color', value=str(r['Color']), key=f'{prefix}_color_{i}')
            activo=c[3].checkbox('Activo', value=bool(r['Activo']), key=f'{prefix}_act_{i}')
            orden=c[4].number_input('Orden', value=int(r['Orden']), step=1, key=f'{prefix}_orden_{i}')
            borrar=c[5].button('❌', key=f'{prefix}_del_{i}', help='Eliminar banco')
            ic=st.columns(2)
            up_color=ic[0].file_uploader('Logo color', type=['png','svg'], key=f'{prefix}_icon_color_{i}')
            up_white=ic[1].file_uploader('Logo blanco', type=['png','svg'], key=f'{prefix}_icon_white_{i}')
            icon_color, icon_color_b64, icon_color_ext = _save_uploaded_icon(up_color, clave, 'color', r.get('IconColor',''), r.get('IconColorBase64',''), r.get('IconColorExt','png'))
            icon_white, icon_white_b64, icon_white_ext = _save_uploaded_icon(up_white, clave, 'white', r.get('IconWhite',''), r.get('IconWhiteBase64',''), r.get('IconWhiteExt','png'))
            if not borrar:
                rows.append({'Clave':safe_key(clave),'Nombre':nombre or clave,'Color':color,'Activo':activo,'Orden':orden,
                             'IconColor':icon_color,'IconWhite':icon_white,'IconColorBase64':icon_color_b64,'IconWhiteBase64':icon_white_b64,
                             'IconColorExt':icon_color_ext,'IconWhiteExt':icon_white_ext})
        st.divider()
        st.markdown('**➕ Añadir banco nuevo**')
        c=st.columns([1.1,1.8,1.1,.7,.7])
        n_clave=c[0].text_input('Nueva clave', key=f'{prefix}_new_clave')
        n_nombre=c[1].text_input('Nuevo nombre', key=f'{prefix}_new_nombre')
        n_color=c[2].color_picker('Nuevo color', value='#6b7280', key=f'{prefix}_new_color')
        n_act=c[3].checkbox('Mostrar', value=True, key=f'{prefix}_new_act')
        n_order=c[4].number_input('Orden nuevo', value=len(cfg)+1, step=1, key=f'{prefix}_new_order')
        ic=st.columns(2)
        n_icon_color=ic[0].file_uploader('Logo color nuevo', type=['png','svg'], key=f'{prefix}_new_icon_color')
        n_icon_white=ic[1].file_uploader('Logo blanco nuevo', type=['png','svg'], key=f'{prefix}_new_icon_white')
        if st.button('Guardar configuración de bancos', use_container_width=True, key=f'{prefix}_save'):
            if n_clave or n_nombre:
                new_clave=safe_key(n_clave or n_nombre)
                icp, icb64, icext=_save_uploaded_icon(n_icon_color, new_clave, 'color')
                iwp, iwb64, iwext=_save_uploaded_icon(n_icon_white, new_clave, 'white')
                rows.append({'Clave':new_clave,'Nombre':n_nombre or n_clave,'Color':n_color,'Activo':n_act,'Orden':n_order,
                             'IconColor':icp,'IconWhite':iwp,'IconColorBase64':icb64,'IconWhiteBase64':iwb64,'IconColorExt':icext,'IconWhiteExt':iwext})
            out=pd.DataFrame(rows).drop_duplicates('Clave', keep='last').sort_values('Orden')
            save_csv('bancos.csv', out)
            a=load_ahorro()
            for k in out['Clave']:
                if k not in a: a[k]=0.0
            save_ahorro(a)
            st.success('Bancos guardados'); st.rerun()

def kpis(df):
    valid=df[df['Total']>0].sort_values('Fecha') if not df.empty else pd.DataFrame()
    if valid.empty:
        st.warning('Aún no hay datos válidos de ahorro.'); return
    last=valid.iloc[-1]
    diff=money(last.get('Diferencia',0))
    bbva_key='BBVA' if 'BBVA' in bank_keys(False) else (bank_keys(True)[0] if bank_keys(True) else '')
    bbva_val=money(last.get(bbva_key,0)) if bbva_key else 0
    otras=money(last.get('Total',0))-bbva_val
    diff_cls='good' if diff>=0 else 'bad'
    diff_icon='📈' if diff>=0 else '📉'
    bbva_icon=bank_icon_html(bbva_key, white=True, size=26) if bbva_key else '🏦'
    html_k=f"""
    <div class='account-grid'>
      <div class='metric-card'><div class='mc-title'>📅 Total actual · {month_label(last.Fecha)}</div><div class='mc-value'>{euro(last.Total)}</div><span class='modern-pill'>Saldo actual</span></div>
      <div class='metric-card {diff_cls}'><div class='mc-title'>{diff_icon} Último +/-</div><div class='mc-value'>{euro(diff)}</div><span class='modern-pill'>{'Subida' if diff>=0 else 'Bajada'}</span></div>
      <div class='metric-card'><div class='mc-title'>{bbva_icon} BBVA</div><div class='mc-value'>{euro(bbva_val)}</div><span class='modern-pill'>Cuenta principal</span></div>
      <div class='metric-card purple'><div class='mc-title'>💠 Otras cuentas</div><div class='mc-value'>{euro(otras)}</div><div class='mc-sub'>Todos los bancos excepto BBVA</div></div>
    </div>
    """
    st.markdown(html_k, unsafe_allow_html=True)

def render_patrimonio_chart(df, prefix="chart"):
    if df.empty: return
    df=df.sort_values('Fecha').copy(); df['Mes']=df['Fecha'].apply(month_label)
    fig=go.Figure(go.Scatter(
        x=df['Mes'], y=df['Total'], mode='lines+markers',
        line=dict(width=3, color='#60a5fa'),
        marker=dict(size=6, color='#93c5fd', line=dict(width=1, color='#e0f2fe')),
        fill='tozeroy', fillcolor='rgba(37,99,235,.24)',
        hovertemplate='%{x}<br>%{y:,.2f} €<extra></extra>'
    ))
    fig.update_layout(
        title='Patrimonio histórico', height=520, margin=dict(l=15,r=15,t=45,b=15),
        paper_bgcolor='rgba(15,23,42,0)', plot_bgcolor='rgba(15,23,42,.08)'
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_patrimonio")

def render_diff_chart(df, prefix="chart"):
    if df.empty: return
    df=df.sort_values('Fecha').copy(); df['Mes']=df['Fecha'].apply(month_label)
    mode = st.selectbox('Vista +/- mensual', ['Marcar gasto extraordinario', 'Zoom normal', 'Completa'], key=f'{prefix}_diff_mode')
    diffs = df['Diferencia'].astype(float)
    colors=['#16a34a' if v>=0 else '#dc2626' for v in diffs]
    fig2=go.Figure(go.Bar(
        x=df['Mes'], y=diffs, marker_color=colors, marker_line=dict(color='rgba(255,255,255,.18)', width=.6),
        opacity=.92, customdata=diffs, hovertemplate='%{x}<br>%{customdata:,.2f} €<extra></extra>'
    ))
    title='+/- mensual'
    normal = diffs.copy()
    if len(normal) > 6:
        q1=normal.quantile(.25); q3=normal.quantile(.75); iqr=q3-q1
        low=q1-3*iqr; high=q3+3*iqr
        no_out=normal[(normal>=low)&(normal<=high)]
    else:
        no_out=normal
    if no_out.empty: no_out=normal
    if mode in ['Marcar gasto extraordinario','Zoom normal'] and len(no_out)>0:
        pad=max(500, (no_out.max()-no_out.min())*.20)
        ymin=min(no_out.min()-pad, -500)
        ymax=max(no_out.max()+pad, 500)
        fig2.update_yaxes(range=[ymin,ymax])
        title += ' · zoom'
    if mode=='Marcar gasto extraordinario' and len(diffs)>0:
        threshold = min(-10000, no_out.min() - max(1000, abs(no_out.std())*2 if len(no_out)>1 else 1000))
        outliers=df[diffs < threshold]
        for _,r in outliers.iterrows():
            fig2.add_annotation(x=r['Mes'], y=0.04, yref='paper', text='⬇️ Gasto extraordinario', showarrow=False, font=dict(size=13, color='#fca5a5'), bgcolor='rgba(17,24,39,.65)', bordercolor='rgba(252,165,165,.5)', borderwidth=1)
    fig2.add_hrect(y0=0, y1=max(float(diffs.max()) if len(diffs) else 0, 0), fillcolor='rgba(34,197,94,.07)', line_width=0, layer='below')
    fig2.add_hrect(y0=min(float(diffs.min()) if len(diffs) else 0, 0), y1=0, fillcolor='rgba(239,68,68,.08)', line_width=0, layer='below')
    fig2.update_layout(title=title, height=520, margin=dict(l=15,r=15,t=45,b=15), paper_bgcolor='rgba(15,23,42,0)', plot_bgcolor='rgba(15,23,42,.08)')
    st.plotly_chart(fig2, use_container_width=True, key=f"{prefix}_diferencia")

def charts(df, prefix="chart"):
    if df.empty: return
    c1,c2=st.columns(2)
    with c1:
        render_patrimonio_chart(df, prefix)
    with c2:
        render_diff_chart(df, prefix)

def latest_valid_ahorro(df):
    if df.empty: return None
    v=df[df['Total']>0].sort_values('Fecha')
    if v.empty: return None
    return v.iloc[-1]

def render_account_cards(df):
    last=latest_valid_ahorro(df)
    if last is None: return
    keys=bank_keys(True)
    st.markdown(f"<div class='account-total'><b>💳 Último mes registrado · {month_label(last['Fecha'])}</b><br><span style='font-size:1.45rem;font-weight:950'>Total: {euro(last['Total'])}</span><div class='modern-pill'>Saldo actual</div></div>", unsafe_allow_html=True)
    html_cards="<div class='account-grid'>"
    for k in keys:
        val=money(last.get(k,0))
        bg=bank_color(k)
        txt=readable_text_color(bg)
        icon=bank_icon_html(k, white=True if is_dark_color(bg) else False, size=24)
        name=html.escape(bank_name(k))
        html_cards += f"<div class='account-card' style='background:{bank_gradient(k)};color:{txt}'><div class='bank'>{icon}{name} · {month_label(last['Fecha'])}</div><div class='amount'>{euro(val)}</div><span class='account-chip'>Saldo actual</span></div>"
    html_cards += "</div>"
    st.markdown(html_cards, unsafe_allow_html=True)
    prev=df[df['Fecha'] < last['Fecha']].sort_values('Fecha')
    if not prev.empty:
        p=prev.iloc[-1]
        diff=money(last['Total'])-money(p['Total'])
        pctv=diff/money(p['Total'])*100 if money(p['Total']) else 0
        col='#22c55e' if diff>=0 else '#ef4444'
        st.markdown(f"<div style='color:{col};font-weight:900;margin:.3rem 0 1rem'>Variación respecto a {month_label(p['Fecha'])}: {euro(diff)} ({pctv:+.2f}%)</div>".replace('.', ','), unsafe_allow_html=True)

def render_bank_distribution(df):
    last=latest_valid_ahorro(df)
    if last is None: return
    keys=[k for k in bank_keys(True) if money(last.get(k,0))>0]
    if not keys: return
    labels=[bank_name(k) for k in keys]
    values=[money(last.get(k,0)) for k in keys]
    total=sum(values) or 1
    colors=[bank_color(k) for k in keys]
    texts=[]
    for k,lab,val in zip(keys,labels,values):
        pctv=val/total*100
        if str(k).upper()=='BBVA' or str(k).lower()!='otros' or pctv>=3:
            texts.append(f"{lab}<br>{pctv:.1f}%")
        else:
            texts.append('')
    fig=go.Figure(go.Pie(labels=labels, values=values, hole=.58, marker=dict(colors=colors), text=texts, textinfo='text', hovertemplate='%{label}<br>%{value:,.2f} €<extra></extra>'))
    fig.update_layout(title=f'Distribución por banco · {month_label(last["Fecha"])}', height=420, margin=dict(l=5,r=5,t=45,b=5), showlegend=True, paper_bgcolor='rgba(15,23,42,0)', plot_bgcolor='rgba(15,23,42,.08)')
    if any((str(k).lower()=='otros' and v/total*100<3) for k,v in zip(keys,values)):
        fig.add_annotation(x=1.18, y=0.05, xref='paper', yref='paper', showarrow=False, align='left', font=dict(size=11, color='#9ca3af'), text='* Otros residual solo en leyenda')
    st.plotly_chart(fig, use_container_width=True, key='dashboard_distribution_bancos')

def _monthly_current_year(df):
    if df.empty: return pd.DataFrame()
    v=df[df['Total']>0].sort_values('Fecha').copy()
    if v.empty: return pd.DataFrame()
    latest_year=pd.to_datetime(v['Fecha']).dt.year.max()
    y=v[pd.to_datetime(v['Fecha']).dt.year==latest_year].copy()
    y['MonthNum']=pd.to_datetime(y['Fecha']).dt.month
    y=y.drop_duplicates('MonthNum', keep='last').sort_values('MonthNum')
    return y

def render_monthly_cards(df):
    y=_monthly_current_year(df)
    if y.empty: return
    y=y.copy()
    y['Acum']=y['Diferencia'].cumsum()
    st.markdown('### Ahorro mensual')
    html_m="<div class='monthly-grid'>"
    for _,r in y.iterrows():
        val=money(r['Diferencia']); cls='month-pos' if val>0 else ('month-neg' if val<0 else 'month-zero')
        html_m += f"<div class='month-card {cls}'><div class='m'>{MONTHS_ES[int(r['MonthNum'])-1].title()}</div><div class='v'>{euro(val)}</div></div>"
    html_m += '</div>'
    st.markdown(html_m, unsafe_allow_html=True)
    st.markdown('### Ahorro mensual acumulado')
    html_a="<div class='monthly-grid'>"
    for _,r in y.iterrows():
        val=money(r['Acum']); cls='month-pos' if val>0 else ('month-neg' if val<0 else 'month-zero')
        html_a += f"<div class='month-card {cls}'><div class='m'>{MONTHS_ES[int(r['MonthNum'])-1].title()}</div><div class='v'>{euro(val)}</div></div>"
    html_a += '</div>'
    st.markdown(html_a, unsafe_allow_html=True)

def create_backup_bytes():
    files=['ahorro.csv','bancos.csv','nominas.csv','vacaciones.csv','intereses.csv','festivos.csv','irpf_overrides.csv','empresa_config.csv','saldos.xlsx','mfe_cabecera.png','mfe_favicon.png']
    # Incluye iconos personalizados y bancos si existen.
    for pat in ['bank_*.*','bbva_*.png','openbank_*.png','cajamar_*.png','empresa_logo.*','empresa_logo_base64.txt']:
        for f in Path('.').glob(pat):
            if f.is_file() and f.name not in files:
                files.append(f.name)
    bio=io.BytesIO()
    with zipfile.ZipFile(bio, 'w', zipfile.ZIP_DEFLATED) as z:
        info={'app':'Ahorro Mikel','version':APP_VERSION,'fecha':APP_UPDATED,'creado':datetime.now().isoformat(timespec='seconds')}
        z.writestr('backup_info.json', json.dumps(info, ensure_ascii=False, indent=2))
        for name in files:
            f=Path(name)
            if f.exists() and f.is_file():
                z.write(f, arcname=f.name)
    bio.seek(0)
    return bio.getvalue()

def restore_backup(upload):
    allowed={'ahorro.csv','bancos.csv','nominas.csv','vacaciones.csv','intereses.csv','festivos.csv','irpf_overrides.csv','empresa_config.csv','saldos.xlsx','mfe_cabecera.png','mfe_favicon.png','empresa_logo_base64.txt'}
    prefixes=('bank_','bbva_','openbank_','cajamar_','empresa_logo')
    data=upload.getvalue()
    with zipfile.ZipFile(io.BytesIO(data),'r') as z:
        for n in z.namelist():
            base=Path(n).name
            if base in allowed or base.startswith(prefixes):
                Path(base).write_bytes(z.read(n))
    # Limpia caché en memoria para recargar desde ficheros restaurados.
    memory_store().clear()

def render_backup():
    st.header('💾 Backup')
    st.markdown("<div class='backup-card'><b>Exporta todos los datos de Ahorro Mikel</b><br>Incluye saldos, bancos, iconos, nóminas, vacaciones, intereses, IRPF y configuración.</div>", unsafe_allow_html=True)
    st.download_button('📥 Descargar backup completo', data=create_backup_bytes(), file_name=f"Ahorro_Mikel_Backup_{date.today().isoformat()}.zip", mime='application/zip', use_container_width=True)
    st.divider()
    st.subheader('📤 Restaurar backup')
    up=st.file_uploader('Sube un backup ZIP de Ahorro Mikel', type=['zip'], key='restore_backup_zip')
    confirm=st.checkbox('Entiendo que esto reemplazará los datos actuales', key='restore_confirm')
    if up is not None and confirm and st.button('Restaurar backup', use_container_width=True):
        restore_backup(up)
        st.success('Backup restaurado. Recargando app...')
        st.rerun()

def render_ahorro_acumulado_anual(df):
    if df.empty:
        return
    d=df[df['Total']>0].sort_values('Fecha').copy()
    if d.empty or 'Diferencia' not in d:
        return
    d['Anio']=pd.to_datetime(d['Fecha'], errors='coerce').dt.year
    annual=d.groupby('Anio', as_index=False)['Diferencia'].sum().rename(columns={'Diferencia':'Ahorro anual'})
    annual=annual.dropna(subset=['Anio']).sort_values('Anio')
    if annual.empty:
        return

    st.markdown('### Ahorro anual por años')
    c1,c2=st.columns([.95,1.35])

    show=annual.copy()
    show['Año']=show['Anio'].astype(int)
    show=show[['Año','Ahorro anual']]
    show_fmt=show.copy()
    show_fmt['Ahorro anual']=show_fmt['Ahorro anual'].apply(euro)

    with c1:
        try:
            sty=pd.DataFrame('', index=show_fmt.index, columns=show_fmt.columns)
            sty['Ahorro anual']=['color:#22c55e;font-weight:900;' if money(v)>=0 else 'color:#ef4444;font-weight:900;' for v in show['Ahorro anual']]
            st.dataframe(show_fmt.style.apply(lambda _x: sty, axis=None), hide_index=True, use_container_width=True)
        except Exception:
            st.dataframe(show_fmt, hide_index=True, use_container_width=True)

    with c2:
        vals=annual['Ahorro anual'].astype(float)
        colors=['#22c55e' if v>=0 else '#ef4444' for v in vals]
        fig=go.Figure(go.Bar(
            x=annual['Anio'].astype(int).astype(str), y=vals, name='Ahorro anual',
            marker_color=colors, marker_line=dict(color='rgba(255,255,255,.20)', width=.7), opacity=.94,
            text=[euro(v) for v in vals], textposition='outside',
            hovertemplate='%{x}<br>%{y:,.2f} €<extra></extra>'
        ))
        ymax=max([0]+[float(v) for v in vals])
        ymin=min([0]+[float(v) for v in vals])
        fig.add_hrect(y0=0, y1=ymax, fillcolor='rgba(34,197,94,.08)', line_width=0, layer='below')
        fig.add_hrect(y0=ymin, y1=0, fillcolor='rgba(239,68,68,.10)', line_width=0, layer='below')
        fig.add_hline(y=0, line_color='rgba(255,255,255,.45)', line_width=1)
        pad=max(500, (ymax-ymin)*.15 if ymax!=ymin else 500)
        fig.update_yaxes(range=[ymin-pad, ymax+pad])
        fig.update_layout(
            title='Ahorro anual por año', height=380, margin=dict(l=15,r=15,t=45,b=15),
            paper_bgcolor='rgba(15,23,42,0)', plot_bgcolor='rgba(15,23,42,.08)', showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, key='ahorro_anual_por_anio')

def render_dashboard():
    # Sin título interno: las pestañas ya indican la sección. Esto evita el hueco fantasma superior.
    df=load_ahorro()
    kpis(df)
    render_account_cards(df)
    # Dos primeros gráficos más anchos; donut más estrecho.
    c1,c2,c3=st.columns([1.35,1.35,.78])
    with c1:
        render_patrimonio_chart(df, "dashboard")
    with c2:
        render_diff_chart(df, "dashboard")
    with c3:
        render_bank_distribution(df)
    render_monthly_cards(df)
    st.download_button('⬇️ Descargar Excel actualizado', data=export_excel_bytes(), file_name='Ahorro_Mikel_actualizado.xlsx', use_container_width=False)

def render_ahorro():
    st.header('💰 Ahorro')
    df=load_ahorro(); kpis(df); render_bank_config("ahorro_banks")
    keys=bank_keys(True)
    with st.expander('➕ Añadir / actualizar mes', expanded=False):
        opts=month_options(2012, date.today().year+8)
        current=date(date.today().year,date.today().month,1)
        sel=st.selectbox('Mes', opts, index=opts.index(current) if current in opts else len(opts)-1, format_func=month_label)
        existing=df[df['Fecha']==sel]
        defaults=existing.iloc[0].to_dict() if not existing.empty else {}
        cols=st.columns(max(1,len(keys)))
        vals={'Fecha':sel}
        for i,k in enumerate(keys): vals[k]=cols[i].number_input(bank_name(k), value=float(money(defaults.get(k,0))), step=.01, format='%.2f', key=f'ah_new_{k}_{sel}')
        if st.button('Guardar mes', use_container_width=True):
            base=df[df['Fecha']!=sel].copy() if not df.empty else pd.DataFrame()
            save_ahorro(pd.concat([base,pd.DataFrame([vals])], ignore_index=True)); st.success('Guardado'); st.rerun()
    if df.empty: return
    charts(df, "ahorro")
    st.subheader('Tabla de saldos')
    chips=st.columns(max(1,len(keys)))
    for i,k in enumerate(keys): chips[i].markdown(f"<div class='bank-chip' style='background:{bank_gradient(k)};color:{readable_text_color(bank_color(k))}'>{bank_icon_html(k, white=True, size=22)}{bank_name(k)}</div>", unsafe_allow_html=True)
    table=df.sort_values('Fecha', ascending=False).copy(); table['Mes']=table['Fecha'].apply(month_label)
    show_cols=['Mes']+keys+['Total','Diferencia']
    raw_show=table[show_cols].rename(columns={k:bank_name(k) for k in keys})

    # Tabla Streamlit nativa: evita que HTML propio interfiera con el login/reruns.
    # Colorea cada saldo con el color de su banco y ajusta negro/blanco para que se lea
    # tanto en modo oscuro como si en el futuro se activa modo claro.
    show_fmt=raw_show.copy()
    for col in [bank_name(k) for k in keys]+['Total','Diferencia']:
        if col in show_fmt.columns:
            if col == 'Diferencia':
                show_fmt[col]=raw_show[col].apply(lambda v: '—' if abs(money(v))<0.005 else euro(money(v)))
            else:
                show_fmt[col]=raw_show[col].apply(lambda v: euro(money(v)))

    def _saldo_style(_df):
        styles=pd.DataFrame('', index=show_fmt.index, columns=show_fmt.columns)
        for k in keys:
            col=bank_name(k)
            if col in styles.columns:
                styles[col]=f'color:{bank_cell_text_color(k)};font-weight:950;'
        if 'Total' in styles.columns:
            styles['Total']='color:#f8fafc;font-weight:900;'
        if 'Diferencia' in styles.columns:
            vals=raw_show['Diferencia'].apply(money)
            styles['Diferencia']=[
                'color:#22c55e;font-weight:950;' if v>0 else
                ('color:#ef4444;font-weight:950;' if v<0 else 'color:#94a3b8;font-weight:850;')
                for v in vals
            ]
        return styles

    try:
        st.dataframe(show_fmt.style.apply(_saldo_style, axis=None), hide_index=True, use_container_width=True)
    except Exception:
        st.dataframe(show_fmt, hide_index=True, use_container_width=True)
    with st.expander('✏️ Editar / borrar saldo', expanded=False):
        labels=table['Mes'].tolist()
        sel_label=st.selectbox('Selecciona mes', labels, key='edit_ah_sel')
        row=table[table['Mes']==sel_label].iloc[0]
        cols=st.columns(max(1,len(keys)))
        new={'Fecha':row['Fecha']}
        for i,k in enumerate(keys):
            new[k]=cols[i].number_input(bank_name(k), value=float(money(row.get(k,0))), step=.01, format='%.2f', key=f'edit_ah_{k}_{sel_label}')
        c1,c2=st.columns(2)
        if c1.button('✏️ Guardar cambios', use_container_width=True):
            base=df[df['Fecha']!=row['Fecha']].copy(); save_ahorro(pd.concat([base,pd.DataFrame([new])], ignore_index=True)); st.success('Actualizado'); st.rerun()
        if c2.button('❌ Borrar mes', use_container_width=True):
            save_ahorro(df[df['Fecha']!=row['Fecha']].copy()); st.success('Borrado'); st.rerun()

    st.divider()
    render_ahorro_acumulado_anual(df)


def load_empresa_config():
    cols=['Nombre','ColorFondo','ColorTexto','LogoArchivo','Pagas','LogoBase64','LogoExt']
    df=read_csv('empresa_config.csv', cols)
    # Si se acaba de subir un logo en esta sesión, lo mantenemos como fuente prioritaria.
    session_cfg = st.session_state.get('empresa_cfg_cache')
    if isinstance(session_cfg, dict) and str(session_cfg.get('LogoBase64') or ''):
        try:
            csv_b64 = ''
            if isinstance(df, pd.DataFrame) and not df.empty:
                csv_b64 = str(df.iloc[0].to_dict().get('LogoBase64') or '')
            if not csv_b64 or csv_b64.lower() in ('nan','none'):
                df = pd.DataFrame([session_cfg], columns=cols)
                save_csv('empresa_config.csv', df)
        except Exception:
            pass
    browser_df = read_browser_df('empresa_config.csv', cols)

    # Si el CSV viene de una actualización y vuelve al logo por defecto,
    # pero el navegador tiene una configuración guardada con LogoBase64,
    # priorizamos la copia del navegador para que el logo personalizado no se pierda.
    if isinstance(browser_df, pd.DataFrame) and not browser_df.empty:
        try:
            brow = browser_df.iloc[0].to_dict()
            brow_b64 = str(brow.get('LogoBase64') or '')
            csv_b64 = ''
            if isinstance(df, pd.DataFrame) and not df.empty:
                csv_b64 = str(df.iloc[0].to_dict().get('LogoBase64') or '')
            if brow_b64 and brow_b64.lower() not in ('nan','none') and (not csv_b64 or csv_b64.lower() in ('nan','none')):
                df = browser_df.copy()
                try:
                    save_csv('empresa_config.csv', df)
                except Exception:
                    pass
        except Exception:
            pass

    if df.empty:
        df=pd.DataFrame([{'Nombre':'Empresa','ColorFondo':'#111827','ColorTexto':'#FFFFFF','LogoArchivo':'','Pagas':12,'LogoBase64':'','LogoExt':'png'}])
        save_csv('empresa_config.csv', df)
    r=df.iloc[0].to_dict()
    r['Nombre']=str(r.get('Nombre') or 'Empresa')
    r['ColorFondo']=str(r.get('ColorFondo') or '#111827')
    r['ColorTexto']=str(r.get('ColorTexto') or '#FFFFFF')
    r['LogoArchivo']=str(r.get('LogoArchivo') or '')
    r['LogoBase64']='' if pd.isna(r.get('LogoBase64')) else str(r.get('LogoBase64') or '')
    # Respaldo adicional en archivo de texto por si el CSV pierde la columna tras una actualización.
    if (not r['LogoBase64'] or r['LogoBase64'].lower() in ('nan','none')) and Path('empresa_logo_base64.txt').exists():
        try:
            r['LogoBase64']=Path('empresa_logo_base64.txt').read_text(encoding='utf-8').strip()
        except Exception:
            pass
    r['LogoExt']='png' if pd.isna(r.get('LogoExt')) else str(r.get('LogoExt') or 'png').replace('.','')
    try: r['Pagas']=int(float(r.get('Pagas') or 12))
    except Exception: r['Pagas']=12
    return r

def save_empresa_config(cfg):
    # Normaliza y guarda la configuración completa, incluyendo el logo embebido en Base64.
    cfg = dict(cfg)
    for k in ['Nombre','ColorFondo','ColorTexto','LogoArchivo','LogoBase64','LogoExt']:
        cfg[k] = '' if cfg.get(k) is None else str(cfg.get(k))
    try:
        cfg['Pagas'] = int(float(cfg.get('Pagas') or 12))
    except Exception:
        cfg['Pagas'] = 12
    df = pd.DataFrame([cfg], columns=['Nombre','ColorFondo','ColorTexto','LogoArchivo','Pagas','LogoBase64','LogoExt'])
    save_csv('empresa_config.csv', df)
    if str(cfg.get('LogoBase64') or '').strip():
        try:
            Path('empresa_logo_base64.txt').write_text(str(cfg.get('LogoBase64')), encoding='utf-8')
        except Exception:
            pass
    st.session_state['empresa_cfg_cache'] = cfg.copy()

def empresa_logo_src(cfg=None):
    cfg=cfg or load_empresa_config()
    raw=cfg.get('LogoBase64','')
    if raw and raw.lower() not in ('nan','none'):
        ext=str(cfg.get('LogoExt') or 'png').replace('.','')
        if ext=='jpg': ext='jpeg'
        if ext=='svg': ext='svg+xml'
        return f"data:image/{ext};base64,{raw}"
    p=Path(str(cfg.get('LogoArchivo') or ''))
    if str(p) and p.exists():
        return img_src(p)
    return None

def empresa_logo_path():
    cfg=load_empresa_config()
    p=Path(str(cfg.get('LogoArchivo') or ''))
    if str(p) and p.exists(): return p
    return None

def render_empresa_box():
    cfg=load_empresa_config()
    logo_src=empresa_logo_src(cfg)
    if logo_src:
        st.markdown(f"<div class='company-preview' style='background:{cfg['ColorFondo']};color:{cfg['ColorTexto']}'><img src='{logo_src}'></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='company-preview' style='background:{cfg['ColorFondo']};color:{cfg['ColorTexto']};font-weight:900'>{cfg['Nombre']}</div>", unsafe_allow_html=True)

def render_empresa_config():
    cfg=load_empresa_config()
    with st.expander('🏢 Configuración empresa / logo nóminas', expanded=False):
        st.markdown("<div class='company-card'>", unsafe_allow_html=True)
        c=st.columns([1.3,1,1,.7])
        nombre=c[0].text_input('Nombre empresa', value=cfg['Nombre'], key='emp_nombre')
        fondo=c[1].color_picker('Color fondo', value=cfg['ColorFondo'], key='emp_fondo')
        texto=c[2].color_picker('Color texto', value=cfg['ColorTexto'], key='emp_texto')
        pagas=c[3].selectbox('Pagas', [12,14], index=0 if cfg['Pagas']==12 else 1, key='emp_pagas')
        st.caption('Recomendaciones logo: PNG o SVG · fondo transparente recomendado · formato horizontal · mínimo 300×100 px · máximo 1 MB. El logo se guarda también codificado para que no se pierda al refrescar.')
        up=st.file_uploader('Subir nuevo logo de empresa', type=['png','svg'], key='emp_logo_upload')
        logo_file=cfg.get('LogoArchivo','')
        logo_b64=cfg.get('LogoBase64','')
        logo_ext=cfg.get('LogoExt','png')

        # El uploader de Streamlit puede vaciarse tras un rerun. Guardamos el logo pendiente
        # en session_state hasta que pulses Guardar configuración empresa.
        pending = st.session_state.get('empresa_logo_pending')
        if isinstance(pending, dict) and pending.get('LogoBase64'):
            logo_file = pending.get('LogoArchivo', logo_file)
            logo_b64 = pending.get('LogoBase64', logo_b64)
            logo_ext = pending.get('LogoExt', logo_ext)

        if up is not None:
            suffix=Path(up.name).suffix.lower() or '.png'
            logo_file='empresa_logo'+suffix
            data=up.getvalue()
            logo_b64=base64.b64encode(data).decode()
            logo_ext=suffix.replace('.','') or 'png'
            st.session_state['empresa_logo_pending']={'LogoArchivo':logo_file,'LogoBase64':logo_b64,'LogoExt':logo_ext}
            try:
                Path(logo_file).write_bytes(data)
                Path('empresa_logo_base64.txt').write_text(logo_b64, encoding='utf-8')
            except Exception:
                pass
            # Guardado inmediato para que el logo esté disponible en otros dispositivos sin esperar otro clic.
            try:
                save_empresa_config({'Nombre':nombre,'ColorFondo':fondo,'ColorTexto':texto,'LogoArchivo':logo_file,'Pagas':pagas,'LogoBase64':logo_b64,'LogoExt':logo_ext})
            except Exception:
                pass
        preview_cfg={'LogoBase64':logo_b64,'LogoExt':logo_ext,'LogoArchivo':logo_file}
        preview_src=empresa_logo_src(preview_cfg)
        if preview_src:
            st.markdown(f"<div class='company-preview' style='background:{fondo};color:{texto}'><img src='{preview_src}'></div>", unsafe_allow_html=True)
        if st.button('💾 Guardar configuración empresa', use_container_width=True, key='emp_save'):
            cfg_to_save={'Nombre':nombre,'ColorFondo':fondo,'ColorTexto':texto,'LogoArchivo':logo_file,'Pagas':pagas,'LogoBase64':logo_b64,'LogoExt':logo_ext}
            save_empresa_config(cfg_to_save)
            st.session_state.pop('empresa_logo_pending', None)
            st.success('Configuración de empresa guardada')
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# payroll/vacations/interests/irpf
def render_nominas():
    st.header('💼 Nóminas')
    render_empresa_box()

    df=load_nominas()
    years=list(range(date.today().year-2,date.today().year+9))
    year=st.selectbox('Año', years, index=years.index(date.today().year) if date.today().year in years else 2, key='nom_year')

    vac_year = load_vacaciones()
    try:
        vac_year = vac_year[pd.to_numeric(vac_year['Anio'], errors='coerce').fillna(0).astype(int)==year]
    except Exception:
        vac_year = pd.DataFrame()
    used = int(pd.to_numeric(vac_year.get('Dias', pd.Series(dtype=float)), errors='coerce').fillna(0).sum()) if not vac_year.empty else 0
    remaining = VACACIONES_ANUALES - used
    prog = min(100, max(0, used / VACACIONES_ANUALES * 100)) if VACACIONES_ANUALES else 0
    st.markdown(f"<div class='account-total'><b>🌴 Vacaciones {year}</b><br>Consumidas: <b>{used}</b> · Restantes: <b>{remaining}</b> · Disponibles: <b>{VACACIONES_ANUALES}</b><div style='height:10px;border-radius:999px;background:rgba(128,128,128,.22);margin-top:.55rem;overflow:hidden'><div style='height:100%;width:{prog:.1f}%;background:#00a2eb'></div></div></div>", unsafe_allow_html=True)

    with st.expander('⚙️ Generar 12 nóminas del año', expanded=True):
        st.caption('Rellena una plantilla mensual una vez y crea ENE-DIC. Después, cada mes solo introduces lo ingresado y la app comprueba si coincide.')
        c=st.columns(5)
        bruto_base=c[0].number_input('Bruto mensual', value=2166.67, step=.01, format='%.2f', key=f'nom_tpl_bruto_{year}')
        ss_pct=c[1].number_input('% SS', value=4.85, step=.01, format='%.2f', key=f'nom_tpl_ss_{year}')
        desempleo_pct=c[2].number_input('% Desempleo', value=1.65, step=.01, format='%.2f', key=f'nom_tpl_des_{year}')
        irpf_pct=c[3].number_input('% IRPF', value=0.00, step=.01, format='%.2f', key=f'nom_tpl_irpf_{year}')
        otros_base=c[4].number_input('Otros descuentos', value=0.00, step=.01, format='%.2f', key=f'nom_tpl_otros_{year}')
        ss_base=bruto_base*ss_pct/100
        des_base=bruto_base*desempleo_pct/100
        irpf_base=bruto_base*irpf_pct/100
        neto_base=bruto_base-ss_base-des_base-irpf_base-otros_base
        st.info(f'Plantilla mensual: SS {euro(ss_base)} · Desempleo {euro(des_base)} · IRPF {euro(irpf_base)} · Neto esperado {euro(neto_base)}')
        c1,c2=st.columns(2)
        if c1.button('🧾 Generar / actualizar ENE-DIC', use_container_width=True, key=f'nom_generate_{year}'):
            existing=df[df['Anio']==year].copy()
            rows=[]
            for mes in MONTHS_ES:
                ex=existing[existing['Mes']==mes]
                ingresado=float(money(ex.iloc[0]['Ingresado'])) if not ex.empty else 0.0
                # Si ya existía una nómina, mantenemos el ingresado; el resto se actualiza con la plantilla.
                rows.append({'Anio':year,'Mes':mes,'Bruto':bruto_base,'SS':ss_base,'Desempleo':des_base,'IRPF':irpf_base,'Otros':otros_base,'Ingresado':ingresado})
            base=df[df['Anio']!=year].copy()
            save_nominas(pd.concat([base,pd.DataFrame(rows)], ignore_index=True))
            st.success('12 nóminas generadas. Ahora solo rellena el importe ingresado cada mes.')
            st.rerun()
        if c2.button('🗑️ Borrar nóminas del año', use_container_width=True, key=f'nom_delete_year_{year}'):
            save_nominas(df[df['Anio']!=year].copy())
            st.warning('Nóminas del año borradas.')
            st.rerun()
        with st.expander('Opciones avanzadas de pagas', expanded=False):
            st.caption('Preparado por si algún año pasas a 14 pagas. Genera dos filas extra editables: verano y Navidad.')
            if st.button('Cambiar a 14 pagas / añadir extras', key=f'nom_14_{year}'):
                cur=load_nominas()
                base=cur[cur['Anio']!=year].copy()
                y=cur[cur['Anio']==year].copy()
                if y.empty:
                    rows=[]
                    for mes in MONTHS_ES:
                        rows.append({'Anio':year,'Mes':mes,'Bruto':bruto_base,'SS':ss_base,'Desempleo':des_base,'IRPF':irpf_base,'Otros':otros_base,'Ingresado':0.0})
                    y=pd.DataFrame(rows)
                # extras editables; por defecto sin SS/desempleo, pero con IRPF según porcentaje.
                extras=pd.DataFrame([
                    {'Anio':year,'Mes':'EXTRA VERANO','Bruto':bruto_base,'SS':0.0,'Desempleo':0.0,'IRPF':irpf_base,'Otros':0.0,'Ingresado':0.0},
                    {'Anio':year,'Mes':'EXTRA NAVIDAD','Bruto':bruto_base,'SS':0.0,'Desempleo':0.0,'IRPF':irpf_base,'Otros':0.0,'Ingresado':0.0},
                ])
                y=y[~y['Mes'].isin(['EXTRA VERANO','EXTRA NAVIDAD','EXTRA JUL','EXTRA DIC','PAGA VERANO','PAGA NAVIDAD'])]
                save_nominas(pd.concat([base,y,extras], ignore_index=True))
                st.success('Añadidas pagas extra de verano y Navidad. Puedes editar todos los importes.')
                st.rerun()

    ydf=ordered_nominas(load_nominas())
    ydf=ydf[ydf['Anio']==year].copy()
    if ydf.empty:
        st.info('Aún no hay nóminas para este año. Genera las 12 desde la plantilla anterior.')
    else:
        total_cols=st.columns(4)
        total_cols[0].metric('Bruto anual', euro(ydf['Bruto'].sum()))
        total_cols[1].metric('Gastos deducibles', euro(ydf['SS'].sum()+ydf['Desempleo'].sum()))
        total_cols[2].metric('Retenciones IRPF', euro(ydf['IRPF'].sum()))
        total_cols[3].metric('Neto esperado anual', euro(ydf['NetoCalculado'].sum()))

        st.subheader('Comprobación de nóminas')
        view=ydf.copy()
        view['Estado']=view['Diferencia'].apply(nomina_status)
        ordered_cols=['Mes','Bruto','SS','Desempleo','IRPF','Otros','NetoCalculado','Ingresado','Diferencia','Estado']
        view=view[ordered_cols]
        st.markdown('<div class="desktop-payroll">'+payroll_html(view)+'</div>'+payroll_mobile_html(view), unsafe_allow_html=True)

        with st.expander('✏️ Editar nóminas / introducir ingresado', expanded=True):
            st.caption('La columna 💙 Ingresado es la que normalmente rellenarás cada mes. El resto queda editable por si una nómina cambia.')
            edit=ydf[['Mes','Bruto','SS','Desempleo','IRPF','Otros','Ingresado']].copy().reset_index(drop=True)
            edit=edit.rename(columns={'Ingresado':'💙 Ingresado'})
            st.markdown('<div class="compact-editor">', unsafe_allow_html=True)
            edited=st.data_editor(
                edit,
                hide_index=True,
                use_container_width=True,
                num_rows='fixed',
                height=620,
                key=f'nom_editor_{year}',
                column_config={
                    'Mes': st.column_config.TextColumn('Mes', disabled=True, width='small'),
                    'Bruto': st.column_config.NumberColumn('Bruto', format='%.2f', width='small'),
                    'SS': st.column_config.NumberColumn('SS', format='%.2f', width='small'),
                    'Desempleo': st.column_config.NumberColumn('Desempleo', format='%.2f', width='small'),
                    'IRPF': st.column_config.NumberColumn('IRPF', format='%.2f', width='small'),
                    'Otros': st.column_config.NumberColumn('Otros', format='%.2f', width='small'),
                    '💙 Ingresado': st.column_config.NumberColumn('💙 Ingresado', format='%.2f', width='small', help='Importe real que te han ingresado en banco'),
                }
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button('💾 Guardar cambios de nóminas', use_container_width=True, key=f'nom_save_editor_{year}'):
                edited=edited.rename(columns={'💙 Ingresado':'Ingresado'})
                edited['Anio']=year
                for col in ['Bruto','SS','Desempleo','IRPF','Otros','Ingresado']:
                    edited[col]=edited[col].apply(money)
                base=df[df['Anio']!=year].copy()
                save_nominas(pd.concat([base,edited[['Anio','Mes','Bruto','SS','Desempleo','IRPF','Otros','Ingresado']]], ignore_index=True))
                st.success('Nóminas actualizadas.')
                st.rerun()

    render_vacaciones(year)
    render_empresa_config()

def easter(y):
    a=y%19; b=y//100; c=y%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31; da=((h+l-7*m+114)%31)+1; return date(y,mo,da)

def base_festivos(y):
    e=easter(y); fixes=[(1,1,'Año Nuevo'),(1,6,'Reyes'),(4,28,'San Prudencio'),(5,1,'Día Trabajo'),(7,25,'Santiago'),(8,5,'Virgen Blanca'),(8,15,'Asunción'),(10,12,'Fiesta Nacional'),(11,1,'Todos Santos'),(12,6,'Constitución'),(12,8,'Inmaculada'),(12,25,'Navidad')]
    rows=[{'Anio':y,'Fecha':date(y,m,d).isoformat(),'Nombre':n,'Activo':True} for m,d,n in fixes]
    rows += [{'Anio':y,'Fecha':(e-timedelta(days=2)).isoformat(),'Nombre':'Viernes Santo','Activo':True},{'Anio':y,'Fecha':(e+timedelta(days=1)).isoformat(),'Nombre':'Lunes Pascua','Activo':True}]
    return pd.DataFrame(rows)

def load_festivos(y):
    df=read_csv('festivos.csv', ['Anio','Fecha','Nombre','Activo'])
    if df.empty or df[df['Anio']==y].empty:
        df=pd.concat([df,base_festivos(y)], ignore_index=True); save_csv('festivos.csv', df)
    df=read_csv('festivos.csv', ['Anio','Fecha','Nombre','Activo'])
    df['Anio']=pd.to_numeric(df['Anio'], errors='coerce').fillna(y).astype(int); df['Activo']=df['Activo'].astype(str).str.lower().isin(['true','1','si','sí'])
    return df[df['Anio']==y].copy()

def laboral_days_between(a, b, year):
    """Días computables de vacaciones: lunes-viernes, excluyendo festivos activos."""
    fest=set(pd.to_datetime(load_festivos(year).query('Activo == True')['Fecha'], errors='coerce').dt.date)
    if b < a:
        return 0
    total=0
    for i in range((b-a).days+1):
        d=a+timedelta(days=i)
        if d.weekday()<5 and d not in fest:
            total += 1
    return total

def calendar_month_html(y, m, vac_days=set(), fest=None):
    fest = fest or set(pd.to_datetime(load_festivos(y).query('Activo == True')['Fecha'], errors='coerce').dt.date)
    first=date(y,m,1); start=first-timedelta(days=first.weekday()); days=[start+timedelta(days=i) for i in range(42)]
    html=f"<div class='cal-month-title'>{MONTHS_ES[m-1]}{str(y)[-2:]}</div>"
    html += "<div class='cal-grid'>" + ''.join(f"<div class='cal-head'>{d}</div>" for d in ['L','M','X','J','V','S','D'])
    for d in days:
        cls='cal-empty' if d.month!=m else 'cal-normal'
        if d.month==m:
            if d in vac_days: cls='cal-green'
            elif d in fest: cls='cal-maroon'
            elif d.weekday()>=5: cls='cal-red'
            elif d.weekday()==4 or (d+timedelta(days=1)) in fest or date(y,6,1)<=d<=date(y,9,30): cls='cal-grey'
        html+=f"<div class='cal-day {cls}'>{d.day}</div>"
    html+='</div>'
    return html

def render_calendar(y, vac_days=set()):
    fest=set(pd.to_datetime(load_festivos(y).query('Activo == True')['Fecha'], errors='coerce').dt.date)
    st.markdown('**Calendario anual**')
    rows=[st.columns(3), st.columns(3), st.columns(3), st.columns(3)]
    m=1
    for row in rows:
        for col in row:
            with col:
                st.markdown(calendar_month_html(y, m, vac_days, fest), unsafe_allow_html=True)
                m += 1

def render_vacaciones(year):
    st.subheader('🌴 Vacaciones y calendario laboral')
    vac=load_vacaciones()
    if not vac.empty:
        vac['Anio']=pd.to_numeric(vac['Anio'], errors='coerce').fillna(year).astype(int)
        vac['Inicio']=pd.to_datetime(vac['Inicio'], errors='coerce').dt.date
        vac['Fin']=pd.to_datetime(vac['Fin'], errors='coerce').dt.date
        vac=vac.dropna(subset=['Inicio','Fin'])
    yvac=vac[vac['Anio']==year].sort_values('Inicio') if not vac.empty else pd.DataFrame(columns=['Anio','Inicio','Fin','Dias','Nota'])
    used=money(yvac['Dias'].sum()) if not yvac.empty else 0
    st.metric('Días restantes', f"{VACACIONES_ANUALES-used:g}", delta=f"Usados: {used:g}")

    with st.expander('➕ Añadir vacaciones', expanded=False):
        ini=st.date_input('Inicio', value=date(year, date.today().month, 1), min_value=date(year,1,1), max_value=date(year,12,31), format='DD/MM/YYYY', key=f'vac_ini_{year}')
        fin=st.date_input('Fin', value=ini, min_value=ini, max_value=date(year,12,31), format='DD/MM/YYYY', key=f'vac_fin_{year}_{ini.isoformat()}')
        calc=laboral_days_between(ini, fin, year)
        dias=st.number_input('Días computables', value=float(calc), step=.5, format='%.1f', help='Calculado automáticamente solo con laborables: excluye sábados, domingos y festivos. Puedes editarlo si hace falta.', key=f'vac_dias_{year}_{ini.isoformat()}_{fin.isoformat()}')
        nota=st.text_input('Nota', key=f'vac_nota_{year}_{ini.isoformat()}')
        if st.button('Guardar vacaciones', use_container_width=True, key=f'vac_save_{year}'):
            row={'Anio':year,'Inicio':ini.isoformat(),'Fin':fin.isoformat(),'Dias':dias,'Nota':nota}
            save_vacaciones(pd.concat([vac,pd.DataFrame([row])], ignore_index=True))
            st.rerun()

    vac_days=set()
    for _,r in yvac.iterrows():
        a=pd.to_datetime(r['Inicio']).date(); b=pd.to_datetime(r['Fin']).date()
        vac_days |= {a+timedelta(days=i) for i in range((b-a).days+1)}
    render_calendar(year, vac_days)

    st.markdown('**Periodos de vacaciones**')
    if yvac.empty:
        st.info('Aún no hay vacaciones registradas para este año.')
    else:
        disp=yvac.copy().sort_values('Inicio')
        disp['Inicio']=disp['Inicio'].apply(date_label)
        disp['Fin']=disp['Fin'].apply(date_label)
        disp=disp[['Inicio','Fin','Dias','Nota']]
        st.dataframe(disp, hide_index=True, use_container_width=True)
        with st.expander('✏️ Editar / borrar vacaciones existentes', expanded=False):
            for i,r in yvac.reset_index(drop=True).iterrows():
                title=f"{date_label(r['Inicio'])} → {date_label(r['Fin'])} · {money(r['Dias']):g} días"
                with st.container():
                    st.markdown(f"**{title}**")
                    c=st.columns([1.15,1.15,.8,1.8,.55,.55])
                    ini2=c[0].date_input('Inicio', value=pd.to_datetime(r['Inicio']).date(), min_value=date(year,1,1), max_value=date(year,12,31), format='DD/MM/YYYY', key=f'vac_edit_ini_{year}_{i}', label_visibility='collapsed')
                    fin2=c[1].date_input('Fin', value=max(pd.to_datetime(r['Fin']).date(), ini2), min_value=ini2, max_value=date(year,12,31), format='DD/MM/YYYY', key=f'vac_edit_fin_{year}_{i}_{ini2.isoformat()}', label_visibility='collapsed')
                    calc2=laboral_days_between(ini2, fin2, year)
                    dias2=c[2].number_input('Días', value=float(money(r['Dias']) if money(r['Dias']) else calc2), step=.5, format='%.1f', key=f'vac_edit_dias_{year}_{i}', label_visibility='collapsed')
                    nota2=c[3].text_input('Nota', value='' if pd.isna(r.get('Nota','')) else str(r.get('Nota','')), key=f'vac_edit_nota_{year}_{i}', label_visibility='collapsed')
                    if c[4].button('💾', key=f'vac_update_{year}_{i}', help='Guardar cambios'):
                        allv=vac.copy().reset_index(drop=True)
                        mask=(allv['Anio'].astype(int)==year)&(pd.to_datetime(allv['Inicio']).dt.date==pd.to_datetime(r['Inicio']).date())&(pd.to_datetime(allv['Fin']).dt.date==pd.to_datetime(r['Fin']).date())&(allv['Nota'].fillna('').astype(str)==str(r.get('Nota','')))
                        idxs=allv[mask].index.tolist() or [yvac.index[i]]
                        idx=idxs[0]
                        allv.loc[idx, ['Anio','Inicio','Fin','Dias','Nota']] = [year, ini2.isoformat(), fin2.isoformat(), dias2, nota2]
                        save_vacaciones(allv)
                        st.rerun()
                    if c[5].button('❌', key=f'vac_delete_{year}_{i}', help='Borrar periodo'):
                        allv=vac.copy().reset_index(drop=True)
                        mask=(allv['Anio'].astype(int)==year)&(pd.to_datetime(allv['Inicio']).dt.date==pd.to_datetime(r['Inicio']).date())&(pd.to_datetime(allv['Fin']).dt.date==pd.to_datetime(r['Fin']).date())&(allv['Nota'].fillna('').astype(str)==str(r.get('Nota','')))
                        idxs=allv[mask].index.tolist() or [yvac.index[i]]
                        allv=allv.drop(index=idxs[0])
                        save_vacaciones(allv)
                        st.rerun()
                    st.divider()

    with st.expander('Editar festivos', expanded=False):
        f=load_festivos(year).reset_index(drop=True)
        if not f.empty:
            f['Fecha']=pd.to_datetime(f['Fecha'], errors='coerce').dt.date
        edited=st.data_editor(f, num_rows='dynamic', hide_index=True, use_container_width=True, key=f'fest_{year}')
        if st.button('Guardar festivos', use_container_width=True, key=f'fest_save_{year}'):
            allf=read_csv('festivos.csv', ['Anio','Fecha','Nombre','Activo']); allf=allf[pd.to_numeric(allf['Anio'], errors='coerce')!=year]
            save_csv('festivos.csv', pd.concat([allf,edited], ignore_index=True)); st.rerun()

def render_intereses():
    st.header('🏦 Intereses')
    render_bank_config('intereses_banks')
    df=load_intereses()
    year=st.selectbox('Año', list(range(date.today().year-2,date.today().year+9)), index=2, key='int_year')
    ydf=load_intereses(); ydf=ydf[ydf['Anio']==year].copy()

    if not ydf.empty:
        c=st.columns(3)
        c[0].metric('Interés bruto anual', euro(ydf['InteresBruto'].sum()))
        c[1].metric('Retención anual', euro(ydf['Retencion'].sum()))
        c[2].metric('Neto anual', euro(ydf['NetoEsperado'].sum()))

    with st.expander('➕ Añadir / actualizar interés', expanded=True):
        top=st.columns([1,1])
        mes=top[0].selectbox('Mes', MONTHS_ES, index=date.today().month-1, key='int_mes')
        banco=top[1].selectbox('Banco', bank_keys(True), format_func=bank_name, key='int_banco')
        ex=df[(df['Anio']==year)&(df['Mes']==mes)&(df['Banco']==banco)]
        d=ex.iloc[0].to_dict() if not ex.empty else {}
        clear_key = st.session_state.get('int_clear_key')
        current_key = f'{year}_{mes}_{banco}'
        default_bruto = 0.0 if clear_key == current_key else float(money(d.get('InteresBruto',0)))
        default_ing = 0.0 if clear_key == current_key else float(money(d.get('Ingresado',0)))
        if clear_key == current_key:
            st.session_state.pop('int_clear_key', None)
        c=st.columns([1,1,.9])
        form_ver = st.session_state.get('int_form_ver', 0)
        bruto_txt=c[0].text_input('Interés bruto', value=euro_input_text(default_bruto), key=f'int_bruto_txt_{year}_{mes}_{banco}_{form_ver}', help='Puedes usar coma decimal: 308,21')
        bruto=money(bruto_txt)
        ret=bruto*0.19
        neto=bruto-ret
        ingresado_txt=c[1].text_input('Ingresado', value=euro_input_text(default_ing), key=f'int_ingresado_txt_{year}_{mes}_{banco}_{form_ver}', help='Puedes usar coma decimal: 249,65')
        ingresado=money(ingresado_txt)
        c[2].markdown(f"<div class='interest-summary'><div class='is-row'><b>Retención 19%</b><span>{euro(ret)}</span></div><div class='is-row'><b>Neto esperado</b><span>{euro(neto)}</span></div></div>", unsafe_allow_html=True)
        st.info(f'El bruto irá a Rendimiento neto capital mobiliario y la retención a Retenciones capital mobiliario en IRPF. Diferencia con ingreso: {euro(ingresado-neto)}')
        if st.button('Guardar interés', use_container_width=True, key=f'int_save_{year}_{mes}_{banco}'):
            row={'Anio':year,'Mes':mes,'Banco':banco,'InteresBruto':bruto,'Saldo':0.0,'Ingresado':ingresado}
            base=df[~((df['Anio']==year)&(df['Mes']==mes)&(df['Banco']==banco))].copy()
            save_intereses(pd.concat([base,pd.DataFrame([row])], ignore_index=True))
            st.session_state['int_clear_key'] = f'{year}_{mes}_{banco}'
            st.session_state['int_form_ver'] = st.session_state.get('int_form_ver', 0) + 1
            st.success('Interés guardado')
            st.rerun()

    ydf=load_intereses(); ydf=ydf[ydf['Anio']==year].copy()
    if not ydf.empty:
        order={m:i for i,m in enumerate(MONTHS_ES)}
        ydf['_o']=ydf['Mes'].map(order).fillna(99); ydf=ydf.sort_values(['_o','Banco']).drop(columns=['_o'])
        st.subheader('Tabla de intereses')
        html_tbl="<table class='irpf-table'><tr><th>Mes</th><th>Banco</th><th>Interés bruto</th><th>Retención 19%</th><th>Neto esperado</th><th>Ingresado</th><th>Diferencia</th></tr>"
        for _,r in ydf.iterrows():
            k=str(r.get('Banco',''))
            btxt=bank_text_color(k)
            bicon_white=True if is_dark_color(bank_color(k)) else False
            bcell=f"<span class='bank-name-cell' style='color:{btxt}'>{bank_icon_html(k, white=bicon_white, size=20)}{html.escape(bank_name(k))}</span>"
            diff=money(r.get('Diferencia',0)); dcol='#22c55e' if diff>=0 else '#ef4444'
            html_tbl += f"<tr><td>{html.escape(str(r.get('Mes','')))}</td><td>{bcell}</td><td class='irpf-num'>{euro(r.get('InteresBruto',0))}</td><td class='irpf-num'>{euro(r.get('Retencion',0))}</td><td class='irpf-num'>{euro(r.get('NetoEsperado',0))}</td><td class='irpf-num'>{euro(r.get('Ingresado',0))}</td><td class='irpf-num' style='color:{dcol};font-weight:900'>{euro(diff)}</td></tr>"
        html_tbl += "</table>"
        st.markdown(html_tbl, unsafe_allow_html=True)

        with st.expander('✏️ Editar / borrar intereses', expanded=False):
            edit=ydf[['Mes','Banco','InteresBruto','Ingresado']].copy().reset_index(drop=True)
            edited=st.data_editor(edit, hide_index=True, use_container_width=True, num_rows='fixed', key=f'int_edit_{year}', column_config={
                'Mes': st.column_config.SelectboxColumn('Mes', options=MONTHS_ES, width='small'),
                'Banco': st.column_config.SelectboxColumn('Banco', options=bank_keys(True), width='medium'),
                'InteresBruto': st.column_config.NumberColumn('Interés bruto', format='%.2f'),
                'Ingresado': st.column_config.NumberColumn('Ingresado', format='%.2f'),
            })
            c1,c2=st.columns(2)
            if c1.button('💾 Guardar cambios de intereses', use_container_width=True, key=f'int_edit_save_{year}'):
                base=df[df['Anio']!=year].copy()
                edited['Anio']=year
                edited['Saldo']=0.0
                save_intereses(pd.concat([base, edited], ignore_index=True))
                st.success('Intereses guardados')
                st.rerun()
            labels=(ydf['Mes']+' · '+ydf['Banco']).tolist()
            sel=st.selectbox('Borrar registro', ['']+labels, key=f'int_del_sel_{year}')
            if sel and c2.button('❌ Borrar interés seleccionado', use_container_width=True, key=f'int_del_btn_{year}'):
                idx=labels.index(sel); todel=ydf.iloc[idx]
                save_intereses(df[~((df['Anio']==todel.Anio)&(df['Mes']==todel.Mes)&(df['Banco']==todel.Banco))])
                st.rerun()

def cuota_general(base):
    tr=[(0,18080,.23),(18080,36160,.28),(36160,54240,.35),(54240,77450,.40),(77450,107260,.45),(107260,142960,.46),(142960,208390,.47)]
    tax=0
    for lo,hi,rate in tr:
        if base>lo: tax += (min(base,hi)-lo)*rate
    if base>208390: tax += (base-208390)*.49
    return tax

def cuota_ahorro(base):
    if base<=2500: return base*.20
    if base<=10000: return 500+(base-2500)*.21
    if base<=15000: return 2075+(base-10000)*.22
    if base<=30000: return 3175+(base-15000)*.23
    return 6625+(base-30000)*.25

def bonificacion(ri, gd):
    base=max(0,ri-gd)
    if base<=14800: return 8000
    if base<=23000: return max(3000,8000-0.6098*(base-14800))
    return 3000

def render_irpf():
    st.header('📄 IRPF')
    year=st.selectbox('Año IRPF', list(range(date.today().year-2,date.today().year+9)), index=2, key='irpf_year')
    nom=load_nominas(); nom=nom[nom['Anio']==year]
    intr=load_intereses(); intr=intr[intr['Anio']==year]
    ri=nom['Bruto'].sum(); gd=(nom['SS'].sum()+nom['Desempleo'].sum()); bon=bonificacion(ri, gd)
    rnet=max(0,ri-gd-bon); cap=intr['InteresBruto'].sum(); res_gen=cuota_general(rnet); minoracion=1583.0; cuota_gen=max(0,res_gen-minoracion); cuota_aho=cuota_ahorro(cap); total=cuota_gen+cuota_aho
    ret_trab=nom['IRPF'].sum(); ret_cap=intr['Retencion'].sum(); pagos=ret_trab+ret_cap; diferencial=total-pagos
    vals={
        'Rendimientos íntegros':ri,'Gastos deducibles':gd,'Bonificación':bon,'Rendimiento neto trabajo':rnet,'Base imponible general':rnet,
        'Rendimiento neto capital mobiliario':cap,'Base liquidable ahorro':cap,'Resultado escala general':res_gen,'Minoración':minoracion,'Cuota íntegra general':cuota_gen,'Cuota íntegra ahorro':cuota_aho,'Cuota líquida':total,
        'Retenciones trabajo':ret_trab,'Retenciones capital mobiliario':ret_cap,'Total pagos a cuenta':pagos,'Cuota diferencial':diferencial
    }
    manual=dict(vals)
    with st.expander('✏️ Introducción / ajuste manual de datos IRPF', expanded=False):
        st.caption('Valores automáticos desde Nóminas e Intereses. Puedes ajustar manualmente aquí para simular o corregir.')
        cols=st.columns(2)
        names=list(vals.keys())
        for i,name in enumerate(names):
            manual[name]=(cols[i%2].number_input(name, value=float(vals[name]), step=.01, format='%.2f', key=f'irpf_{year}_{safe_key(name)}'))
    diferencial=manual['Cuota líquida']-manual['Total pagos a cuenta']
    left=['Rendimientos íntegros','Gastos deducibles','Bonificación','Rendimiento neto trabajo','Base imponible general','Rendimiento neto capital mobiliario','Base liquidable ahorro']
    right=['Resultado escala general','Minoración','Cuota íntegra general','Cuota íntegra ahorro','Cuota líquida','Retenciones trabajo','Retenciones capital mobiliario','Total pagos a cuenta']
    cls='irpf-result-ok' if diferencial<0 else 'irpf-result-bad'
    label='A DEVOLVER' if diferencial<0 else 'A PAGAR'
    html="<div class='irpf-desktop'><table class='irpf-table'><tr><th colspan='2'>RENTA {}</th><th colspan='2'>CUOTA / PAGOS</th></tr>".format(year)
    for i in range(max(len(left),len(right))):
        l=left[i] if i<len(left) else ''; r=right[i] if i<len(right) else ''
        html+=f"<tr><td>{l}</td><td class='irpf-num'>{euro(manual.get(l,0)) if l else ''}</td><td>{r}</td><td class='irpf-num'>{euro(manual.get(r,0)) if r else ''}</td></tr>"
    html+=f"<tr><td colspan='3'><b>CUOTA DIFERENCIAL</b></td><td class='irpf-num'><b>{euro(diferencial)}</b></td></tr><tr><td colspan='3' class='{cls}'>{label}</td><td class='{cls} irpf-num'>{euro(abs(diferencial))}</td></tr></table></div>"
    mobile=f"<div class='irpf-mobile'><div class='irpf-block'><div class='irpf-block-title'>RENTA {year}</div>"
    for l in left:
        mobile+=f"<div class='irpf-row'><div>{l}</div><div class='num'>{euro(manual.get(l,0))}</div></div>"
    mobile += "</div><div class='irpf-block'><div class='irpf-block-title'>CUOTA / PAGOS</div>"
    for r in right:
        mobile+=f"<div class='irpf-row'><div>{r}</div><div class='num'>{euro(manual.get(r,0))}</div></div>"
    mobile+=f"</div><div class='irpf-final {cls}'>{label}: {euro(abs(diferencial))}</div></div>"
    st.markdown(html+mobile, unsafe_allow_html=True)

login_gate(); header()
tabs=st.tabs(['📊 Dashboard','🐷 Ahorro','👤 Nóminas','％ Intereses','📋 IRPF','☁️ Backup'])
with tabs[0]: render_dashboard()
with tabs[1]: render_ahorro()
with tabs[2]: render_nominas()
with tabs[3]: render_intereses()
with tabs[4]: render_irpf()
with tabs[5]: render_backup()
footer()
