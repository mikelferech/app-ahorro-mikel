from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
import calendar

import pandas as pd
import plotly.express as px
import streamlit as st
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

EXCEL_PATH = Path(__file__).with_name("Ahorro.xlsx")
APP_AHORRO = "App_Ahorro"
APP_NOMINAS = "App_Nominas"
APP_VACACIONES = "App_Vacaciones"
APP_INTERESES = "App_Intereses"
RETENCION_AHORRO = 0.19
VACACIONES_ANUALES = 23

st.set_page_config(page_title="Ahorro Mikel", page_icon="💰", layout="wide")

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def parse_money(value):
    """Convierte importes de Excel a float aunque vengan con €, puntos, comas o fórmulas simples."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0

    # Fórmulas simples tipo =74000+50000
    if text.startswith('='):
        expr = text[1:].replace('€', '').replace(' ', '')
        # Solo permitimos números y operaciones básicas para evitar ejecutar nada raro
        allowed = set('0123456789.,+-*/()')
        if expr and all(ch in allowed for ch in expr):
            expr = expr.replace(',', '.')
            try:
                return float(eval(expr, {"__builtins__": {}}, {}))
            except Exception:
                return 0.0
        return 0.0

    text = text.replace('€', '').replace(' ', '')
    # Formato español: 1.234,56 -> 1234.56
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return 0.0


def get_wb():
    if EXCEL_PATH.exists():
        return load_workbook(EXCEL_PATH)
    return Workbook()


def save_df_to_sheet(wb, sheet_name: str, df: pd.DataFrame):
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]
    ws = wb.create_sheet(sheet_name)
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    for col in ws.columns:
        width = min(max(len(str(c.value or "")) for c in col) + 2, 28)
        ws.column_dimensions[col[0].column_letter].width = width


def read_sheet_df(sheet_name: str) -> pd.DataFrame:
    wb = get_wb()
    if sheet_name not in wb.sheetnames:
        return pd.DataFrame()
    ws = wb[sheet_name]
    rows = list(ws.values)
    if not rows:
        return pd.DataFrame()
    headers = list(rows[0])
    df = pd.DataFrame(rows[1:], columns=headers)
    return df.dropna(how="all")


def init_app_sheets():
    wb = get_wb()
    changed = False

    if APP_AHORRO not in wb.sheetnames:
        df = extraer_ahorro_original(wb)
        save_df_to_sheet(wb, APP_AHORRO, df)
        changed = True

    if APP_NOMINAS not in wb.sheetnames:
        year = date.today().year
        df = pd.DataFrame({
            "Año": [year] * 14,
            "Mes": MESES + ["Extra 1", "Extra 2"],
            "Bruto": [0.0] * 14,
            "SS": [0.0] * 14,
            "Desempleo": [0.0] * 14,
            "IRPF": [0.0] * 14,
            "Neto calculado": [0.0] * 14,
            "Ingresado": [0.0] * 14,
            "Diferencia": [0.0] * 14,
            "Estado": [""] * 14,
        })
        save_df_to_sheet(wb, APP_NOMINAS, df)
        changed = True

    if APP_VACACIONES not in wb.sheetnames:
        df = pd.DataFrame(columns=["Año", "Fecha inicio", "Fecha fin", "Días", "Notas"])
        save_df_to_sheet(wb, APP_VACACIONES, df)
        changed = True

    if APP_INTERESES not in wb.sheetnames:
        year = date.today().year
        rows = []
        for m in range(1, 13):
            rows.append({"Año": year, "Mes": m, "Interés 1 %": 0.0, "Saldo 1": 0.0, "Interés 2 %": 0.0, "Saldo 2": 0.0, "Interés bruto": 0.0, "Retención 19%": 0.0, "Neto calculado": 0.0, "Ingresado": 0.0, "Diferencia": 0.0, "Estado": ""})
        save_df_to_sheet(wb, APP_INTERESES, pd.DataFrame(rows))
        changed = True

    if changed:
        wb.save(EXCEL_PATH)


def extraer_ahorro_original(wb) -> pd.DataFrame:
    rows = []
    if "Ahorro BBVA" in wb.sheetnames:
        ws = wb["Ahorro BBVA"]
        header_row = 7
        headers = [ws.cell(header_row, c).value for c in range(1, ws.max_column + 1)]
        for r in range(header_row + 1, ws.max_row + 1):
            mes = ws.cell(r, 1).value
            if not isinstance(mes, (datetime, date)):
                continue
            vals = {headers[c-1]: ws.cell(r, c).value for c in range(1, min(ws.max_column, 10) + 1)}
            bbva = parse_money(vals.get("BBVA"))
            # En el Excel original BBVA puede venir como fórmula; si no hay valor calculable, usamos Cuenta + Ahorro.
            if bbva == 0:
                bbva = parse_money(vals.get("Cuenta")) + parse_money(vals.get("Ahorro"))
            openbank = parse_money(vals.get("Openbank Cajamar"))
            rows.append({
                "Mes": pd.to_datetime(mes).date(),
                "BBVA": bbva,
                "Openbank": openbank,
                "Cajamar": 0.0,
            })
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Mes", "BBVA", "Openbank", "Cajamar"])
    df = df.sort_values("Mes")
    return calcular_ahorro(df)


def calcular_ahorro(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Mes", "BBVA", "Openbank", "Cajamar", "Total", "+/-"])
    df = df.copy()
    df["Mes"] = pd.to_datetime(df["Mes"]).dt.date
    for c in ["BBVA", "Openbank", "Cajamar"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df = df.sort_values("Mes")
    df["Total"] = df[["BBVA", "Openbank", "Cajamar"]].sum(axis=1)
    df["+/-"] = df["Total"].diff().fillna(0)
    return df


def persist(sheet_name: str, df: pd.DataFrame):
    wb = get_wb()
    save_df_to_sheet(wb, sheet_name, df)
    wb.save(EXCEL_PATH)


def download_excel_button():
    with open(EXCEL_PATH, "rb") as f:
        st.download_button("⬇️ Descargar Excel actualizado", f.read(), file_name="Ahorro_actualizado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_ahorro():
    st.header("💰 Evolución de ahorro")
    df = calcular_ahorro(read_sheet_df(APP_AHORRO))
    c1, c2, c3, c4 = st.columns(4)
    total = df["Total"].iloc[-1] if not df.empty else 0
    dif = df["+/-"].iloc[-1] if not df.empty else 0
    c1.metric("Total actual", f"{total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    c2.metric("Último +/-", f"{dif:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    c3.metric("BBVA", f"{(df['BBVA'].iloc[-1] if not df.empty else 0):,.2f} €")
    c4.metric("Openbank + Cajamar", f"{((df['Openbank'].iloc[-1] + df['Cajamar'].iloc[-1]) if not df.empty else 0):,.2f} €")

    with st.expander("➕ Introducir saldo mensual", expanded=True):
        with st.form("nuevo_saldo"):
            mes = st.date_input("Mes y año", value=date.today().replace(day=1))
            bbva = st.number_input("Saldo BBVA", step=100.0, format="%.2f")
            openbank = st.number_input("Saldo Openbank", step=100.0, format="%.2f")
            cajamar = st.number_input("Saldo Cajamar", step=100.0, format="%.2f")
            if st.form_submit_button("Guardar saldo"):
                new = pd.DataFrame([{"Mes": mes.replace(day=1), "BBVA": bbva, "Openbank": openbank, "Cajamar": cajamar}])
                base = df[["Mes", "BBVA", "Openbank", "Cajamar"]]
                base = base[pd.to_datetime(base["Mes"]).dt.date != mes.replace(day=1)]
                out = calcular_ahorro(pd.concat([base, new], ignore_index=True))
                persist(APP_AHORRO, out)
                st.success("Saldo guardado.")
                st.rerun()

    min_d, max_d = pd.to_datetime(df["Mes"]).min().date(), pd.to_datetime(df["Mes"]).max().date() if not df.empty else (date.today(), date.today())
    periodo = st.slider("Periodo a mostrar", min_value=min_d, max_value=max_d, value=(min_d, max_d), format="MM/YYYY") if not df.empty else None
    chart_df = df[(pd.to_datetime(df["Mes"]).dt.date >= periodo[0]) & (pd.to_datetime(df["Mes"]).dt.date <= periodo[1])] if periodo else df
    st.plotly_chart(px.line(chart_df, x="Mes", y="Total", title="Evolución del ahorro total", markers=True), use_container_width=True)
    st.plotly_chart(px.bar(chart_df, x="Mes", y="+/-", title="Diferencia respecto al mes anterior"), use_container_width=True)
    edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Guardar cambios tabla ahorro"):
        persist(APP_AHORRO, calcular_ahorro(edited))
        st.success("Tabla guardada.")


def render_nominas():
    st.header("🧾 Nóminas y vacaciones")
    df = read_sheet_df(APP_NOMINAS)
    if df.empty:
        return
    year = st.number_input("Año", min_value=2012, max_value=2100, value=int(date.today().year), step=1)
    dyear = df[df["Año"].astype(int) == year].copy()
    if dyear.empty:
        dyear = pd.DataFrame({"Año": [year]*14, "Mes": MESES+["Extra 1","Extra 2"], "Bruto": [0.0]*14, "SS": [0.0]*14, "Desempleo": [0.0]*14, "IRPF": [0.0]*14, "Neto calculado": [0.0]*14, "Ingresado": [0.0]*14, "Diferencia": [0.0]*14, "Estado": [""]*14})
    edit = st.data_editor(dyear, use_container_width=True, num_rows="dynamic")
    for c in ["Bruto", "SS", "Desempleo", "IRPF", "Ingresado"]:
        edit[c] = pd.to_numeric(edit[c], errors="coerce").fillna(0)
    edit["Neto calculado"] = edit["Bruto"] - edit["SS"] - edit["Desempleo"] - edit["IRPF"]
    edit["Diferencia"] = edit["Ingresado"] - edit["Neto calculado"]
    edit["Estado"] = edit["Diferencia"].apply(lambda x: "Correcto" if abs(x) < 0.01 else (f"Sobran {x:.2f} €" if x > 0 else f"Faltan {abs(x):.2f} €"))
    col1, col2, col3 = st.columns(3)
    col1.metric("Bruto anual", f"{edit['Bruto'].sum():,.2f} €")
    col2.metric("Gastos deducibles", f"{(edit['SS'].sum()+edit['Desempleo'].sum()):,.2f} €")
    col3.metric("Retención IRPF", f"{edit['IRPF'].sum():,.2f} €")
    if st.button("💾 Guardar nóminas"):
        resto = df[df["Año"].astype(str) != str(year)]
        persist(APP_NOMINAS, pd.concat([resto, edit], ignore_index=True))
        st.success("Nóminas guardadas.")

    st.subheader("Vacaciones")
    vac = read_sheet_df(APP_VACACIONES)
    if vac.empty:
        vac = pd.DataFrame(columns=["Año", "Fecha inicio", "Fecha fin", "Días", "Notas"])
    vac_y = vac[vac["Año"].astype(str) == str(year)] if "Año" in vac else vac
    used = pd.to_numeric(vac_y.get("Días", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    st.metric("Días restantes", f"{VACACIONES_ANUALES - used:g} de {VACACIONES_ANUALES}")
    vac_edit = st.data_editor(vac_y if not vac_y.empty else pd.DataFrame([{"Año":year,"Fecha inicio":date(year,1,1),"Fecha fin":date(year,1,1),"Días":0,"Notas":""}]), use_container_width=True, num_rows="dynamic")
    if st.button("💾 Guardar vacaciones"):
        resto = vac[vac["Año"].astype(str) != str(year)] if not vac.empty and "Año" in vac else pd.DataFrame()
        persist(APP_VACACIONES, pd.concat([resto, vac_edit], ignore_index=True))
        st.success("Vacaciones guardadas.")
    render_calendario(year, vac_edit)


def render_calendario(year: int, vac_df: pd.DataFrame):
    st.subheader("Calendario anual")
    festivos_txt = st.text_input("Festivos separados por coma, formato DD/MM", "01/01,06/01,01/05,25/12")
    festivos = set()
    for item in festivos_txt.split(','):
        try:
            d, m = map(int, item.strip().split('/'))
            festivos.add(date(year, m, d))
        except Exception:
            pass
    vacation_days = set()
    for _, r in vac_df.iterrows():
        try:
            ini, fin = pd.to_datetime(r["Fecha inicio"]).date(), pd.to_datetime(r["Fecha fin"]).date()
            cur = ini
            while cur <= fin:
                vacation_days.add(cur)
                cur += timedelta(days=1)
        except Exception:
            pass
    months = st.columns(3)
    for m in range(1, 13):
        with months[(m-1)%3]:
            cal = calendar.Calendar(firstweekday=0)
            rows = []
            for week in cal.monthdatescalendar(year, m):
                rows.append([day.day if day.month == m else "" for day in week])
            st.caption(calendar.month_name[m].capitalize())
            st.table(pd.DataFrame(rows, columns=["L", "M", "X", "J", "V", "S", "D"]))


def render_intereses():
    st.header("🏦 Intereses cuentas")
    df = read_sheet_df(APP_INTERESES)
    year = st.number_input("Año intereses", 2012, 2100, int(date.today().year), 1)
    d = df[df["Año"].astype(str) == str(year)].copy() if not df.empty else pd.DataFrame()
    if d.empty:
        d = pd.DataFrame([{"Año":year,"Mes":m,"Interés 1 %":0.0,"Saldo 1":0.0,"Interés 2 %":0.0,"Saldo 2":0.0,"Interés bruto":0.0,"Retención 19%":0.0,"Neto calculado":0.0,"Ingresado":0.0,"Diferencia":0.0,"Estado":""} for m in range(1,13)])
    edit = st.data_editor(d, use_container_width=True, num_rows="dynamic")
    for c in ["Interés 1 %","Saldo 1","Interés 2 %","Saldo 2","Ingresado"]:
        edit[c] = pd.to_numeric(edit[c], errors="coerce").fillna(0)
    edit["Interés bruto"] = (edit["Saldo 1"] * edit["Interés 1 %"] / 100 / 12) + (edit["Saldo 2"] * edit["Interés 2 %"] / 100 / 12)
    edit["Retención 19%"] = edit["Interés bruto"] * RETENCION_AHORRO
    edit["Neto calculado"] = edit["Interés bruto"] - edit["Retención 19%"]
    edit["Diferencia"] = edit["Ingresado"] - edit["Neto calculado"]
    edit["Estado"] = edit["Diferencia"].apply(lambda x: "Correcto" if abs(x) < 0.01 else (f"Sobran {x:.2f} €" if x > 0 else f"Faltan {abs(x):.2f} €"))
    c1, c2, c3 = st.columns(3)
    c1.metric("Interés bruto anual", f"{edit['Interés bruto'].sum():,.2f} €")
    c2.metric("Retención anual", f"{edit['Retención 19%'].sum():,.2f} €")
    c3.metric("Neto anual", f"{edit['Neto calculado'].sum():,.2f} €")
    if st.button("💾 Guardar intereses"):
        resto = df[df["Año"].astype(str) != str(year)] if not df.empty else pd.DataFrame()
        persist(APP_INTERESES, pd.concat([resto, edit], ignore_index=True))
        st.success("Intereses guardados.")


def render_irpf():
    st.header("📄 IRPF")
    nom = read_sheet_df(APP_NOMINAS)
    inter = read_sheet_df(APP_INTERESES)
    year = st.number_input("Año IRPF", 2012, 2100, int(date.today().year), 1)
    n = nom[nom["Año"].astype(str) == str(year)] if not nom.empty else pd.DataFrame()
    i = inter[inter["Año"].astype(str) == str(year)] if not inter.empty else pd.DataFrame()
    bruto = pd.to_numeric(n.get("Bruto", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    gastos = (pd.to_numeric(n.get("SS", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() + pd.to_numeric(n.get("Desempleo", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    ret = pd.to_numeric(n.get("IRPF", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    ahorro_bruto = pd.to_numeric(i.get("Interés bruto", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    ahorro_ret = pd.to_numeric(i.get("Retención 19%", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    resumen = pd.DataFrame({"Concepto":["Rendimientos íntegros trabajo","Gastos deducibles","Retenciones trabajo","Intereses bruto ahorro","Retenciones ahorro"],"Importe":[bruto,gastos,ret,ahorro_bruto,ahorro_ret]})
    st.dataframe(resumen, use_container_width=True)
    st.info("Esta pestaña deja preparados los importes base para trasladarlos a tu cálculo de IRPF. La fórmula exacta puede ajustarse después replicando al 100% tu hoja IRPF actual.")


def main():
    init_app_sheets()
    st.title("App de ahorro, nóminas, intereses e IRPF")
    download_excel_button()
    tabs = st.tabs(["Ahorro", "Nóminas y vacaciones", "Intereses", "IRPF"])
    with tabs[0]: render_ahorro()
    with tabs[1]: render_nominas()
    with tabs[2]: render_intereses()
    with tabs[3]: render_irpf()

if __name__ == "__main__":
    main()
