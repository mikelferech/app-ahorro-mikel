import base64
import calendar
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from openpyxl import load_workbook, Workbook

APP_TITLE = "Ahorro Mikel"
EXCEL_PATH = Path("Ahorro.xlsx")
BUDGET_PATH = Path("Presupuesto_Casa.xlsx")
ASSETS = Path("assets")
MONTHS_ES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
BANKS = ["BBVA", "Openbank", "Cajamar", "Otros"]
RETENCION_INTERESES = 0.19
VACACIONES_ANUALES = 23

st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide", initial_sidebar_state="collapsed")

# ------------------ Estilos ------------------
st.markdown("""
<style>
    .main .block-container {padding-top: 1.3rem; max-width: 1500px;}
    div[data-testid="stMetricValue"] {font-size: 2.0rem;}
    .brand-card {border-radius: 14px; padding: 18px; margin-bottom: 14px; border: 1px solid rgba(255,255,255,.12);}
    .brand-title {font-weight: 800; font-size: 1.05rem; margin-bottom: .3rem;}
    .bank-chip {border-radius:10px; padding:8px 12px; font-weight:800; text-align:center; color:#fff; margin-bottom:8px;}
    .bbva-bg {background:#072146;}
    .openbank-bg {background:#e40046;}
    .cajamar-bg {background:#008c95;}
    .vadillo-box {background:#ffffff; border-radius:18px; padding:14px; display:flex; align-items:center; justify-content:center; margin-bottom:16px; border:1px solid rgba(0,0,0,.08);}
    .vadillo-box img {max-height:95px; max-width:95%; object-fit: contain;}
    @media (prefers-color-scheme: dark) {
        .vadillo-box {background:#111827; border-color:rgba(255,255,255,.12);}
        .vadillo-box img {filter: grayscale(1) brightness(0) invert(1);}
    }
    .login-box {max-width: 460px; margin: 5rem auto 1rem auto; padding: 2rem; border-radius: 18px; border:1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.04);}
    .cal-grid {display:grid; grid-template-columns: repeat(7, 1fr); gap:4px; margin-bottom:18px;}
    .cal-head {text-align:center; font-weight:800; font-size:.78rem; opacity:.75;}
    .cal-day {min-height:36px; border-radius:7px; padding:5px; text-align:center; font-size:.82rem; border:1px solid rgba(255,255,255,.10);}
    .cal-empty {opacity:.15;}
    .cal-red {background:#8b0000; color:#fff;}
    .cal-maroon {background:#5b1720; color:#fff;}
    .cal-grey {background:#5c6370; color:#fff;}
    .cal-green {background:#176c37; color:#fff; font-weight:800;}
    .cal-normal {background:#151922; color:#ddd;}
    .small-note {font-size:.85rem; opacity:.8;}
</style>
""", unsafe_allow_html=True)

# ------------------ Utilidades ------------------
def img_b64(path: Path) -> str:
    try:
        return base64.b64encode(path.read_bytes()).decode()
    except Exception:
        return ""

def image_html(path: Path) -> str:
    b64 = img_b64(path)
    if not b64:
        return ""
    ext = path.suffix.lower().replace(".", "") or "png"
    if ext == "jpg": ext = "jpeg"
    return f"data:image/{ext};base64,{b64}"

def money(v) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.replace("€", "").replace(" ", "").strip()
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except Exception:
            return 0.0
    return 0.0

def euro(v) -> str:
    try:
        s = f"{float(v):,.2f} €"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00 €"

def pct(v) -> str:
    try:
        return f"{float(v)*100:.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"

def mes_label(d) -> str:
    if pd.isna(d): return ""
    if not isinstance(d, (pd.Timestamp, datetime, date)):
        d = pd.to_datetime(d, errors="coerce")
    if pd.isna(d): return ""
    return f"{MONTHS_ES[d.month-1]}{str(d.year)[-2:]}"

def first_month_day(year: int, month: int) -> date:
    return date(int(year), int(month), 1)

def normalize_month(d) -> date:
    if isinstance(d, datetime): d = d.date()
    if isinstance(d, pd.Timestamp): d = d.date()
    return date(d.year, d.month, 1)

def date_range(a: date, b: date):
    if isinstance(a, datetime): a=a.date()
    if isinstance(b, datetime): b=b.date()
    cur = a
    while cur <= b:
        yield cur
        cur += timedelta(days=1)

def easter_date(year: int) -> date:
    a = year % 19; b = year // 100; c = year % 100; d = b // 4; e = b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30; i = c // 4; k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7; m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1
    return date(year, month, day)

def festivos_vitoria_base(year: int) -> pd.DataFrame:
    e = easter_date(year)
    rows = []
    fixed = [
        (1,1,"Año Nuevo"), (1,6,"Reyes"), (4,28,"San Prudencio"), (5,1,"Día del Trabajo"),
        (7,25,"Santiago"), (8,5,"Virgen Blanca"), (8,15,"Asunción"), (10,12,"Fiesta Nacional"),
        (11,1,"Todos los Santos"), (12,6,"Constitución"), (12,8,"Inmaculada"), (12,25,"Navidad")
    ]
    for m, d, name in fixed:
        rows.append({"Año": year, "Fecha": date(year, m, d).isoformat(), "Nombre": name, "Activo": True, "Origen": "Base"})
    rows.append({"Año": year, "Fecha": (e - timedelta(days=2)).isoformat(), "Nombre": "Viernes Santo", "Activo": True, "Origen": "Base"})
    rows.append({"Año": year, "Fecha": (e + timedelta(days=1)).isoformat(), "Nombre": "Lunes de Pascua", "Activo": True, "Origen": "Base"})
    return pd.DataFrame(rows)

def load_festivos_df(year: int) -> pd.DataFrame:
    headers = ["Año", "Fecha", "Nombre", "Activo", "Origen"]
    saved = load_table("App_Festivos", headers)
    saved_y = saved[pd.to_numeric(saved.get("Año"), errors="coerce") == year].copy() if not saved.empty else pd.DataFrame(columns=headers)
    if saved_y.empty:
        base = festivos_vitoria_base(year)
        all_df = pd.concat([saved, base], ignore_index=True) if not saved.empty else base
        save_table("App_Festivos", all_df)
        return base
    for c in headers:
        if c not in saved_y:
            saved_y[c] = None
    return saved_y[headers]

def festivos_vitoria(year: int) -> set:
    df = load_festivos_df(year)
    if df.empty:
        return set()
    out = set()
    for _, r in df.iterrows():
        activo = r.get("Activo", True)
        if isinstance(activo, str):
            activo = activo.strip().lower() not in ("false", "0", "no", "n", "")
        if not activo:
            continue
        try:
            out.add(pd.to_datetime(r.get("Fecha")).date())
        except Exception:
            pass
    return out

def save_festivos_year(year: int, df_year: pd.DataFrame):
    headers = ["Año", "Fecha", "Nombre", "Activo", "Origen"]
    current = load_table("App_Festivos", headers)
    other = current[pd.to_numeric(current.get("Año"), errors="coerce") != year].copy() if not current.empty else pd.DataFrame(columns=headers)
    clean = df_year.copy()
    for h in headers:
        if h not in clean: clean[h] = None
    clean["Año"] = year
    clean["Fecha"] = pd.to_datetime(clean["Fecha"], errors="coerce").dt.date.apply(lambda x: x.isoformat() if pd.notna(x) else "")
    clean["Nombre"] = clean["Nombre"].fillna("")
    clean["Activo"] = clean["Activo"].fillna(True)
    clean["Origen"] = clean["Origen"].fillna("Manual")
    clean = clean[clean["Fecha"] != ""]
    save_table("App_Festivos", pd.concat([other, clean[headers]], ignore_index=True))

def is_intensiva(day: date, festivos: set) -> bool:
    return day.weekday() == 4 or (day + timedelta(days=1) in festivos) or (date(day.year,6,1) <= day <= date(day.year,9,30))

def working_vacation_days(start: date, end: date, festivos: set) -> int:
    return sum(1 for d in date_range(start, end) if d.weekday() < 5 and d not in festivos)

# ------------------ Excel ------------------
def wb_data_only():
    return load_workbook(EXCEL_PATH, data_only=True)

def wb_write():
    return load_workbook(EXCEL_PATH)

def ensure_sheet(wb, title, headers):
    if title not in wb.sheetnames:
        ws = wb.create_sheet(title)
        ws.append(headers)
    else:
        ws = wb[title]
        if ws.max_row == 1 and all(ws.cell(1,c).value is None for c in range(1, len(headers)+1)):
            for c,h in enumerate(headers,1): ws.cell(1,c).value = h
    return ws

def sheet_to_df(ws):
    rows = list(ws.iter_rows(values_only=True))
    if not rows: return pd.DataFrame()
    headers = [str(h) if h is not None else f"Col{i}" for i,h in enumerate(rows[0], 1)]
    return pd.DataFrame(rows[1:], columns=headers).dropna(how="all")

def replace_sheet(wb, title, df):
    if title in wb.sheetnames:
        del wb[title]
    ws = wb.create_sheet(title)
    ws.append(list(df.columns))
    for _, row in df.iterrows():
        ws.append([row.get(c) for c in df.columns])
    return ws

@st.cache_data(show_spinner=False)
def extract_original_ahorro() -> pd.DataFrame:
    wb = wb_data_only()
    if "Ahorro BBVA" not in wb.sheetnames: return pd.DataFrame()
    ws = wb["Ahorro BBVA"]
    data = []
    for r in range(8, ws.max_row + 1):
        d = ws.cell(r,1).value
        if not isinstance(d, (datetime, date)): continue
        bbva = money(ws.cell(r,4).value if ws.cell(r,4).value not in (None, "") else ws.cell(r,2).value)
        open_caj = money(ws.cell(r,8).value)
        total = money(ws.cell(r,9).value)
        dif = ws.cell(r,10).value
        if bbva == 0 and open_caj == 0 and total == 0 and money(dif) == 0: continue
        if total == 0: total = bbva + open_caj
        data.append({"Fecha": normalize_month(d), "BBVA": bbva, "Openbank": open_caj, "Cajamar": 0.0, "Otros": 0.0, "Total": total})
    df = pd.DataFrame(data)
    if df.empty: return df
    df = df.drop_duplicates("Fecha", keep="first").sort_values("Fecha")
    df["+/-"] = df["Total"].diff().fillna(0)
    return df

def load_app_ahorro() -> pd.DataFrame:
    wb = wb_data_only()
    if "App_Ahorro" in wb.sheetnames:
        df = sheet_to_df(wb["App_Ahorro"])
        if not df.empty:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.date
            for col in BANKS:
                if col not in df: df[col] = 0.0
                df[col] = df[col].apply(money)
            df = df.dropna(subset=["Fecha"])
            df["Fecha"] = df["Fecha"].apply(normalize_month)
            df["Total"] = df[BANKS].sum(axis=1)
            df = df.sort_values("Fecha")
            df["+/-"] = df["Total"].diff().fillna(0)
            return df
    df = extract_original_ahorro()
    if not df.empty:
        save_ahorro(df)
    return df

def save_ahorro(df: pd.DataFrame):
    wb = wb_write()
    out = df.copy()
    out["Fecha"] = out["Fecha"].apply(lambda x: normalize_month(x).isoformat() if not pd.isna(x) else "")
    for col in BANKS: out[col] = out[col].apply(money)
    out["Total"] = out[BANKS].sum(axis=1)
    out = out.sort_values("Fecha")
    out["+/-"] = out["Total"].diff().fillna(0)
    replace_sheet(wb, "App_Ahorro", out[["Fecha"] + BANKS + ["Total", "+/-"]])
    wb.save(EXCEL_PATH)
    st.cache_data.clear()

def load_table(sheet, headers) -> pd.DataFrame:
    wb = wb_data_only()
    if sheet not in wb.sheetnames:
        return pd.DataFrame(columns=headers)
    df = sheet_to_df(wb[sheet])
    if df.empty: return pd.DataFrame(columns=headers)
    for h in headers:
        if h not in df: df[h] = None
    return df[headers]

def save_table(sheet, df):
    wb = wb_write()
    replace_sheet(wb, sheet, df)
    wb.save(EXCEL_PATH)
    st.cache_data.clear()


def load_bank_config() -> pd.DataFrame:
    headers = ["Clave", "Nombre", "Color", "Activo", "Orden"]
    df = load_table("App_Bancos", headers)
    if df.empty:
        df = pd.DataFrame([
            {"Clave":"BBVA", "Nombre":"BBVA", "Color":"#072146", "Activo":True, "Orden":1},
            {"Clave":"Openbank", "Nombre":"Openbank", "Color":"#e40046", "Activo":True, "Orden":2},
            {"Clave":"Cajamar", "Nombre":"Cajamar", "Color":"#008c95", "Activo":True, "Orden":3},
            {"Clave":"Otros", "Nombre":"Otros", "Color":"#6b7280", "Activo":True, "Orden":4},
        ])
        save_table("App_Bancos", df)
    for h in headers:
        if h not in df: df[h] = None
    df["Clave"] = df["Clave"].fillna("").astype(str)
    df["Nombre"] = df["Nombre"].fillna(df["Clave"]).astype(str)
    df["Color"] = df["Color"].fillna("#6b7280").astype(str)
    df["Activo"] = df["Activo"].apply(lambda x: False if str(x).strip().lower() in ("false","0","no","n","") else bool(x))
    df["Orden"] = pd.to_numeric(df["Orden"], errors="coerce").fillna(99).astype(int)
    # asegurar claves base
    for i, clave in enumerate(BANKS, 1):
        if clave not in set(df["Clave"]):
            df = pd.concat([df, pd.DataFrame([{"Clave":clave, "Nombre":clave, "Color":"#6b7280", "Activo":True, "Orden":i}])], ignore_index=True)
    return df.sort_values("Orden")[headers]

def active_bank_keys() -> list:
    cfg = load_bank_config()
    keys = [k for k in cfg[cfg["Activo"]]["Clave"].tolist() if k in BANKS]
    return keys or BANKS

def bank_name(clave: str) -> str:
    cfg = load_bank_config()
    row = cfg[cfg["Clave"] == clave]
    return str(row.iloc[0]["Nombre"]) if not row.empty else clave

def bank_color(clave: str) -> str:
    cfg = load_bank_config()
    row = cfg[cfg["Clave"] == clave]
    return str(row.iloc[0]["Color"]) if not row.empty else "#6b7280"

def month_options(min_year=None, max_year=None):
    today = date.today()
    min_year = min_year or max(2012, today.year - 2)
    max_year = max_year or today.year + 6
    opts = []
    for y in range(int(min_year), int(max_year)+1):
        for m in range(1, 13):
            d = date(y, m, 1)
            opts.append((d, mes_label(d)))
    return opts

def date_options_for_year(year:int):
    start = date(year,1,1); end = date(year,12,31)
    dias = [d for d in date_range(start,end)]
    nombres = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    return dias, [f"{nombres[d.weekday()]} {d.strftime('%d/%m/%Y')}" for d in dias]

# ------------------ Auth ------------------
def get_secret_auth():
    try:
        return st.secrets["auth"]["username"], st.secrets["auth"]["password"]
    except Exception:
        return None, None

def login_gate():
    user, password = get_secret_auth()
    if not user or not password:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.error("La app está bloqueada hasta configurar usuario y contraseña en Streamlit Secrets.")
        st.code('[auth]\nusername = "mikelferech"\npassword = "TU_CONTRASEÑA"')
        st.markdown("Configúralo en Streamlit → Manage app → Settings → Secrets.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False
    if not st.session_state.auth_ok:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.title("🔒 Ahorro Mikel")
        st.caption("Acceso privado")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar", use_container_width=True):
            if u == user and p == password:
                st.session_state.auth_ok = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

# ------------------ UI ------------------
def bank_chip(css, label):
    st.markdown(f'<div class="bank-chip {css}">{label}</div>', unsafe_allow_html=True)

def style_saldos_table(df):
    cfg = load_bank_config()
    color_map = {r["Nombre"]: r["Color"] for _, r in cfg.iterrows()}
    def col_style(col):
        color = color_map.get(col.name)
        if color:
            return [f"background-color:{color};color:white;font-weight:700" for _ in col]
        return ["" for _ in col]
    styles=[]
    for idx, col in enumerate(df.columns):
        if col in color_map:
            styles.append({"selector":f"th.col_heading.level0.col{idx}", "props":f"background-color:{color_map[col]};color:white;"})
    return df.style.apply(col_style, axis=0).set_table_styles(styles, overwrite=False)

def render_bank_config():
    with st.expander("⚙️ Configurar bancos / colores", expanded=False):
        st.caption("Puedes cambiar el nombre visible, color y si se muestra cada cuenta. La columna interna se mantiene para no perder datos históricos.")
        cfg = load_bank_config().copy()
        edited = st.data_editor(
            cfg,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            disabled=["Clave"],
            key="bank_config_editor",
            column_config={
                "Clave": st.column_config.TextColumn("Clave interna"),
                "Nombre": st.column_config.TextColumn("Nombre visible"),
                "Color": st.column_config.TextColumn("Color HEX"),
                "Activo": st.column_config.CheckboxColumn("Mostrar"),
                "Orden": st.column_config.NumberColumn("Orden", step=1),
            },
        )
        if st.button("Guardar configuración de bancos", use_container_width=True, key="save_bank_config"):
            save_table("App_Bancos", edited)
            st.success("Configuración guardada.")
            st.rerun()

def kpi_dashboard(df):
    valid = df.dropna(subset=["Fecha"]).copy()
    valid = valid[valid["Total"].apply(money) > 0].sort_values("Fecha")
    if valid.empty:
        st.warning("Aún no hay datos válidos de ahorro.")
        return
    last = valid.iloc[-1]
    prev = valid.iloc[-2] if len(valid) > 1 else None
    total = last["Total"]
    diff = total - prev["Total"] if prev is not None else last.get("+/-", 0)
    ytd = total - valid[valid["Fecha"].apply(lambda d: d.year == last["Fecha"].year)].iloc[0]["Total"] if len(valid[valid["Fecha"].apply(lambda d: d.year == last["Fecha"].year)]) else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric(f"Total actual · {mes_label(last['Fecha'])}", euro(total))
    c2.metric("Último +/-", euro(diff), delta=euro(diff))
    c3.metric("BBVA", euro(last.get("BBVA", 0)))
    c4.metric("Openbank + Cajamar", euro(last.get("Openbank", 0) + last.get("Cajamar", 0)))

def render_ahorro():
    st.header("💰 Evolución de ahorro")
    df = load_app_ahorro()
    kpi_dashboard(df)
    render_bank_config()
    keys = active_bank_keys()

    with st.expander("➕ Introducir / actualizar saldo mensual", expanded=False):
        today = date.today()
        min_year = min([d.year for d in df["Fecha"]]) if not df.empty else 2012
        opts = month_options(min_year=min_year, max_year=today.year+6)
        values = [o[0] for o in opts]; labels = [o[1] for o in opts]
        current = date(today.year, today.month, 1)
        idx = values.index(current) if current in values else len(values)-1
        selected = st.selectbox("Mes", values, index=idx, format_func=lambda d: mes_label(d), key="ahorro_month_select")
        existing = df[df["Fecha"] == selected]
        defaults = existing.iloc[0].to_dict() if not existing.empty else {b: 0.0 for b in BANKS}
        cols = st.columns(max(1, len(keys)))
        vals = {}
        for i,b in enumerate(keys):
            vals[b] = cols[i].number_input(f"Saldo {bank_name(b)}", value=float(defaults.get(b,0) or 0), step=0.01, format="%.2f", key=f"saldo_{b}_{selected}")
        for b in BANKS:
            if b not in vals:
                vals[b] = float(defaults.get(b,0) or 0)
        if st.button("Guardar saldo", use_container_width=True):
            new = {"Fecha": selected, **vals}
            df2 = df[df["Fecha"] != selected].copy() if not df.empty else pd.DataFrame()
            df2 = pd.concat([df2, pd.DataFrame([new])], ignore_index=True)
            save_ahorro(df2)
            st.success(f"Saldo de {mes_label(selected)} guardado.")
            st.rerun()

    if df.empty:
        return
    df = df.sort_values("Fecha")
    min_d, max_d = df["Fecha"].min(), df["Fecha"].max()
    c1,c2 = st.columns(2)
    start = c1.date_input("Mostrar desde", value=min_d, min_value=min_d, max_value=max_d, key="ah_start")
    end = c2.date_input("Mostrar hasta", value=max_d, min_value=min_d, max_value=max_d, key="ah_end")
    chart_df = df[(df["Fecha"] >= normalize_month(start)) & (df["Fecha"] <= normalize_month(end))].sort_values("Fecha")
    chart_df["Mes"] = chart_df["Fecha"].apply(mes_label)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart_df["Mes"], y=chart_df["Total"], mode="lines+markers", name="Total"))
    fig.update_layout(title="Evolución patrimonio", yaxis_title="€", xaxis_title="", height=420)
    st.plotly_chart(fig, use_container_width=True)

    colors = ["#1f9d55" if v >= 0 else "#d64545" for v in chart_df["+/-"]]
    fig2 = go.Figure(go.Bar(x=chart_df["Mes"], y=chart_df["+/-"], marker_color=colors, name="+/-"))
    fig2.update_layout(title="Diferencia con el mes anterior", yaxis_title="€", xaxis_title="", height=360)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Saldos por banco")
    chip_cols = st.columns(max(1, len(keys)))
    for i,b in enumerate(keys):
        chip_cols[i].markdown(f'<div class="bank-chip" style="background:{bank_color(b)}">{bank_name(b)}</div>', unsafe_allow_html=True)

    view = df.sort_values("Fecha", ascending=False).copy()
    view["Mes"] = view["Fecha"].apply(mes_label)
    display_cols = ["Mes"]
    rename = {}
    for b in keys:
        rename[b] = bank_name(b)
        display_cols.append(b)
    display_cols += ["Total","+/-"]
    shown = view[display_cols].rename(columns=rename).copy()
    for col in shown.columns:
        if col != "Mes":
            shown[col] = shown[col].apply(euro)
    styled = style_saldos_table(shown)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    with st.expander("✏️ Editar o borrar líneas de ahorro", expanded=False):
        edit = df.sort_values("Fecha", ascending=False).copy()
        edit["Borrar"] = False
        edit["Mes"] = edit["Fecha"].apply(mes_label)
        cols_order = ["Borrar", "Mes"] + BANKS
        edited = st.data_editor(
            edit[cols_order],
            use_container_width=True,
            hide_index=True,
            key="editor_ahorro_lineas",
            column_config={
                "Borrar": st.column_config.CheckboxColumn("Borrar"),
                "Mes": st.column_config.TextColumn("Mes", disabled=True),
                **{b: st.column_config.NumberColumn(bank_name(b), step=0.01, format="%.2f") for b in BANKS},
            },
        )
        if st.button("Guardar cambios de la tabla", use_container_width=True, key="save_edit_ahorro"):
            base = edit[["Fecha","Mes"]].reset_index(drop=True)
            ed = edited.reset_index(drop=True)
            out = base.join(ed.drop(columns=["Mes"], errors="ignore"))
            out = out[~out["Borrar"].fillna(False)].drop(columns=["Borrar","Mes"], errors="ignore")
            for b in BANKS:
                if b not in out: out[b]=0.0
            save_ahorro(out[["Fecha"]+BANKS])
            st.success("Cambios guardados.")
            st.rerun()

# Nóminas
def load_nominas():
    headers = ["Año","Mes","Fecha","Bruto","SS","Desempleo","IRPF_pct","IRPF","Neto_calculado","Ingresado","Diferencia","Estado"]
    df = load_table("App_Nominas", headers)
    if df.empty:
        wb = wb_data_only(); rows=[]
        if "25 26 Vadillo" in wb.sheetnames:
            ws=wb["25 26 Vadillo"]
            for r in range(8, min(ws.max_row, 25)+1):
                d=ws.cell(r,3).value
                if isinstance(d,(datetime,date)):
                    bruto=money(ws.cell(r,4).value); ss=money(ws.cell(r,5).value); desemp=money(ws.cell(r,6).value)
                    irpf=money(ws.cell(r,8).value); ing=money(ws.cell(r,10).value)
                    pctv = irpf/bruto if bruto else 0.13
                    neto = bruto-ss-desemp-irpf
                    rows.append({"Año":d.year,"Mes":d.month,"Fecha":normalize_month(d),"Bruto":bruto,"SS":ss,"Desempleo":desemp,"IRPF_pct":pctv,"IRPF":irpf,"Neto_calculado":neto,"Ingresado":ing,"Diferencia":ing-neto if ing else 0,"Estado":""})
        df = pd.DataFrame(rows, columns=headers)
        if not df.empty: save_table("App_Nominas", df)
    return df

def render_nominas():
    st.header("💼 Nóminas")
    src = image_html(ASSETS / "vadillo.svg")
    if src:
        st.markdown(f'<div class="vadillo-box"><img src="{src}" alt="Grupo Vadillo Asesores"></div>', unsafe_allow_html=True)
    df = load_nominas()
    year = st.selectbox("Año", list(range(date.today().year-1, date.today().year+6)), index=1 if date.today().year in list(range(date.today().year-1, date.today().year+6)) else 0)
    month = st.selectbox("Mes", list(range(1,13)), index=date.today().month-1, format_func=lambda m: f"{MONTHS_ES[m-1]}{str(year)[-2:]}")
    current = df[(pd.to_numeric(df.get("Año"), errors="coerce") == year) & (pd.to_numeric(df.get("Mes"), errors="coerce") == month)]
    cur = current.iloc[0].to_dict() if not current.empty else {}
    st.subheader("Nómina mensual")
    c1,c2,c3,c4,c5 = st.columns(5)
    bruto = c1.number_input("Bruto", value=float(money(cur.get("Bruto",0))), step=0.01, format="%.2f")
    ss_pct = c2.number_input("SS %", value=float(money(cur.get("SS",0))/bruto*100 if bruto and money(cur.get("SS",0)) else 4.85), step=0.01, format="%.2f")
    desempleo_pct = c3.number_input("Desempleo %", value=float(money(cur.get("Desempleo",0))/bruto*100 if bruto and money(cur.get("Desempleo",0)) else 1.65), step=0.01, format="%.2f")
    irpf_pct = c4.number_input("IRPF %", value=float((money(cur.get("IRPF_pct",0)) or 0.13)*100), step=0.01, format="%.2f")
    ingresado = c5.number_input("Ingresado", value=float(money(cur.get("Ingresado",0))), step=0.01, format="%.2f")
    ss = bruto * ss_pct / 100
    desemp = bruto * desempleo_pct / 100
    irpf = bruto * irpf_pct / 100
    neto = bruto - ss - desemp - irpf
    diferencia = ingresado - neto if ingresado else 0
    estado = "✅ Correcto" if ingresado and abs(diferencia) < 0.02 else (f"🟢 Sobra {euro(diferencia)}" if diferencia > 0 else (f"🔴 Falta {euro(abs(diferencia))}" if ingresado else "Pendiente"))
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("SS", euro(ss)); k2.metric("Desempleo", euro(desemp)); k3.metric("IRPF", euro(irpf)); k4.metric("Neto calculado", euro(neto), estado if ingresado else None)
    if st.button("Guardar nómina", use_container_width=True):
        row={"Año":year,"Mes":month,"Fecha":date(year,month,1),"Bruto":bruto,"SS":ss,"Desempleo":desemp,"IRPF_pct":irpf_pct/100,"IRPF":irpf,"Neto_calculado":neto,"Ingresado":ingresado,"Diferencia":diferencia,"Estado":estado}
        df2 = df[~((pd.to_numeric(df.get("Año"), errors="coerce")==year)&(pd.to_numeric(df.get("Mes"), errors="coerce")==month))].copy() if not df.empty else pd.DataFrame()
        df2 = pd.concat([df2, pd.DataFrame([row])], ignore_index=True)
        save_table("App_Nominas", df2)
        st.success("Nómina guardada."); st.rerun()
    show = df[pd.to_numeric(df.get("Año"), errors="coerce") == year].copy() if not df.empty else pd.DataFrame()
    if not show.empty:
        show["Mes"] = show.apply(lambda r: f"{MONTHS_ES[int(r['Mes'])-1]}{str(int(r['Año']))[-2:]}", axis=1)
        show = show.sort_values(["Año","Mes"], ascending=False)
        for col in ["Bruto","SS","Desempleo","IRPF","Neto_calculado","Ingresado","Diferencia"]:
            show[col]=show[col].apply(euro)
        st.dataframe(show[["Mes","Bruto","SS","Desempleo","IRPF","Neto_calculado","Ingresado","Diferencia","Estado"]], use_container_width=True, hide_index=True)
        raw = df[pd.to_numeric(df.get("Año"), errors="coerce") == year].copy()
        st.subheader("Resumen anual")
        a,b,c,d = st.columns(4)
        a.metric("Bruto acumulado", euro(raw["Bruto"].apply(money).sum()))
        b.metric("Retención IRPF", euro(raw["IRPF"].apply(money).sum()))
        c.metric("Gastos deducibles", euro(raw["SS"].apply(money).sum()+raw["Desempleo"].apply(money).sum()))
        d.metric("Neto acumulado", euro(raw["Neto_calculado"].apply(money).sum()))
    render_vacaciones(year)

def load_vacaciones():
    headers=["Año","Inicio","Fin","Dias","Notas"]
    return load_table("App_Vacaciones", headers)

def render_festivos_editor(year:int):
    with st.expander("🟤 Revisar / modificar festivos", expanded=False):
        st.caption("Estos días se usan para pintar el calendario en granate, calcular vísperas de festivo y descontar vacaciones. Puedes desactivar, cambiar fechas o añadir filas manuales.")
        fdf = load_festivos_df(year).copy()
        if fdf.empty:
            fdf = festivos_vitoria_base(year)
        fdf["Fecha"] = pd.to_datetime(fdf["Fecha"], errors="coerce").dt.date
        fdf["Activo"] = fdf["Activo"].apply(lambda x: False if str(x).strip().lower() in ("false","0","no","n","") else bool(x))
        fdf = fdf[["Fecha", "Nombre", "Activo", "Origen"]].sort_values("Fecha")
        edited = st.data_editor(
            fdf,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key=f"festivos_editor_{year}",
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "Nombre": st.column_config.TextColumn("Nombre"),
                "Activo": st.column_config.CheckboxColumn("Activo"),
                "Origen": st.column_config.TextColumn("Origen"),
            },
        )
        c1, c2 = st.columns(2)
        if c1.button("Guardar festivos", use_container_width=True, key=f"guardar_festivos_{year}"):
            out = edited.copy()
            out["Año"] = year
            save_festivos_year(year, out[["Año", "Fecha", "Nombre", "Activo", "Origen"]])
            st.cache_data.clear()
            st.success("Festivos guardados.")
            st.rerun()
        if c2.button("Restaurar festivos base", use_container_width=True, key=f"restaurar_festivos_{year}"):
            save_festivos_year(year, festivos_vitoria_base(year))
            st.cache_data.clear()
            st.success("Festivos base restaurados.")
            st.rerun()

def render_vacaciones(year:int):
    st.divider(); st.subheader("🌴 Vacaciones y calendario laboral")
    render_festivos_editor(year)
    festivos = festivos_vitoria(year)
    df = load_vacaciones()
    if not df.empty:
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(year).astype(int)
    ydf = df[df["Año"]==year].copy() if not df.empty else pd.DataFrame(columns=["Año","Inicio","Fin","Dias","Notas"])
    used = sum(money(x) for x in ydf.get("Dias", []))
    c1,c2,c3 = st.columns(3)
    c1.metric("Días disponibles", VACACIONES_ANUALES)
    c2.metric("Días usados", f"{used:g}")
    c3.metric("Días restantes", f"{VACACIONES_ANUALES-used:g}")
    with st.expander("➕ Añadir periodo de vacaciones", expanded=False):
        dias_year, labels_year = date_options_for_year(year)
        today = date.today()
        default_start = today if today.year == year else date(year,1,1)
        idx_start = dias_year.index(default_start) if default_start in dias_year else 0
        start = st.selectbox("Fecha inicio", dias_year, index=idx_start, format_func=lambda d: labels_year[dias_year.index(d)], key=f"vac_start_select_{year}")
        end_options = [d for d in dias_year if d >= start]
        end = st.selectbox("Fecha fin", end_options, index=0, format_func=lambda d: labels_year[dias_year.index(d)], key=f"vac_end_select_{year}_{start.isoformat()}")
        calc = working_vacation_days(start, end, festivos)
        dias = st.number_input("Días calculados/editables", value=float(calc), step=0.5, format="%.1f", key=f"vac_dias_{year}_{start}_{end}")
        notas = st.text_input("Notas", value="")
        st.caption("Las fechas se eligen en listas que empiezan en lunes y la fecha fin arranca desde la fecha inicio.")
        if st.button("Guardar vacaciones", use_container_width=True):
            new = {"Año":year,"Inicio":start.isoformat(),"Fin":end.isoformat(),"Dias":dias,"Notas":notas}
            df2 = pd.concat([df, pd.DataFrame([new])], ignore_index=True) if not df.empty else pd.DataFrame([new])
            save_table("App_Vacaciones", df2)
            st.success("Vacaciones guardadas."); st.rerun()
    if not ydf.empty:
        ydf_show=ydf.copy(); st.dataframe(ydf_show, use_container_width=True, hide_index=True)
    vac_days=set()
    for _,r in ydf.iterrows():
        try:
            a=pd.to_datetime(r["Inicio"]).date(); b=pd.to_datetime(r["Fin"]).date()
            vac_days.update(set(date_range(a,b)))
        except Exception: pass
    month_cols = st.columns(3)
    for m in range(1,13):
        with month_cols[(m-1)%3]:
            st.markdown(f"**{MONTHS_ES[m-1]} {year}**")
            render_month_calendar(year, m, festivos, vac_days)

def render_month_calendar(year, month, festivos, vac_days):
    cal = calendar.Calendar(firstweekday=0)
    html = '<div class="cal-grid">' + ''.join([f'<div class="cal-head">{d}</div>' for d in ["L","M","X","J","V","S","D"]])
    for week in cal.monthdatescalendar(year, month):
        for d in week:
            if d.month != month:
                cls="cal-day cal-empty"; txt=""
            elif d in vac_days:
                cls="cal-day cal-green"; txt=str(d.day)
            elif d in festivos:
                cls="cal-day cal-maroon"; txt=str(d.day)
            elif d.weekday() >= 5:
                cls="cal-day cal-red"; txt=str(d.day)
            elif is_intensiva(d, festivos):
                cls="cal-day cal-grey"; txt=str(d.day)
            else:
                cls="cal-day cal-normal"; txt=str(d.day)
            html += f'<div class="{cls}">{txt}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_intereses():
    st.header("🏦 Intereses cuentas")
    headers=["Año","Mes","Fecha","Cuenta1_Interes","Cuenta1_Saldo","Cuenta2_Interes","Cuenta2_Saldo","Retencion","Neto_esperado","Ingresado","Diferencia","Estado"]
    df=load_table("App_Intereses", headers)
    year=st.selectbox("Año", list(range(2023, date.today().year+6)), index=max(0, date.today().year-2023), key="int_year")
    month=st.selectbox("Mes", list(range(1,13)), index=date.today().month-1, format_func=lambda m: f"{MONTHS_ES[m-1]}{str(year)[-2:]}", key="int_month")
    cur=df[(pd.to_numeric(df.get("Año"), errors="coerce")==year)&(pd.to_numeric(df.get("Mes"), errors="coerce")==month)] if not df.empty else pd.DataFrame()
    row=cur.iloc[0].to_dict() if not cur.empty else {}
    c1,c2,c3,c4,c5=st.columns(5)
    i1=c1.number_input("Interés 1 bruto", value=float(money(row.get("Cuenta1_Interes",0))), step=0.01, format="%.2f", key=f"int_i1_{year}_{month}")
    s1=c2.number_input("Saldo 1", value=float(money(row.get("Cuenta1_Saldo",0))), step=0.01, format="%.2f", key=f"int_s1_{year}_{month}")
    i2=c3.number_input("Interés 2 bruto", value=float(money(row.get("Cuenta2_Interes",0))), step=0.01, format="%.2f", key=f"int_i2_{year}_{month}")
    s2=c4.number_input("Saldo 2", value=float(money(row.get("Cuenta2_Saldo",0))), step=0.01, format="%.2f", key=f"int_s2_{year}_{month}")
    ingresado=c5.number_input("Ingresado", value=float(money(row.get("Ingresado",0))), step=0.01, format="%.2f", key=f"int_ingresado_{year}_{month}")
    bruto=i1+i2; ret=bruto*RETENCION_INTERESES; neto=bruto-ret; dif=ingresado-neto if ingresado else 0
    estado = "✅ Correcto" if ingresado and abs(dif)<0.02 else (f"🟢 Sobra {euro(dif)}" if dif>0 else (f"🔴 Falta {euro(abs(dif))}" if ingresado else "Pendiente"))
    a,b,c,d=st.columns(4); a.metric("Bruto", euro(bruto)); b.metric("Retención 19%", euro(ret)); c.metric("Neto esperado", euro(neto)); d.metric("Diferencia", euro(dif))
    if st.button("Guardar intereses", use_container_width=True, key=f"btn_guardar_intereses_{year}_{month}"):
        new={"Año":year,"Mes":month,"Fecha":date(year,month,1),"Cuenta1_Interes":i1,"Cuenta1_Saldo":s1,"Cuenta2_Interes":i2,"Cuenta2_Saldo":s2,"Retencion":ret,"Neto_esperado":neto,"Ingresado":ingresado,"Diferencia":dif,"Estado":estado}
        df2=df[~((pd.to_numeric(df.get("Año"), errors="coerce")==year)&(pd.to_numeric(df.get("Mes"), errors="coerce")==month))].copy() if not df.empty else pd.DataFrame()
        df2=pd.concat([df2,pd.DataFrame([new])],ignore_index=True); save_table("App_Intereses", df2); st.success("Intereses guardados."); st.rerun()
    if not df.empty:
        show=df.copy(); show["Año"]=pd.to_numeric(show["Año"], errors="coerce")
        show=show[show["Año"]==year]
        if not show.empty:
            show["Mes_txt"]=show.apply(lambda r: f"{MONTHS_ES[int(r['Mes'])-1]}{str(int(r['Año']))[-2:]}", axis=1)
            show=show.sort_values(["Año","Mes"], ascending=False)
            for col in ["Cuenta1_Interes","Cuenta1_Saldo","Cuenta2_Interes","Cuenta2_Saldo","Retencion","Neto_esperado","Ingresado","Diferencia"]: show[col]=show[col].apply(euro)
            st.dataframe(show[["Mes_txt","Cuenta1_Interes","Cuenta1_Saldo","Cuenta2_Interes","Cuenta2_Saldo","Retencion","Neto_esperado","Ingresado","Diferencia","Estado"]], use_container_width=True, hide_index=True)

def extract_presupuesto_irpf_table() -> pd.DataFrame:
    try:
        wb = load_workbook(BUDGET_PATH, data_only=True)
        if "IRPF" not in wb.sheetnames:
            return pd.DataFrame()
        ws = wb["IRPF"]
        rows=[]
        for row in ws.iter_rows(values_only=True):
            vals = list(row)
            if any(v is not None and str(v).strip() != "" for v in vals):
                rows.append(vals)
        if not rows:
            return pd.DataFrame()
        max_len = max(len(r) for r in rows)
        rows = [r + [None]*(max_len-len(r)) for r in rows]
        # quitar columnas totalmente vacías
        df = pd.DataFrame(rows)
        df = df.dropna(axis=1, how="all")
        df.columns = [f"Col {i+1}" for i in range(df.shape[1])]
        return df
    except Exception:
        return pd.DataFrame()

def render_irpf():
    st.header("📄 IRPF")
    st.caption("Modelo basado en la hoja IRPF de Presupuesto Casa, conectado a nóminas e intereses de esta app.")
    year = st.selectbox("Año IRPF", list(range(2023, date.today().year+6)), index=max(0, date.today().year-2023), key="irpf_year")
    nom=load_nominas(); inte=load_table("App_Intereses", ["Año","Mes","Fecha","Cuenta1_Interes","Cuenta1_Saldo","Cuenta2_Interes","Cuenta2_Saldo","Retencion","Neto_esperado","Ingresado","Diferencia","Estado"])
    nom_y=nom[pd.to_numeric(nom.get("Año"), errors="coerce")==year] if not nom.empty else pd.DataFrame()
    int_y=inte[pd.to_numeric(inte.get("Año"), errors="coerce")==year] if not inte.empty else pd.DataFrame()
    bruto = nom_y["Bruto"].apply(money).sum() if not nom_y.empty else 0
    gastos = nom_y["SS"].apply(money).sum()+nom_y["Desempleo"].apply(money).sum() if not nom_y.empty else 0
    ret_trabajo = nom_y["IRPF"].apply(money).sum() if not nom_y.empty else 0
    intereses_brutos = (int_y["Cuenta1_Interes"].apply(money).sum()+int_y["Cuenta2_Interes"].apply(money).sum()) if not int_y.empty else 0
    ret_ahorro = int_y["Retencion"].apply(money).sum() if not int_y.empty else 0
    a,b,c,d=st.columns(4)
    a.metric("Rendimientos íntegros", euro(bruto)); b.metric("Gastos deducibles", euro(gastos)); c.metric("Retención nóminas", euro(ret_trabajo)); d.metric("Intereses brutos", euro(intereses_brutos))
    base_general=max(bruto-gastos,0); base_ahorro=max(intereses_brutos,0); pagos=ret_trabajo+ret_ahorro
    st.subheader("Resumen automático")
    rows=[
        ("RENTA GENERAL", "", ""),
        ("Rendimientos íntegros", euro(bruto), "Nóminas"),
        ("Gastos deducibles", euro(gastos), "SS + Desempleo"),
        ("Base imponible general", euro(base_general), "Auto"),
        ("RENTA DEL AHORRO", "", ""),
        ("Intereses brutos", euro(intereses_brutos), "Intereses cuentas"),
        ("Retención ahorro", euro(ret_ahorro), "19%"),
        ("Base imponible ahorro", euro(base_ahorro), "Auto"),
        ("PAGOS A CUENTA", euro(pagos), "IRPF nómina + retención intereses"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Concepto","Importe","Origen"]), use_container_width=True, hide_index=True)
    st.subheader("Tabla completa del modelo Presupuesto Casa")
    model = extract_presupuesto_irpf_table()
    if model.empty:
        st.warning("No he podido leer la tabla IRPF completa de Presupuesto Casa.")
    else:
        st.dataframe(model, use_container_width=True, hide_index=True, height=680)
        st.caption("De momento se muestra completa como referencia. En la siguiente iteración podemos mapear cada celda/fórmula concreta a los datos automáticos de Ahorro Mikel.")

# Main
login_gate()
col_title, col_out = st.columns([5,1])
with col_title:
    st.title("💰 Ahorro Mikel")
    st.caption("Patrimonio · Nóminas · Vacaciones · Intereses · IRPF")
with col_out:
    if st.button("Cerrar sesión"):
        st.session_state.auth_ok=False; st.rerun()

if EXCEL_PATH.exists():
    with open(EXCEL_PATH, "rb") as f:
        st.download_button("⬇️ Descargar Excel actualizado", f, file_name="Ahorro_actualizado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

tabs = st.tabs(["Dashboard", "Ahorro", "Nóminas", "Intereses", "IRPF"])
with tabs[0]:
    st.header("📊 Dashboard")
    df = load_app_ahorro(); kpi_dashboard(df)
    if not df.empty:
        c1,c2=st.columns(2)
        with c1:
            chart = df.sort_values("Fecha").copy(); chart["Mes"]=chart["Fecha"].apply(mes_label)
            fig = go.Figure(go.Scatter(x=chart["Mes"], y=chart["Total"], mode="lines+markers"))
            fig.update_layout(title="Patrimonio histórico", height=360)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            colors=["#1f9d55" if v>=0 else "#d64545" for v in chart["+/-"]]
            fig2=go.Figure(go.Bar(x=chart["Mes"], y=chart["+/-"], marker_color=colors))
            fig2.update_layout(title="+/- mensual", height=360)
            st.plotly_chart(fig2, use_container_width=True)
with tabs[1]: render_ahorro()
with tabs[2]: render_nominas()
with tabs[3]: render_intereses()
with tabs[4]: render_irpf()
