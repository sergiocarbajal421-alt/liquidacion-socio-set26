"""Dashboard de la liquidación del socio · Set-26.

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
COLOR_PALANCA = {"Volumen": "#1F4E78", "Cuentas": "#2E86AB"}

st.set_page_config(page_title="Liquidación de socio · Set-26", page_icon=":material/payments:",
                   layout="wide", initial_sidebar_state="expanded")


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
    st.error("No se encontraron los datos en app/data/. Ejecuta el notebook completo (incluida la fase 10).",
             icon=":material/error:")
    st.stop()

VALLA = params.get("valla", 5000)
MES = params.get("mes_liquidacion", "Set-26")
TODOS_CANALES = sorted(detalle["canal"].unique())


def miles(v):
    """Número con separador de miles; vacío si no hay valor."""
    return "" if pd.isna(v) else f"{v:,.0f}"


def grafico(fig, alto=340, leyenda_y=-0.12):
    """Formato común: leyenda horizontal arriba y márgenes compactos."""
    fig.update_layout(height=alto, margin=dict(t=50, b=10, l=10, r=10),
                      legend=dict(orientation="h", yanchor="top", y=leyenda_y, x=0, title=None))
    return fig


# ------------------------------------------------------------------ #
# Sidebar: filtros y reglas
# ------------------------------------------------------------------ #
def restablecer():
    st.session_state["f_canal"] = TODOS_CANALES
    st.session_state["f_cosecha"] = ORDEN_COSECHA


with st.sidebar:
    st.header(":material/filter_alt: Filtros")
    canales = st.pills("Canal", TODOS_CANALES, selection_mode="multi", default=TODOS_CANALES, key="f_canal")
    cosechas = st.pills("Cosecha", ORDEN_COSECHA, selection_mode="multi", default=ORDEN_COSECHA, key="f_cosecha")
    st.button("Restablecer filtros", icon=":material/restart_alt:", on_click=restablecer, width="stretch")
    st.caption("Los filtros aplican a las pestañas de análisis. La liquidación es siempre del socio completo.")

    st.divider()
    with st.expander(":material/menu_book: Reglas de pago"):
        st.markdown(
            f"""
- **Pago** = S/ {params['bolsa']:,.0f} × ({params['peso_volumen']:.0%} × cumpl. volumen
  + {params['peso_cuentas']:.0%} × cumpl. cuentas). Sin piso ni tope.
- **Cumplimiento** = real / cuota. Cuotas: volumen {params['cuota_volumen']:,.0f}, cuentas {params['cuota_cuentas']}.
- **Unidad:** el RUC (se suman sus POS).
- **Valla:** activo si su volumen mensual llega a S/ {VALLA:,.0f} en algún mes M0–M3.
- **Cuenta:** se paga en el mes en que el RUC pasa la valla por primera vez ({MES}).
- **Volumen:** incremental {MES} − mes anterior de los RUCs activos, neteado.
"""
        )

filtrado = detalle[detalle["canal"].isin(canales) & detalle["cosecha"].isin(cosechas)]

# ------------------------------------------------------------------ #
# Encabezado e indicadores (socio completo)
# ------------------------------------------------------------------ #
st.title("Liquidación de socio · Set-26")
st.caption(f"Bolsa S/ {params['bolsa']:,.0f} · sin piso ni tope · cumplimiento = real / cuota")

vol, cta, tot = resumen.iloc[0], resumen.iloc[1], resumen.iloc[2]
k = st.columns(4)
k[0].metric("Pago al socio", f"S/ {params['pago']:,.0f}", f"{params['pago'] - params['bolsa']:+,.0f}",
            delta_description="vs bolsa", border=True,
            help="Bolsa × cumplimiento ponderado. Sin piso ni tope.")
k[1].metric("Cumplimiento", f"{tot['cumplimiento']:.1%}", f"{(tot['cumplimiento'] - 1) * 100:+.1f} pp",
            delta_description="vs 100%", border=True,
            help=f"Cumplimiento ponderado: {params['peso_volumen']:.0%} × volumen + {params['peso_cuentas']:.0%} × cuentas.")
k[2].metric("Volumen incremental", f"{vol['cumplimiento']:.1%}", f"{(vol['cumplimiento'] - 1) * 100:+.1f} pp",
            delta_description="vs cuota", border=True,
            help=f"{vol['real']:,.0f} de {vol['cuota']:,.0f} · aporta S/ {vol['pago']:,.0f} al pago.")
k[3].metric("Cuentas (RUCs)", f"{cta['cumplimiento']:.1%}", f"{(cta['cumplimiento'] - 1) * 100:+.1f} pp",
            delta_description="vs cuota", border=True,
            help=f"{cta['real']:.0f} de {cta['cuota']:.0f} RUCs · aporta S/ {cta['pago']:,.0f} al pago.")

t_res, t_canal, t_inact, t_ruc, t_det = st.tabs([
    ":material/summarize: Liquidación", ":material/storefront: Por canal", ":material/hourglass_empty: RUCs inactivos",
    ":material/query_stats: RUC vs mediana", ":material/table_view: Detalle",
])


def contexto():
    """Línea que recuerda qué filtros están aplicados."""
    n_canal = "todos los canales" if len(canales) == len(TODOS_CANALES) else ", ".join(canales) or "ningún canal"
    n_cos = "todas las cosechas" if len(cosechas) == len(ORDEN_COSECHA) else ", ".join(cosechas) or "ninguna cosecha"
    st.caption(f":material/filter_alt: {n_canal} · {n_cos} · {len(filtrado)} de {len(detalle)} RUCs")


def sin_datos():
    if filtrado.empty:
        st.warning("Selecciona al menos un canal y una cosecha en el sidebar.", icon=":material/warning:")
        return True
    return False


# ------------------------------------------------------------------ #
# Pestaña 1 · Liquidación
# ------------------------------------------------------------------ #
with t_res:
    with st.container(border=True):
        st.markdown("**Cálculo por palanca**")
        tabla = resumen.rename(columns={"palanca": "Palanca", "cuota": "Cuota", "real": "Real",
                                        "cumplimiento": "Cumplimiento", "peso": "Peso", "pago": "Pago (S/)"})
        tabla["Cuota"] = tabla["Cuota"].map(miles)
        tabla["Real"] = tabla["Real"].map(miles)
        derecha = st.column_config.TextColumn(alignment="right")
        st.dataframe(tabla.style.format({"Cumplimiento": "{:.1%}", "Peso": "{:.0%}", "Pago (S/)": "{:,.0f}"}),
                     hide_index=True, width="stretch", column_config={"Cuota": derecha, "Real": derecha})
        st.caption(f"Pago = {params['bolsa']:,.0f} × ({params['peso_volumen']} × {vol['cumplimiento']:.3f}"
                   f" + {params['peso_cuentas']} × {cta['cumplimiento']:.3f}) = S/ {params['pago']:,.2f}")

    c1, c2 = st.columns([1.6, 1])
    with c1.container(border=True):
        cump = pd.DataFrame({"Palanca": ["Volumen", "Cuentas"], "Cumplimiento": [vol["cumplimiento"], cta["cumplimiento"]]})
        fig = px.bar(cump, x="Palanca", y="Cumplimiento", color="Palanca", text_auto=".1%",
                     color_discrete_map=COLOR_PALANCA, title="Cumplimiento por palanca", labels={"Palanca": ""})
        fig.update_traces(textposition="outside")
        fig.add_hline(y=1, line_dash="dash", annotation_text="Cuota (100%)", annotation_position="bottom right")
        fig.update_yaxes(tickformat=".0%", range=[0, max(1.4, cump["Cumplimiento"].max() * 1.2)])
        fig.update_layout(showlegend=False)
        st.plotly_chart(grafico(fig, 300), width="stretch")
    with c2:
        activos = int(detalle["activo"].sum())
        st.metric("RUCs activos", f"{activos} de {len(detalle)}", border=True,
                  help=f"RUCs que pasaron la valla de S/ {VALLA:,.0f} en algún mes.")
        st.metric(f"Cuentas nuevas en {MES}", f"{cta['real']:.0f}", f"{cta['real'] - cta['cuota']:+.0f}",
                  delta_description="vs cuota", border=True,
                  help=f"RUCs que pasaron la valla por primera vez en {MES}.")
        st.metric("Volumen incremental neto", f"{vol['real']:,.0f}", f"{vol['real'] - vol['cuota']:+,.0f}",
                  delta_description="vs cuota", border=True)

# ------------------------------------------------------------------ #
# Pestaña 2 · Por canal
# ------------------------------------------------------------------ #
with t_canal:
    contexto()
    if not sin_datos():
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
            rucs=("ruc", "count"), activos=("activo", "sum"), incremental=("incremental_pagable", "sum"),
        ).reset_index()
        por_cc["pct_activos"] = por_cc["activos"] / por_cc["rucs"]

        g1, g2 = st.columns(2)
        with g1.container(border=True):
            largo = por_canal.melt(id_vars="canal", value_vars=["pago_volumen", "pago_cuentas"],
                                   var_name="palanca", value_name="pago")
            largo["palanca"] = largo["palanca"].map({"pago_volumen": "Volumen", "pago_cuentas": "Cuentas"})
            fig = px.bar(largo, x="canal", y="pago", color="palanca", text_auto=",.0f",
                         color_discrete_map=COLOR_PALANCA, title="Pago atribuido por canal (S/)",
                         labels={"pago": "S/", "canal": ""})
            st.plotly_chart(grafico(fig), width="stretch")
        with g2.container(border=True):
            fig = px.bar(por_cc, x="cosecha", y="incremental", color="canal", barmode="group",
                         category_orders={"cosecha": ORDEN_COSECHA}, color_discrete_map=COLOR_CANAL,
                         title="Incremental neto por cosecha y canal (S/)", labels={"incremental": "S/", "cosecha": ""})
            st.plotly_chart(grafico(fig), width="stretch")

        g3, g4 = st.columns(2)
        with g3.container(border=True):
            fig = px.bar(por_cc, x="cosecha", y="pct_activos", color="canal", barmode="group",
                         category_orders={"cosecha": ORDEN_COSECHA}, color_discrete_map=COLOR_CANAL,
                         title="% de RUCs activos por cosecha y canal", labels={"pct_activos": "% activos", "cosecha": ""})
            fig.update_yaxes(tickformat=".0%", range=[0, 1.05])
            st.plotly_chart(grafico(fig), width="stretch")
        with g4.container(border=True):
            st.markdown("**Resumen por canal**")
            vista = por_canal[["canal", "rucs", "pct_activos", "cuentas", "incremental", "pago_total"]].rename(columns={
                "canal": "Canal", "rucs": "RUCs", "pct_activos": "% activos", "cuentas": "Cuentas",
                "incremental": "Incremental", "pago_total": "Pago (S/)"})
            st.dataframe(
                vista.style.format({"Incremental": "{:,.0f}", "Pago (S/)": "{:,.0f}"}),
                hide_index=True, width="stretch",
                column_config={"% activos": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1, width="small")},
            )
            st.info("El pago por canal es atribuido: el socio se liquida como un solo bloque.", icon=":material/info:")

# ------------------------------------------------------------------ #
# Pestaña 3 · RUCs inactivos
# ------------------------------------------------------------------ #
with t_inact:
    contexto()
    if not sin_datos():
        max_vol = volumen.groupby("ruc")["volumen"].max()
        inactivos = filtrado[~filtrado["activo"]].copy()
        inactivos["max_vol"] = inactivos["ruc"].map(max_vol)
        inactivos["avance"] = inactivos["max_vol"] / VALLA

        i1, i2, i3 = st.columns(3)
        i1.metric("RUCs inactivos", f"{len(inactivos)}", border=True,
                  help=f"Nunca pasaron la valla de S/ {VALLA:,.0f}: no suman volumen ni cuenta.")
        i2.metric(f"Volumen de {MES} sin pagar", f"S/ {inactivos['vol_set'].sum():,.0f}", border=True,
                  help=f"Volumen de {MES} de los RUCs inactivos, que no entra en la liquidación.")
        i3.metric("Cercanos a la valla", f"{(inactivos['avance'] >= 0.8).sum()}", border=True,
                  help=f"Volumen máximo de al menos S/ {0.8 * VALLA:,.0f} (80% de la valla).")

        lista = (inactivos.sort_values("max_vol", ascending=False)[["ruc", "canal", "cosecha", "vol_set", "max_vol", "avance"]]
                 .rename(columns={"ruc": "RUC", "canal": "Canal", "cosecha": "Cosecha", "vol_set": f"Volumen {MES}",
                                  "max_vol": "Volumen máximo mensual", "avance": "Avance a la valla"}))
        lista["RUC"] = lista["RUC"].astype(str)
        st.dataframe(
            lista.style.format({f"Volumen {MES}": "{:,.0f}", "Volumen máximo mensual": "{:,.0f}"}),
            hide_index=True, width="stretch",
            column_config={"Avance a la valla": st.column_config.ProgressColumn(
                format="percent", min_value=0, max_value=1, help=f"Volumen máximo mensual / S/ {VALLA:,.0f}")},
        )
        st.caption(f"Los inactivos de la cosecha {MES} están en su M0 y aún tienen 3 meses para activarse.")

# ------------------------------------------------------------------ #
# Pestaña 4 · RUC vs mediana de su cosecha
# ------------------------------------------------------------------ #
with t_ruc:
    mayores = volumen.groupby("ruc")["volumen"].max().sort_values(ascending=False)
    ruc_sel = st.selectbox(
        "RUC", list(mayores.index), index=0,
        format_func=lambda r: f"{r} · máx. mensual S/ {mayores[r]:,.0f}",
        help="Ordenados por volumen mensual máximo. El primero es el RUC atípico.",
    )
    serie = volumen[volumen["ruc"] == ruc_sel].sort_values("mes")
    cosecha_ruc = serie["cosecha"].iloc[0]
    mediana = (volumen[volumen["cosecha"] == cosecha_ruc].groupby("mes")["volumen"].median()
               .reindex(serie["mes"]).reset_index())
    datos = pd.concat([serie[["mes", "volumen"]].assign(serie=f"RUC {ruc_sel}"),
                       mediana.assign(serie=f"Mediana de la cosecha {cosecha_ruc}")])

    fila = detalle[detalle["ruc"] == ruc_sel].iloc[0]
    sin_ruc = detalle.loc[detalle["ruc"] != ruc_sel, "incremental_pagable"].sum()
    pago_sin = params["bolsa"] * (
        params["peso_volumen"] * sin_ruc / params["cuota_volumen"]
        + params["peso_cuentas"] * (detalle["cuenta"].sum() - int(fila["cuenta"])) / params["cuota_cuentas"])

    c1, c2 = st.columns([2.6, 1])
    with c1.container(border=True):
        fig = px.line(datos, x="mes", y="volumen", color="serie", markers=True,
                      color_discrete_sequence=["#E07A1F", "#7F8C9A"],
                      title=f"Volumen mensual del RUC {ruc_sel} (S/)", labels={"volumen": "S/", "mes": "Mes de vida"})
        fig.add_hline(y=VALLA, line_dash="dot", annotation_text=f"Valla S/ {VALLA:,.0f}", annotation_position="top left")
        st.plotly_chart(grafico(fig, 380, leyenda_y=-0.22), width="stretch")
    with c2:
        st.metric("Canal", fila["canal"], f"cosecha {cosecha_ruc}", delta_color="off", delta_arrow="off", border=True)
        estado = "Activo" if fila["activo"] else "Inactivo"
        st.metric("Estado", estado, f"cuenta en {MES}" if fila["cuenta"] else None,
                  delta_color="off", delta_arrow="off", border=True)
        st.metric(f"Incremental en {MES}", f"{fila['incremental']:,.0f}", border=True)
        st.metric("Pago sin este RUC", f"S/ {pago_sin:,.0f}", f"{pago_sin - params['pago']:+,.0f}",
                  delta_description="vs pago actual", border=True)

# ------------------------------------------------------------------ #
# Pestaña 5 · Detalle por RUC
# ------------------------------------------------------------------ #
with t_det:
    contexto()
    if not sin_datos():
        buscar = st.text_input("Buscar RUC", placeholder="Escribe parte del número", icon=":material/search:")
        vista = filtrado.rename(columns={
            "ruc": "RUC", "canal": "Canal", "cosecha": "Cosecha", "primer_mes": "Mes de activación",
            "activo": "Activo", "cuenta": "Cuenta pagable", "vol_set": f"Volumen {MES}",
            "vol_ago": "Volumen mes anterior", "incremental": "Incremental", "incremental_pagable": "Incremental pagable"})
        vista["RUC"] = vista["RUC"].astype(str)
        vista["Mes de activación"] = vista["Mes de activación"].fillna("—")
        if buscar:
            vista = vista[vista["RUC"].str.contains(buscar.strip(), regex=False)]
        cols = [f"Volumen {MES}", "Volumen mes anterior", "Incremental", "Incremental pagable"]
        st.dataframe(vista.style.format({c: "{:,.0f}" for c in cols}), hide_index=True, width="stretch", height=420)
        st.download_button("Descargar CSV", vista.to_csv(index=False).encode("utf-8"),
                           file_name="detalle_ruc_filtrado.csv", mime="text/csv", icon=":material/download:")
