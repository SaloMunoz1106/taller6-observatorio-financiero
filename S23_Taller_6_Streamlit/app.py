"""Observatorio financiero colombiano - Taller 6 (Streamlit).

Arquitectura cliente-servidor: el navegador (cliente) muestra los widgets y
envia cada cambio al servidor Streamlit, que vuelve a ejecutar este script de
arriba a abajo y devuelve la pagina actualizada.
"""
import zlib

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    import yfinance as yf
except ImportError:  # la app sigue funcionando con datos de demostracion
    yf = None

st.set_page_config(page_title="Observatorio financiero", page_icon="📈", layout="wide")

# ---------------------------------------------------------------- datos base
ACTIVOS = {
    "Ecopetrol": "ECOPETROL.CL",
    "Bancolombia": "BCOLOMBIA.CL",
    "Celsia": "CELSIA.CL",
    "ISA": "ISA.CL",
    "Grupo Argos": "GRUPOARGOS.CL",
    "Dólar (USD/COP)": "COP=X",
}
PERIODOS = {"3 meses": "3mo", "6 meses": "6mo", "1 año": "1y", "2 años": "2y", "5 años": "5y"}
DIAS = {"3mo": 63, "6mo": 126, "1y": 252, "2y": 504, "5y": 1260}


# ------------------------------------------------------------------ funciones
@st.cache_data(ttl=3600, show_spinner=False)
def descargar_precios(tickers: tuple, periodo: str):
    """Descarga precios de cierre. Devuelve (DataFrame, es_demo)."""
    if yf is not None:
        try:
            datos = yf.download(list(tickers), period=periodo, auto_adjust=True, progress=False)["Close"]
            if isinstance(datos, pd.Series):
                datos = datos.to_frame(tickers[0])
            datos = datos.dropna(how="all").ffill().dropna(axis=1, how="all")
            if not datos.empty:
                return datos, False
        except Exception:
            pass
    return datos_demo(tickers, periodo), True


def datos_demo(tickers, periodo):
    """Serie sintetica reproducible, solo para cuando no hay conexion a Yahoo."""
    n = DIAS[periodo]
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    out = {}
    for t in tickers:
        rng = np.random.default_rng(zlib.crc32(t.encode()))
        r = rng.normal(0.0004, 0.015, n)
        out[t] = 100 * np.exp(np.cumsum(r))
    return pd.DataFrame(out, index=idx)


def metricas(precios: pd.DataFrame, rf_anual: float) -> pd.DataFrame:
    ret = precios.pct_change().dropna()
    rend_total = precios.iloc[-1] / precios.iloc[0] - 1
    vol = ret.std() * np.sqrt(252)
    rend_anual = ret.mean() * 252
    sharpe = (rend_anual - rf_anual) / vol
    dd = (precios / precios.cummax() - 1).min()
    return pd.DataFrame({
        "Rendimiento total": rend_total,
        "Volatilidad anual": vol,
        "Sharpe": sharpe,
        "Máx. caída": dd,
    })


# -------------------------------------------------------------------- sidebar
st.sidebar.header("Parámetros")
elegidos = st.sidebar.multiselect("Activos a comparar", list(ACTIVOS), default=["Ecopetrol", "Bancolombia", "Celsia"])
periodo_txt = st.sidebar.select_slider("Período", options=list(PERIODOS), value="1 año")
rf = st.sidebar.number_input("Tasa libre de riesgo anual (%)", 0.0, 20.0, 9.0, 0.25) / 100
base100 = st.sidebar.checkbox("Normalizar a base 100", value=True)

# ----------------------------------------------------------------------- main
st.title("📈 Observatorio financiero colombiano")
st.caption("Compara acciones de la BVC y el dólar. Taller 6 · Visualización y Apps.")

if len(elegidos) < 1:
    st.info("Elige al menos un activo en la barra lateral.")
    st.stop()

periodo = PERIODOS[periodo_txt]
mapa = {ACTIVOS[n]: n for n in elegidos}
precios, demo = descargar_precios(tuple(mapa), periodo)
precios = precios.rename(columns=mapa)

if demo:
    st.warning("No se pudo conectar con Yahoo Finance: se muestran datos SIMULADOS de demostración.")

tab1, tab2, tab3 = st.tabs(["Evolución de precios", "Riesgo y retorno", "Correlaciones"])

with tab1:
    serie = precios / precios.iloc[0] * 100 if base100 else precios
    fig = px.line(serie, labels={"value": "Base 100" if base100 else "Precio", "index": "Fecha", "variable": "Activo"})
    fig.update_layout(hovermode="x unified", legend_title_text="")
    st.plotly_chart(fig, width="stretch")

    m = metricas(precios, rf)
    c = st.columns(min(len(m), 4))
    for col, (nombre, fila) in zip(c, m.iterrows()):
        col.metric(nombre, f"{fila['Rendimiento total']:+.1%}", f"Vol. {fila['Volatilidad anual']:.1%}", delta_color="off")

with tab2:
    m = metricas(precios, rf)
    st.dataframe(
        m.style.format({"Rendimiento total": "{:.1%}", "Volatilidad anual": "{:.1%}", "Sharpe": "{:.2f}", "Máx. caída": "{:.1%}"}),
        width="stretch",
    )
    d = m.reset_index().rename(columns={"index": "Activo"})
    fig2 = px.scatter(d, x="Volatilidad anual", y="Rendimiento total", text="Activo", size=[18] * len(d), color="Activo")
    fig2.update_traces(textposition="top center")
    fig2.update_layout(showlegend=False, xaxis_tickformat=".0%", yaxis_tickformat=".0%")
    st.plotly_chart(fig2, width="stretch")
    st.caption("Más a la izquierda = menos riesgo; más arriba = más rendimiento.")

with tab3:
    if precios.shape[1] < 2:
        st.info("Elige al menos dos activos para ver correlaciones.")
    else:
        corr = precios.pct_change().dropna().corr()
        fig3 = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r")
        st.plotly_chart(fig3, width="stretch")

with st.expander("Ver datos"):
    st.dataframe(precios.round(2))
    st.download_button("Descargar CSV", precios.to_csv().encode("utf-8"), "precios.csv", "text/csv")
