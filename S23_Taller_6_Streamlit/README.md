# Observatorio financiero colombiano · Taller 6

Aplicación interactiva en **Streamlit** que compara acciones de la BVC (Ecopetrol, Bancolombia, Celsia, ISA, Grupo Argos) y el dólar (USD/COP).

## Qué hace
- Widgets para elegir activos, período, tasa libre de riesgo y normalización a base 100.
- Tres gráficos: evolución de precios, riesgo vs. retorno y matriz de correlaciones.
- Métricas: rendimiento total, volatilidad anual, Sharpe y máxima caída.
- Datos de Yahoo Finance (`yfinance`); si no hay conexión muestra datos simulados con una advertencia.

## Ejecutar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Arquitectura
El navegador (cliente) envía cada cambio de widget al servidor Streamlit, que re-ejecuta `app.py` y devuelve la página actualizada. `st.cache_data` evita volver a descargar los precios en cada interacción.

## Archivos
`app.py` · `requirements.txt` · `README.md` · `informe_taller6.pdf`
