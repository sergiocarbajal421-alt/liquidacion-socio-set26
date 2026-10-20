"""Dashboard de la liquidación del socio · Set-26 (una sola pantalla).

Lee las tablas que exporta el notebook (fase 10) desde app/data/.
Ejecutar (desde la raíz del proyecto):  streamlit run app/app_streamlit.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parent / "data"
ORDEN_COSECHA = ["Jun-26", "Jul-26", "Ago-26", "Set-26"]
COLOR_CANAL = {"Canal 1": "#2E9E6B", "Canal 2": "#E07A1F", "Canal 3": "#2E86AB"}
AZUL, TEAL, NARANJA, VERDE, GRIS = "#1F4E78", "#2E86AB", "#E07A1F", "#2E9E6B", "#7F8C9A"

st.set_page_config(page_title="Liquidación de socio · Set-26", layout="wide", initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ #
# Estilo: compacto para que todo quepa en una pantalla
# ------------------------------------------------------------------ #
st.markdown(
    """
    <style>
    header[data-testid="stHeader"], footer {display: none;}
    .block-container {padding: 0.9rem 1.6rem 0.4rem 1.6rem; max-width: 100%;}
    div[data-testid="stVerticalBlock"] {gap: 0.55rem;}
    h1 {font-size: 1.55rem !important; padding: 0 !important; margin: 0 !important; line-height: 1.2;}
    .sub {font-size: 0.82rem; opacity: 0.65; margin-top: 0.1rem;}
    .kpi {background: var(--secondary-background-color); border-radius: 10px; padding: 0.55rem 0.9rem; height: 100%; margin-bottom: 0.8rem;}
    .kpi .lbl {font-size: 0.74rem; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.03em;}
    .kpi .val {font-size: 1.75rem; font-weight: 700; line-height: 1.15;}
    .kpi .det {font-size: 0.76rem; opacity: 0.65;}
    .kpi.main {background: #1F4E78; color: #fff;}
    .kpi.main .lbl, .kpi.main .det {opacity: 0.85;}
    .mini {background: var(--secondary-background-color); border-radius: 8px; padding: 0.35rem 0.7rem;}
    .mini .lbl {font-size: 0.7rem; opacity: 0.65;}
    .mini .val {font-size: 1.15rem; font-weight: 700;}
    button[data-variant="pills"] {border-color: #1F4E78 !important;}
    button[data-variant="pills"][data-selected="true"] {background: #1F4E78 !important; color: #fff !important;}
    button[data-variant="pills"][data-selected="true"] p {color: #fff !important;}
    button[data-baseweb="tab"][aria-selected="true"] {color: #1F4E78;}
    div[data-baseweb="tab-highlight"] {background-color: #1F4E78 !important;}
    .ttl {font-size: 0.86rem; font-weight: 600; padding-bottom: 0.45rem; line-height: 1.3;}
    div[data-testid="stVerticalBlockBorderWrapper"] {padding: 0.5rem 0.7rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def cargar():
    """Tablas finales del notebook."""
    params = json.loads((DATA / "parametros.json").read_text())
    resumen = pd.read_csv(DATA / "resumen.csv")
    detalle = pd.read_csv(DATA / "detalle_ruc.csv")
    volumen = pd.read_csv(DATA / "volumen_ruc_mes.csv")
    return params, resumen, detalle, volumen


try:
    params, resumen, detalle, volumen = cargar()
except FileNotFoundError:
    st.error("No se encontró la carpeta app/data/. Ejecuta primero el notebook (fases 1 a 10).")
    st.stop()


def kpi(col, etiqueta, valor, detalle_txt="", principal=False):
    """Tarjeta de indicador."""
    clase = "kpi main" if principal else "kpi"
    col.markdown(
        f'<div class="{clase}"><div class="lbl">{etiqueta}</div><div class="val">{valor}</div>'
        f'<div class="det">{detalle_txt}&nbsp;</div></div>',
        unsafe_allow_html=True,
    )


def mini(col, etiqueta, valor):
    col.markdown(f'<div class="mini"><div class="lbl">{etiqueta}</div><div class="val">{valor}</div></div>',
                 unsafe_allow_html=True)


def ajustar(fig, alto):
    """Formato común de los gráficos."""
    fig.update_layout(
        height=alto, margin=dict(l=4, r=4, t=26, b=4), font_size=11,
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title=None, font_size=11),
        xaxis_title=None,
    )
    return fig


# ------------------------------------------------------------------ #
# Encabezado: título, filtros y detalle
# ------------------------------------------------------------------ #
todos_canales = sorted(detalle["canal"].unique())
h1, h2, h3, h4 = st.columns([4, 2.6, 3.2, 1.3], vertical_alignment="center")
h1.markdown(
    f"<h1>Liquidación de socio · Set-26</h1>"
    f"<div class='sub'>Bolsa S/ {params['bolsa']:,.0f} · sin piso ni tope · cumplimiento = real / cuota</div>",
    unsafe_allow_html=True,
)
sel_canales = h2.pills("Canal", todos_canales, selection_mode="multi", default=todos_canales)
sel_cosechas = h3.pills("Cosecha", ORDEN_COSECHA, selection_mode="multi", default=ORDEN_COSECHA)

canales = sel_canales or todos_canales          # sin selección = todos
cosechas = sel_cosechas or ORDEN_COSECHA
filtrado = detalle[detalle["canal"].isin(canales) & detalle["cosecha"].isin(cosechas)]

max_vol = volumen.groupby("ruc")["volumen"].max()
inactivos = filtrado[~filtrado["activo"]].copy()
inactivos["max_vol"] = inactivos["ruc"].map(max_vol)


@st.dialog("Detalle", width="large")
def ver_detalle():
    t1, t2 = st.tabs(["Detalle por RUC", "RUCs inactivos"])
    vista = filtrado.rename(columns={
        "ruc": "RUC", "canal": "Canal", "cosecha": "Cosecha", "primer_mes": "Mes de activación",
        "activo": "Activo", "cuenta": "Cuenta pagable", "vol_set": "Volumen Set-26",
        "vol_ago": "Volumen Ago-26", "incremental": "Incremental", "incremental_pagable": "Incremental pagable"})
    vista["RUC"] = vista["RUC"].astype(str)
    vista["Mes de activación"] = vista["Mes de activación"].fillna("—")
    miles = {c: "{:,.0f}" for c in ["Volumen Set-26", "Volumen Ago-26", "Incremental", "Incremental pagable"]}
    t1.dataframe(vista.style.format(miles), hide_index=True, width="stretch", height=380)
    t1.download_button("Descargar CSV", vista.to_csv(index=False).encode("utf-8"),
                       file_name="detalle_ruc_filtrado.csv", mime="text/csv")

    lista = (inactivos[["ruc", "canal", "cosecha", "vol_set", "max_vol"]].sort_values("max_vol", ascending=False)
             .rename(columns={"ruc": "RUC", "canal": "Canal", "cosecha": "Cosecha",
                              "vol_set": "Volumen Set-26", "max_vol": "Volumen máximo mensual"}))
    lista["RUC"] = lista["RUC"].astype(str)
    t2.dataframe(lista.style.format({"Volumen Set-26": "{:,.0f}", "Volumen máximo mensual": "{:,.0f}"}),
                 hide_index=True, width="stretch", height=380)
    t2.caption("Los inactivos de la cosecha Set-26 están en su M0 y aún tienen 3 meses para activarse.")


if h4.button("Ver detalle", width="stretch"):
    ver_detalle()

# ------------------------------------------------------------------ #
# KPIs de la liquidación (siempre el socio completo)
# ------------------------------------------------------------------ #
vol, cta, tot = resumen.iloc[0], resumen.iloc[1], resumen.iloc[2]
k = st.columns([1.25, 1, 1, 1, 1])
kpi(k[0], "Pago al socio", f"S/ {params['pago']:,.0f}", "liquidación total", principal=True)
kpi(k[1], "Cumplimiento ponderado", f"{tot['cumplimiento']:.1%}", "70% volumen + 30% cuentas")
kpi(k[2], "Volumen incremental", f"{vol['cumplimiento']:.1%}", f"{vol['real']:,.0f} de {vol['cuota']:,.0f} · S/ {vol['pago']:,.0f}")
kpi(k[3], "Cuentas (RUCs)", f"{cta['cumplimiento']:.1%}", f"{cta['real']:.0f} de {cta['cuota']:.0f} · S/ {cta['pago']:,.0f}")
kpi(k[4], "RUCs activos", f"{int(detalle['activo'].sum())} de {len(detalle)}", "pasaron la valla de S/ 5,000")

# ------------------------------------------------------------------ #
# Cálculos por canal (aplican los filtros)
# ------------------------------------------------------------------ #
por_canal = filtrado.groupby("canal").agg(
    rucs=("ruc", "count"), activos=("activo", "sum"),
    cuentas=("cuenta", "sum"), incremental=("incremental_pagable", "sum"),
).reset_index()
por_canal["pct_activos"] = por_canal["activos"] / por_canal["rucs"]
# Pago atribuido: cada canal aporta a cada palanca en proporción a su resultado
por_canal["pago_volumen"] = params["bolsa"] * params["peso_volumen"] * por_canal["incremental"] / params["cuota_volumen"]
por_canal["pago_cuentas"] = params["bolsa"] * params["peso_cuentas"] * por_canal["cuentas"] / params["cuota_cuentas"]
por_canal["pago_total"] = por_canal["pago_volumen"] + por_canal["pago_cuentas"]

por_cc = filtrado.groupby(["canal", "cosecha"]).agg(
    rucs=("ruc", "count"), activos=("activo", "sum"), incremental=("incremental_pagable", "sum")).reset_index()
por_cc["pct_activos"] = por_cc["activos"] / por_cc["rucs"]

# ------------------------------------------------------------------ #
# Fila de gráficos
# ------------------------------------------------------------------ #
ALTO = 225
g1, g2, g3 = st.columns(3)

with g1.container(border=True):
    st.markdown('<div class="ttl">Pago atribuido por canal (S/)</div>', unsafe_allow_html=True)
    largo = por_canal.melt(id_vars="canal", value_vars=["pago_volumen", "pago_cuentas"], var_name="palanca", value_name="pago")
    largo["palanca"] = largo["palanca"].map({"pago_volumen": "Volumen", "pago_cuentas": "Cuentas"})
    fig = px.bar(largo, x="canal", y="pago", color="palanca", text_auto=",.0f",
                 color_discrete_map={"Volumen": AZUL, "Cuentas": TEAL}, labels={"pago": "S/", "canal": ""})
    st.plotly_chart(ajustar(fig, ALTO), width="stretch", key="g_pago")

with g2.container(border=True):
    st.markdown('<div class="ttl">Incremental neto por cosecha y canal (S/)</div>', unsafe_allow_html=True)
    fig = px.bar(por_cc, x="cosecha", y="incremental", color="canal", barmode="group",
                 category_orders={"cosecha": ORDEN_COSECHA}, color_discrete_map=COLOR_CANAL,
                 labels={"incremental": "S/", "cosecha": ""})
    st.plotly_chart(ajustar(fig, ALTO), width="stretch", key="g_inc")

with g3.container(border=True):
    st.markdown('<div class="ttl">% de RUCs activos por cosecha y canal</div>', unsafe_allow_html=True)
    fig = px.bar(por_cc, x="cosecha", y="pct_activos", color="canal", barmode="group",
                 category_orders={"cosecha": ORDEN_COSECHA}, color_discrete_map=COLOR_CANAL,
                 labels={"pct_activos": "% activos", "cosecha": ""})
    fig.update_yaxes(tickformat=".0%", range=[0, 1.05])
    st.plotly_chart(ajustar(fig, ALTO), width="stretch", key="g_act")

# ------------------------------------------------------------------ #
# Fila inferior: resumen por canal + inactivos | RUC atípico
# ------------------------------------------------------------------ #
b1, b2 = st.columns([5, 6.5])

with b1.container(border=True):
    st.markdown('<div class="ttl">Resumen por canal</div>', unsafe_allow_html=True)
    tabla = por_canal[["canal", "rucs", "pct_activos", "cuentas", "incremental", "pago_total"]].rename(columns={
        "canal": "Canal", "rucs": "RUCs", "pct_activos": "% Activos", "cuentas": "Cuentas",
        "incremental": "Incremental", "pago_total": "Pago (S/)"})
    st.dataframe(
        tabla.style.format({"% Activos": "{:.1%}", "Incremental": "{:,.0f}", "Pago (S/)": "{:,.0f}"}),
        hide_index=True, width="stretch", height=35 * (len(por_canal) + 1) + 3)
    m = st.columns(3)
    mini(m[0], "RUCs inactivos", f"{len(inactivos)}")
    mini(m[1], "Volumen Set-26 sin pagar", f"S/ {inactivos['vol_set'].sum():,.0f}")
    mini(m[2], "Cercanos a la valla (≥ 4,000)", f"{(inactivos['max_vol'] >= 4000).sum()}")
    st.caption("Pago por canal atribuido: el socio se liquida como un solo bloque.")

with b2.container(border=True):
    top = st.columns([3.2, 1.2])
    top[0].markdown('<div class="ttl">RUC atípico vs mediana de su cosecha (S/)</div>', unsafe_allow_html=True)
    mayores = max_vol.sort_values(ascending=False)
    ruc_sel = top[1].selectbox("RUC", list(mayores.index), index=0, label_visibility="collapsed")

    serie = volumen[volumen["ruc"] == ruc_sel].sort_values("mes")
    cosecha_ruc = serie["cosecha"].iloc[0]
    mediana = (volumen[volumen["cosecha"] == cosecha_ruc].groupby("mes")["volumen"].median()
               .reindex(serie["mes"]).reset_index())
    grafico = pd.concat([serie[["mes", "volumen"]].assign(serie=f"RUC {ruc_sel}"),
                         mediana.assign(serie=f"Mediana {cosecha_ruc}")])
    fila = detalle[detalle["ruc"] == ruc_sel].iloc[0]
    sin_ruc = detalle.loc[detalle["ruc"] != ruc_sel, "incremental_pagable"].sum()
    pago_sin = params["bolsa"] * (
        params["peso_volumen"] * sin_ruc / params["cuota_volumen"]
        + params["peso_cuentas"] * (detalle["cuenta"].sum() - int(fila["cuenta"])) / params["cuota_cuentas"])

    c1, c2 = st.columns([3, 1.4])
    fig = px.line(grafico, x="mes", y="volumen", color="serie", markers=True,
                  color_discrete_sequence=[NARANJA, GRIS], labels={"volumen": "S/", "mes": ""})
    c1.plotly_chart(ajustar(fig, 200), width="stretch", key="g_ruc")
    with c2:
        mini(st, "Canal · cosecha", f"{fila['canal']} · {cosecha_ruc}")
        mini(st, "Incremental en Set-26", f"{fila['incremental']:,.0f}")
        mini(st, "Pago sin este RUC", f"S/ {pago_sin:,.0f} ({pago_sin - params['pago']:+,.0f})")
