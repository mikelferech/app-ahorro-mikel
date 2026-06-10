import base64
import calendar
import io
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "Ahorro Mikel"
APP_VERSION = "0.5.7"
APP_UPDATED = "10/06/2026"
DATA = Path(".")
ASSETS = Path(".")
MFE_LOGO = Path("mfe_cabecera.png")
VADILLO_LOGO = Path("vadillo.svg")
MONTHS_ES = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
VACACIONES_ANUALES = 23

st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.main .block-container {padding-top: 1.2rem; max-width: 1800px; font-size: 1.08rem;}
h1 {font-size: 3.0rem !important;}
h2 {font-size: 2.25rem !important;} h3 {font-size: 1.85rem !important;}
[data-testid="stMetricLabel"] {font-size: 1.12rem !important; font-weight: 800 !important;}
[data-testid="stMetricValue"] {font-size: 2.65rem !important;}
[data-testid="stMetricDelta"] {font-size: 1.05rem !important;}
.stTabs [data-baseweb="tab"] p {font-size: 1.12rem !important; font-weight: 800 !important;}
.stDataFrame, [data-testid="stDataFrame"] {font-size: 1.08rem !important;}
[data-testid="stDataFrame"] [role="columnheader"], [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {background:#263244!important;color:#fff!important;font-weight:900!important;}
[data-testid="stDataFrame"] div[role="columnheader"] {background:#263244!important;color:#fff!important;}
thead tr th {background:#263244!important;color:#fff!important;}
[data-testid="stDataFrame"] [role="gridcell"] {font-size:1.02rem!important;}
.login-card {max-width:560px;margin:5rem auto 1rem auto;padding:1.8rem;border:1px solid rgba(128,128,128,.25);border-radius:24px;background:rgba(128,128,128,.06);text-align:center;}
.login-card img {max-width:330px;width:85%;margin-bottom:1rem;}
.header-row{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:1rem;}
.brand{display:flex;align-items:center;gap:22px;}
.brand img{height:64px;max-width:285px;object-fit:contain;}
.brand h1{font-size:3.75rem!important;margin:0;line-height:1;}
.userbox{text-align:right;min-width:150px;}
.logout-inline{display:flex;align-items:center;justify-content:flex-end;gap:10px;}
.logout-inline .user{font-weight:800;opacity:.85;}
.logout-icon button{font-size:1.25rem!important;padding:.25rem .58rem!important;min-height:34px!important;}
.bank-chip{border-radius:10px;padding:13px 14px;color:white;font-weight:900;text-align:center;margin-bottom:10px;font-size:1.15rem;}
.row-card{border-bottom:1px solid rgba(128,128,128,.15);padding:.35rem 0;}
.footer{margin-top:2rem;border-top:1px solid rgba(128,128,128,.22);padding:1rem 0 .2rem;display:flex;align-items:center;justify-content:center;gap:14px;opacity:.8;font-size:.86rem;}
.footer img{height:24px;width:auto;}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:18px;}
.cal-head{text-align:center;font-weight:900;opacity:.8;font-size:.78rem;}
.cal-month-title{text-align:center;font-weight:900;margin:.6rem 0 .3rem;font-size:1.12rem}.cal-day{min-height:38px;border-radius:7px;text-align:center;padding:6px;border:1px solid rgba(128,128,128,.18);font-size:.96rem;}
.cal-empty{opacity:.1}.cal-normal{background:rgba(128,128,128,.08)}.cal-red{background:#b91c1c;color:#fff}.cal-maroon{background:#5b1720;color:#fff}.cal-grey{background:#6b7280;color:#fff}.cal-green{background:#15803d;color:#fff;font-weight:900}
.vadillo-box{background:#fff;border-radius:16px;padding:12px;border:1px solid rgba(128,128,128,.2);display:flex;align-items:center;justify-content:center;margin-bottom:1rem;}
.vadillo-box img{max-height:78px;max-width:95%;object-fit:contain;}
@media (prefers-color-scheme: dark){.vadillo-box{background:#111827}.vadillo-box img{filter: grayscale(1) brightness(0) invert(1);}}
.irpf-table{width:100%;border-collapse:collapse;font-size:.92rem}.irpf-table th{background:#d4006f;color:white;padding:7px}.irpf-table td{padding:6px 8px;border:1px solid rgba(128,128,128,.22)}.irpf-sec{background:#5f5f5f;color:white;font-weight:800}.irpf-pink{background:#ffd0d0;color:#111}.irpf-result-ok{background:#00c800!important;color:white!important;font-weight:900}.irpf-result-bad{background:#dc2626!important;color:white!important;font-weight:900}.irpf-num{text-align:right;font-variant-numeric:tabular-nums}.muted{opacity:.7}
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

def rerun(): st.rerun()

# ---------- csv storage ----------
def path(name): DATA.mkdir(exist_ok=True); return DATA/name

def read_csv(name, columns=None):
    p=path(name)
    if not p.exists(): return pd.DataFrame(columns=columns or [])
    df=pd.read_csv(p)
    if columns:
        for c in columns:
            if c not in df: df[c]=None
    return df

def save_csv(name, df):
    DATA.mkdir(exist_ok=True)
    df.to_csv(path(name), index=False)

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
    st.markdown(f"<div class='login-card'><img src='{img_src(MFE_LOGO)}'><h1>🔒 Ahorro Mikel</h1><p>Acceso privado</p></div>", unsafe_allow_html=True)
    if not u_ok or not p_ok:
        st.error('Faltan credenciales en Streamlit Secrets.'); st.code('[auth]\nusername = "mikelferech"\npassword = "TU_CONTRASEÑA"'); st.stop()
    with st.form('login_form'):
        u=st.text_input('Usuario')
        p=st.text_input('Contraseña', type='password')
        ok=st.form_submit_button('Entrar', use_container_width=True)
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
    df=read_csv('bancos.csv', ['Clave','Nombre','Color','Activo','Orden'])
    if df.empty:
        df=pd.DataFrame([
            {'Clave':'BBVA','Nombre':'BBVA','Color':'#072146','Activo':True,'Orden':1},
            {'Clave':'Openbank','Nombre':'Openbank','Color':'#e40046','Activo':True,'Orden':2},
            {'Clave':'Cajamar','Nombre':'Cajamar','Color':'#008c95','Activo':True,'Orden':3},
            {'Clave':'Otros','Nombre':'Otros','Color':'#6b7280','Activo':True,'Orden':4},
        ]); save_csv('bancos.csv', df)
    df['Clave']=df['Clave'].astype(str).apply(safe_key)
    df['Nombre']=df['Nombre'].fillna(df['Clave']).astype(str)
    df['Color']=df['Color'].fillna('#6b7280').astype(str)
    df['Activo']=df['Activo'].astype(str).str.lower().isin(['true','1','sí','si','yes'])
    df['Orden']=pd.to_numeric(df['Orden'], errors='coerce').fillna(99).astype(int)
    return df.drop_duplicates('Clave').sort_values('Orden')

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

def save_nominas(df): save_csv('nominas.csv', calc_nominas(df))

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
    <div class='header-row'><div class='brand'><img src='{img_src(MFE_LOGO)}'><h1>💰 Ahorro Mikel</h1></div><div></div></div>
    """, unsafe_allow_html=True)
    logout_button()

def footer():
    st.markdown(f"<div class='footer'><img src='{img_src(MFE_LOGO)}'><span><b>Ahorro Mikel v{APP_VERSION}</b></span><span>Actualizado: {APP_UPDATED}</span></div>", unsafe_allow_html=True)

def export_excel_bytes():
    bio=io.BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        load_ahorro().to_excel(writer, sheet_name='Ahorro', index=False)
        load_banks().to_excel(writer, sheet_name='Bancos', index=False)
        load_nominas().to_excel(writer, sheet_name='Nominas', index=False)
        load_intereses().to_excel(writer, sheet_name='Intereses', index=False)
        read_csv('vacaciones.csv').to_excel(writer, sheet_name='Vacaciones', index=False)
        read_csv('festivos.csv').to_excel(writer, sheet_name='Festivos', index=False)
    bio.seek(0); return bio.getvalue()

def render_bank_config(prefix='bank_config'):
    with st.expander('⚙️ Configuración de bancos', expanded=False):
        cfg=load_banks().reset_index(drop=True)
        st.caption('Edita nombres, colores, orden, activa/oculta o añade bancos. Los datos históricos no se pierden.')
        rows=[]
        for i,r in cfg.iterrows():
            c=st.columns([1.1,1.8,1.3,.8,.8,.55])
            clave=c[0].text_input('Clave', value=r['Clave'], key=f'{prefix}_clave_{i}', label_visibility='collapsed')
            nombre=c[1].text_input('Nombre', value=r['Nombre'], key=f'{prefix}_nombre_{i}', label_visibility='collapsed')
            color=c[2].color_picker('Color', value=str(r['Color']), key=f'{prefix}_color_{i}', label_visibility='collapsed')
            activo=c[3].checkbox('Activo', value=bool(r['Activo']), key=f'{prefix}_act_{i}', label_visibility='collapsed')
            orden=c[4].number_input('Orden', value=int(r['Orden']), step=1, key=f'{prefix}_orden_{i}', label_visibility='collapsed')
            borrar=c[5].button('❌', key=f'{prefix}_del_{i}', help='Eliminar banco')
            if not borrar:
                rows.append({'Clave':safe_key(clave),'Nombre':nombre or clave,'Color':color,'Activo':activo,'Orden':orden})
        st.divider()
        c=st.columns([1.1,1.8,1.3,.8,.8])
        n_clave=c[0].text_input('Nueva clave', key=f'{prefix}_new_clave')
        n_nombre=c[1].text_input('Nuevo nombre', key=f'{prefix}_new_nombre')
        n_color=c[2].color_picker('Nuevo color', value='#6b7280', key=f'{prefix}_new_color')
        n_act=c[3].checkbox('Mostrar', value=True, key=f'{prefix}_new_act')
        n_order=c[4].number_input('Orden nuevo', value=len(cfg)+1, step=1, key=f'{prefix}_new_order')
        if st.button('Guardar configuración de bancos', use_container_width=True, key=f'{prefix}_save'):
            if n_clave or n_nombre:
                rows.append({'Clave':safe_key(n_clave or n_nombre),'Nombre':n_nombre or n_clave,'Color':n_color,'Activo':n_act,'Orden':n_order})
            out=pd.DataFrame(rows).drop_duplicates('Clave', keep='last').sort_values('Orden')
            save_csv('bancos.csv', out)
            # add new bank cols to ahorro if needed
            a=load_ahorro()
            for k in out['Clave']:
                if k not in a: a[k]=0.0
            save_ahorro(a)
            st.success('Bancos guardados'); st.rerun()

def kpis(df):
    valid=df[df['Total']>0].sort_values('Fecha') if not df.empty else pd.DataFrame()
    if valid.empty:
        st.warning('Aún no hay datos válidos de ahorro.'); return
    last=valid.iloc[-1]; diff=last['Diferencia']; keys=bank_keys(True)
    cols=st.columns(4)
    cols[0].metric(f'Total actual · {month_label(last.Fecha)}', euro(last.Total))
    cols[1].metric('Último +/-', euro(diff), delta=euro(diff))
    if keys: cols[2].metric(bank_name(keys[0]), euro(last.get(keys[0],0)))
    if len(keys)>1: cols[3].metric(' + '.join(bank_name(k) for k in keys[1:3]), euro(sum(money(last.get(k,0)) for k in keys[1:3])))

def charts(df, prefix="chart"):
    if df.empty: return
    df=df.sort_values('Fecha').copy(); df['Mes']=df['Fecha'].apply(month_label)
    c1,c2=st.columns(2)
    fig=go.Figure(go.Scatter(x=df['Mes'], y=df['Total'], mode='lines+markers'))
    fig.update_layout(title='Patrimonio histórico', height=430, margin=dict(l=15,r=15,t=45,b=15))
    c1.plotly_chart(fig, use_container_width=True, key=f"{prefix}_patrimonio")
    colors=['#16a34a' if v>=0 else '#dc2626' for v in df['Diferencia']]
    fig2=go.Figure(go.Bar(x=df['Mes'], y=df['Diferencia'], marker_color=colors))
    fig2.update_layout(title='+/- mensual', height=430, margin=dict(l=15,r=15,t=45,b=15))
    c2.plotly_chart(fig2, use_container_width=True, key=f"{prefix}_diferencia")

def render_dashboard():
    st.header('📊 Dashboard')
    df=load_ahorro(); kpis(df); charts(df, "dashboard")
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
    for i,k in enumerate(keys): chips[i].markdown(f"<div class='bank-chip' style='background:{bank_color(k)}'>{bank_name(k)}</div>", unsafe_allow_html=True)
    table=df.sort_values('Fecha', ascending=False).copy(); table['Mes']=table['Fecha'].apply(month_label)
    show_cols=['Mes']+keys+['Total','Diferencia']
    show=table[show_cols].rename(columns={k:bank_name(k) for k in keys})
    for c in show.columns:
        if c!='Mes': show[c]=show[c].apply(euro)
    st.dataframe(show, hide_index=True, use_container_width=True)
    st.subheader('Editar / borrar saldo')
    labels=table['Mes'].tolist()
    sel_label=st.selectbox('Selecciona mes', labels, key='edit_ah_sel')
    row=table[table['Mes']==sel_label].iloc[0]
    cols=st.columns(max(1,len(keys)))
    new={'Fecha':row['Fecha']}
    for i,k in enumerate(keys): new[k]=cols[i].number_input(bank_name(k), value=float(money(row.get(k,0))), step=.01, format='%.2f', key=f'edit_ah_{k}_{sel_label}')
    c1,c2=st.columns(2)
    if c1.button('✏️ Guardar cambios', use_container_width=True):
        base=df[df['Fecha']!=row['Fecha']].copy(); save_ahorro(pd.concat([base,pd.DataFrame([new])], ignore_index=True)); st.success('Actualizado'); st.rerun()
    if c2.button('❌ Borrar mes', use_container_width=True):
        save_ahorro(df[df['Fecha']!=row['Fecha']].copy()); st.success('Borrado'); st.rerun()

# payroll/vacations/interests/irpf
def render_nominas():
    st.header('💼 Nóminas')
    if img_src(VADILLO_LOGO): st.markdown(f"<div class='vadillo-box'><img src='{img_src(VADILLO_LOGO)}'></div>", unsafe_allow_html=True)
    df=load_nominas(); year=st.selectbox('Año', list(range(date.today().year-2,date.today().year+9)), index=2)
    with st.expander('➕ Añadir / actualizar nómina', expanded=True):
        mes=st.selectbox('Mes', MONTHS_ES, index=date.today().month-1, key='nom_mes')
        ex=df[(df['Anio']==year)&(df['Mes']==mes)]
        d=ex.iloc[0].to_dict() if not ex.empty else {}
        c=st.columns(5)
        bruto=c[0].number_input('Bruto', value=float(money(d.get('Bruto',0))), step=.01, format='%.2f')
        ss=c[1].number_input('SS 4,85%', value=float(money(d.get('SS', bruto*.0485))), step=.01, format='%.2f')
        desempleo=c[2].number_input('Desempleo 1,65%', value=float(money(d.get('Desempleo', bruto*.0165))), step=.01, format='%.2f')
        irpf=c[3].number_input('IRPF', value=float(money(d.get('IRPF',0))), step=.01, format='%.2f')
        ingresado=c[4].number_input('Ingresado', value=float(money(d.get('Ingresado',0))), step=.01, format='%.2f')
        otros=st.number_input('Otros descuentos', value=float(money(d.get('Otros',0))), step=.01, format='%.2f')
        neto=bruto-ss-desempleo-irpf-otros; st.info(f'Neto esperado: {euro(neto)} · Diferencia: {euro(ingresado-neto)}')
        if st.button('Guardar nómina', use_container_width=True):
            row={'Anio':year,'Mes':mes,'Bruto':bruto,'SS':ss,'Desempleo':desempleo,'IRPF':irpf,'Otros':otros,'Ingresado':ingresado}
            base=df[~((df['Anio']==year)&(df['Mes']==mes))].copy(); save_nominas(pd.concat([base,pd.DataFrame([row])], ignore_index=True)); st.success('Nómina guardada'); st.rerun()
    ydf=load_nominas(); ydf=ydf[ydf['Anio']==year]
    if not ydf.empty:
        st.metric('Bruto anual', euro(ydf['Bruto'].sum())); st.dataframe(ydf, hide_index=True, use_container_width=True)
    render_vacaciones(year)

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
    vac=read_csv('vacaciones.csv', ['Anio','Inicio','Fin','Dias','Nota'])
    if not vac.empty:
        vac['Anio']=pd.to_numeric(vac['Anio'], errors='coerce').fillna(year).astype(int)
        vac['Inicio']=pd.to_datetime(vac['Inicio'], errors='coerce').dt.date
        vac['Fin']=pd.to_datetime(vac['Fin'], errors='coerce').dt.date
        vac=vac.dropna(subset=['Inicio','Fin'])
    yvac=vac[vac['Anio']==year].sort_values('Inicio') if not vac.empty else pd.DataFrame(columns=['Anio','Inicio','Fin','Dias','Nota'])
    used=money(yvac['Dias'].sum()) if not yvac.empty else 0
    st.metric('Días restantes', f"{VACACIONES_ANUALES-used:g}", delta=f"Usados: {used:g}")

    with st.expander('➕ Añadir vacaciones', expanded=False):
        ini=st.date_input('Inicio', value=date(year, date.today().month, 1), min_value=date(year,1,1), max_value=date(year,12,31), key=f'vac_ini_{year}')
        fin=st.date_input('Fin', value=ini, min_value=ini, max_value=date(year,12,31), key=f'vac_fin_{year}_{ini.isoformat()}')
        calc=laboral_days_between(ini, fin, year)
        dias=st.number_input('Días computables', value=float(calc), step=.5, format='%.1f', help='Calculado automáticamente solo con laborables: excluye sábados, domingos y festivos. Puedes editarlo si hace falta.', key=f'vac_dias_{year}_{ini.isoformat()}_{fin.isoformat()}')
        nota=st.text_input('Nota', key=f'vac_nota_{year}_{ini.isoformat()}')
        if st.button('Guardar vacaciones', use_container_width=True, key=f'vac_save_{year}'):
            row={'Anio':year,'Inicio':ini.isoformat(),'Fin':fin.isoformat(),'Dias':dias,'Nota':nota}
            save_csv('vacaciones.csv', pd.concat([vac,pd.DataFrame([row])], ignore_index=True))
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
                    ini2=c[0].date_input('Inicio', value=pd.to_datetime(r['Inicio']).date(), min_value=date(year,1,1), max_value=date(year,12,31), key=f'vac_edit_ini_{year}_{i}', label_visibility='collapsed')
                    fin2=c[1].date_input('Fin', value=max(pd.to_datetime(r['Fin']).date(), ini2), min_value=ini2, max_value=date(year,12,31), key=f'vac_edit_fin_{year}_{i}_{ini2.isoformat()}', label_visibility='collapsed')
                    calc2=laboral_days_between(ini2, fin2, year)
                    dias2=c[2].number_input('Días', value=float(money(r['Dias']) if money(r['Dias']) else calc2), step=.5, format='%.1f', key=f'vac_edit_dias_{year}_{i}', label_visibility='collapsed')
                    nota2=c[3].text_input('Nota', value='' if pd.isna(r.get('Nota','')) else str(r.get('Nota','')), key=f'vac_edit_nota_{year}_{i}', label_visibility='collapsed')
                    if c[4].button('💾', key=f'vac_update_{year}_{i}', help='Guardar cambios'):
                        allv=vac.copy().reset_index(drop=True)
                        mask=(allv['Anio'].astype(int)==year)&(pd.to_datetime(allv['Inicio']).dt.date==pd.to_datetime(r['Inicio']).date())&(pd.to_datetime(allv['Fin']).dt.date==pd.to_datetime(r['Fin']).date())&(allv['Nota'].fillna('').astype(str)==str(r.get('Nota','')))
                        idxs=allv[mask].index.tolist() or [yvac.index[i]]
                        idx=idxs[0]
                        allv.loc[idx, ['Anio','Inicio','Fin','Dias','Nota']] = [year, ini2.isoformat(), fin2.isoformat(), dias2, nota2]
                        save_csv('vacaciones.csv', allv)
                        st.rerun()
                    if c[5].button('❌', key=f'vac_delete_{year}_{i}', help='Borrar periodo'):
                        allv=vac.copy().reset_index(drop=True)
                        mask=(allv['Anio'].astype(int)==year)&(pd.to_datetime(allv['Inicio']).dt.date==pd.to_datetime(r['Inicio']).date())&(pd.to_datetime(allv['Fin']).dt.date==pd.to_datetime(r['Fin']).date())&(allv['Nota'].fillna('').astype(str)==str(r.get('Nota','')))
                        idxs=allv[mask].index.tolist() or [yvac.index[i]]
                        allv=allv.drop(index=idxs[0])
                        save_csv('vacaciones.csv', allv)
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
    render_bank_config('intereses_banks'); df=load_intereses(); year=st.selectbox('Año', list(range(date.today().year-2,date.today().year+9)), index=2, key='int_year')
    with st.expander('➕ Añadir / actualizar interés', expanded=True):
        mes=st.selectbox('Mes', MONTHS_ES, index=date.today().month-1, key='int_mes')
        banco=st.selectbox('Banco', bank_keys(True), format_func=bank_name, key='int_banco')
        ex=df[(df['Anio']==year)&(df['Mes']==mes)&(df['Banco']==banco)]
        d=ex.iloc[0].to_dict() if not ex.empty else {}
        c=st.columns(3)
        bruto=c[0].number_input('Interés bruto', value=float(money(d.get('InteresBruto',0))), step=.01, format='%.2f', key=f'int_bruto_{year}_{mes}_{banco}')
        saldo=c[1].number_input('Saldo', value=float(money(d.get('Saldo',0))), step=.01, format='%.2f', key=f'int_saldo_{year}_{mes}_{banco}')
        ingresado=c[2].number_input('Ingresado', value=float(money(d.get('Ingresado',0))), step=.01, format='%.2f', key=f'int_ingresado_{year}_{mes}_{banco}')
        neto=bruto*0.81; st.info(f'Retención: {euro(bruto*.19)} · Neto esperado: {euro(neto)} · Diferencia: {euro(ingresado-neto)}')
        if st.button('Guardar interés', use_container_width=True):
            row={'Anio':year,'Mes':mes,'Banco':banco,'InteresBruto':bruto,'Saldo':saldo,'Ingresado':ingresado}
            base=df[~((df['Anio']==year)&(df['Mes']==mes)&(df['Banco']==banco))].copy(); save_intereses(pd.concat([base,pd.DataFrame([row])], ignore_index=True)); st.rerun()
    ydf=load_intereses(); ydf=ydf[ydf['Anio']==year]
    if not ydf.empty:
        show=ydf.copy();
        for c in ['InteresBruto','Saldo','Retencion','NetoEsperado','Ingresado','Diferencia']: show[c]=show[c].apply(euro)
        st.dataframe(show, hide_index=True, use_container_width=True)
        labels=(ydf['Mes']+' · '+ydf['Banco']).tolist(); sel=st.selectbox('Borrar registro', ['']+labels)
        if sel and st.button('❌ Borrar interés', use_container_width=True):
            idx=labels.index(sel); todel=ydf.iloc[idx]
            save_intereses(df[~((df['Anio']==todel.Anio)&(df['Mes']==todel.Mes)&(df['Banco']==todel.Banco))]); st.rerun()

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
    if base<=23000: return max(0,8000-0.6098*(base-14800))
    return 0

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
    st.caption('Valores automáticos desde Nóminas e Intereses. Puedes ajustar manualmente aquí para simular o corregir.')
    cols=st.columns(2); manual={}
    names=list(vals.keys())
    for i,name in enumerate(names):
        manual[name]=(cols[i%2].number_input(name, value=float(vals[name]), step=.01, format='%.2f', key=f'irpf_{year}_{safe_key(name)}'))
    diferencial=manual['Cuota líquida']-manual['Total pagos a cuenta']
    html="<table class='irpf-table'><tr><th colspan='2'>RENTA {}</th><th colspan='2'>CUOTA / PAGOS</th></tr>".format(year)
    left=['Rendimientos íntegros','Gastos deducibles','Bonificación','Rendimiento neto trabajo','Base imponible general','Rendimiento neto capital mobiliario','Base liquidable ahorro']
    right=['Resultado escala general','Minoración','Cuota íntegra general','Cuota íntegra ahorro','Cuota líquida','Retenciones trabajo','Retenciones capital mobiliario','Total pagos a cuenta']
    for i in range(max(len(left),len(right))):
        l=left[i] if i<len(left) else ''; r=right[i] if i<len(right) else ''
        html+=f"<tr><td>{l}</td><td class='irpf-num'>{euro(manual.get(l,0)) if l else ''}</td><td>{r}</td><td class='irpf-num'>{euro(manual.get(r,0)) if r else ''}</td></tr>"
    cls='irpf-result-ok' if diferencial<0 else 'irpf-result-bad'
    label='A DEVOLVER' if diferencial<0 else 'A PAGAR'
    html+=f"<tr><td colspan='3'><b>CUOTA DIFERENCIAL</b></td><td class='irpf-num'><b>{euro(diferencial)}</b></td></tr><tr><td colspan='3' class='{cls}'>{label}</td><td class='{cls} irpf-num'>{euro(abs(diferencial))}</td></tr></table>"
    st.markdown(html, unsafe_allow_html=True)

login_gate(); header()
tabs=st.tabs(['Dashboard','Ahorro','Nóminas','Intereses','IRPF'])
with tabs[0]: render_dashboard()
with tabs[1]: render_ahorro()
with tabs[2]: render_nominas()
with tabs[3]: render_intereses()
with tabs[4]: render_irpf()
footer()
